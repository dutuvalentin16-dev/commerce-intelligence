from commerce_pipeline.generate_sample_data import generate, TABLE_FIELDS, write_csv


def test_deterministic():
    assert generate(seed=42) == generate(seed=42)
    assert generate(seed=42) != generate(seed=43)


def test_referential_integrity_and_session_grain():
    rows = generate(seed=42)
    users = {r["customer_id"] for r in rows["customers"]}
    sessions = {r["session_id"]: r for r in rows["sessions"]}
    orders = {r["order_id"]: r for r in rows["orders"]}
    products = {r["product_id"] for r in rows["products"]}
    assert len({r["session_id"] for r in rows["orders"]}) == len(rows["orders"])
    for row in rows["sessions"]:
        assert row["customer_id"] in users
    for row in rows["orders"]:
        assert row["session_id"] in sessions
        assert row["customer_id"] == sessions[row["session_id"]]["customer_id"]
        assert row["order_ts"] > sessions[row["session_id"]]["session_ts"]
    for row in rows["order_items"]:
        assert row["order_id"] in orders
        assert row["product_id"] in products
        assert row["quantity"] > 0


def test_csv_headers_and_rows(tmp_path):
    rows = generate(seed=42, n_sessions=50)
    write_csv(rows, tmp_path)
    for table, fields in TABLE_FIELDS.items():
        import csv
        with (tmp_path / f"{table}.csv").open(newline="") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == fields
            assert len(list(reader)) == len(rows[table])


def test_invalid_session_count_rejected():
    import pytest
    with pytest.raises(ValueError):
        generate(n_sessions=0)
