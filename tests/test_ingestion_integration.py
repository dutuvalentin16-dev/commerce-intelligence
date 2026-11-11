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
