"""Opt-in PostgreSQL tests; each test uses a separate disposable database."""
import os
from uuid import uuid4

import pytest

from commerce_pipeline.generate_sample_data import TABLE_FIELDS, generate, write_csv
from commerce_pipeline.ingest import run

pytestmark = pytest.mark.skipif(
    os.getenv("COMMERCE_INTEGRATION_TESTS") != "1",
    reason="Set COMMERCE_INTEGRATION_TESTS=1 with local PostgreSQL running",
)


@pytest.fixture
def isolated_database(monkeypatch):
    import psycopg
    from psycopg import sql

    name = "commerce_test_" + uuid4().hex
    config = {
        "host": os.getenv("PGHOST", "localhost"),
        "port": int(os.getenv("PGPORT", "5434")),
        "dbname": os.getenv("PGDATABASE", "commerce"),
        "user": os.getenv("PGUSER", "commerce"),
        "password": os.getenv("PGPASSWORD", "commerce"),
        "connect_timeout": 5,
    }
    with psycopg.connect(**config, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
        try:
            monkeypatch.setenv("PGDATABASE", name)
            yield {**config, "dbname": name}
        finally:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


def snapshot(config):
    import psycopg
    from psycopg import sql

    with psycopg.connect(**config) as conn:
        return {
            table: conn.execute(
                sql.SQL("SELECT * FROM raw.{} ORDER BY 1").format(sql.Identifier(table))
            ).fetchall()
            for table in TABLE_FIELDS
        }


def test_reingestion_is_idempotent(isolated_database, tmp_path):
    rows = generate()
    write_csv(rows, tmp_path)
    expected = {table: len(values) for table, values in rows.items()}
    assert run(tmp_path) == expected
    before = snapshot(isolated_database)
    assert run(tmp_path) == expected
    assert snapshot(isolated_database) == before


def test_invalid_final_table_rolls_back_entire_load(isolated_database, tmp_path):
    import psycopg

    write_csv(generate(), tmp_path)
    run(tmp_path)
    before = snapshot(isolated_database)
    replacement = generate(seed=43)
    # Fail in the final table after earlier COPY operations have succeeded.
    replacement["order_items"][0]["quantity"] = 0
    write_csv(replacement, tmp_path)
    with pytest.raises(psycopg.errors.CheckViolation):
        run(tmp_path)
    assert snapshot(isolated_database) == before


def incremental_batch(rows):
    """Synthetic change set: status update, changed/removed/new items and a new order."""
    from copy import deepcopy

    order = deepcopy(rows['orders'][0])
    order['status'] = 'refunded'
    items = [deepcopy(i) for i in rows['order_items'] if i['order_id'] == order['order_id']]
    items = items[:1]  # Complete replacement also removes any remaining old lines.
    items[0]['quantity'] = 7
    added = {**items[0], 'order_item_id': 90001, 'quantity': 2}
    session = {**rows['sessions'][0], 'session_id': 90001}
    new_order = {**order, 'order_id': 90001, 'session_id': 90001,
                 'customer_id': session['customer_id'], 'order_ts': session['session_ts'], 'status': 'paid'}
    new_item = {**added, 'order_item_id': 90002, 'order_id': 90001}
    return {'customers': [], 'products': [], 'sessions': [session],
            'orders': [order, new_order], 'order_items': items + [added, new_item]}


def test_incremental_updates_new_orders_items_and_reruns(isolated_database, tmp_path):
    rows = generate()
    write_csv(rows, tmp_path)
    run(tmp_path)
    before = snapshot(isolated_database)
    batch = incremental_batch(rows)
    write_csv(batch, tmp_path)
    counts = run(tmp_path, mode='incremental')
    after = snapshot(isolated_database)
    assert counts['orders'] == len(rows['orders']) + 1
    assert counts['sessions'] == len(rows['sessions']) + 1
    assert after['customers'] == before['customers']
    assert after['products'] == before['products']
    assert next(o for o in after['orders'] if o[0] == batch['orders'][0]['order_id'])[-1] == 'refunded'
    actual_items = [i for i in after['order_items'] if i[1] == batch['orders'][0]['order_id']]
    assert {i[0] for i in actual_items} == {i['order_item_id'] for i in batch['order_items'][:2]}
    assert actual_items[0][3] == 7
    assert run(tmp_path, mode='incremental') == counts
    assert snapshot(isolated_database) == after
    # Full ingestion still replaces the changed dataset exactly.
    write_csv(rows, tmp_path)
    run(tmp_path)
    assert snapshot(isolated_database) == before


@pytest.mark.parametrize('failure', ['duplicate', 'invalid_quantity', 'foreign_key',
                                     'missing_items', 'orphan_batch_item', 'customer_mismatch',
                                     'item_reassignment', 'invalid_time'])
def test_invalid_incremental_batch_is_atomic(isolated_database, tmp_path, failure):
    import psycopg

    rows = generate()
    write_csv(rows, tmp_path)
    run(tmp_path)
    before = snapshot(isolated_database)
    batch = incremental_batch(rows)
    if failure == 'duplicate':
        batch['orders'].append(dict(batch['orders'][0]))
    elif failure == 'invalid_quantity':
        batch['order_items'][-1]['quantity'] = 0
    elif failure == 'foreign_key':
        batch['order_items'][-1]['product_id'] = 999999
    elif failure == 'missing_items':
        batch['order_items'] = batch['order_items'][:2]
    elif failure == 'orphan_batch_item':
        batch['order_items'][-1]['order_id'] = 999999
    elif failure == 'customer_mismatch':
        batch['orders'][-1]['customer_id'] = (batch['orders'][-1]['customer_id'] % 250) + 1
    elif failure == 'item_reassignment':
        batch['order_items'][-1]['order_item_id'] = rows['order_items'][-1]['order_item_id']
    elif failure == 'invalid_time':
        batch['orders'][-1]['order_ts'] = '1900-01-01T00:00:00+00:00'
    write_csv(batch, tmp_path)
    with pytest.raises((ValueError, psycopg.IntegrityError)):
        run(tmp_path, mode='incremental')
    assert snapshot(isolated_database) == before
