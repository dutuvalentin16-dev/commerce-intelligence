"""Atomic, rerunnable CSV -> PostgreSQL ingestion using COPY."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from commerce_pipeline.generate_sample_data import TABLE_FIELDS

ROOT = Path(__file__).resolve().parents[1]


def run(directory: Path, mode: str = "full") -> dict[str, int]:
    import psycopg

    if mode not in ("full", "incremental"):
        raise ValueError("mode must be full or incremental")
    directory = directory.resolve()
    for table in TABLE_FIELDS:
        if not (directory / f"{table}.csv").is_file():
            raise FileNotFoundError(f"Missing {table}.csv in {directory}")
    cfg = {"host": os.getenv("PGHOST", "localhost"),
           "port": int(os.getenv("PGPORT", "5434")),
           "dbname": os.getenv("PGDATABASE", "commerce"),
           "user": os.getenv("PGUSER", "commerce"),
           "password": os.getenv("PGPASSWORD", "commerce")}
    counts = {}
    with psycopg.connect(**cfg) as conn:
        with conn.cursor() as cur:
            cur.execute((ROOT / "sql/create_raw_tables.sql").read_text(encoding="utf-8"))
            # Serialize writers, including full reloads, to avoid mixed batches.
            cur.execute("LOCK TABLE raw.customers, raw.products, raw.sessions, raw.orders, raw.order_items IN EXCLUSIVE MODE")
            if mode == "full":
                cur.execute("TRUNCATE raw.order_items, raw.orders, raw.sessions, raw.products, raw.customers")
            for table in TABLE_FIELDS:
                target = f"raw.{table}"
                if mode == "incremental":
                    target = f"batch_{table}"
                    cur.execute(f"CREATE TEMP TABLE {target} (LIKE raw.{table} INCLUDING ALL) ON COMMIT DROP")
                fields = ", ".join(TABLE_FIELDS[table])
                with cur.copy(f"COPY {target} ({fields}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)") as copy:
                    with (directory / f"{table}.csv").open("rb") as f:
                        while block := f.read(1024 * 1024):
                            copy.write(block)
            if mode == "incremental":
                # Each included order carries its complete current item snapshot.
                cur.execute("SELECT 1 FROM batch_order_items i LEFT JOIN batch_orders o USING (order_id) WHERE o.order_id IS NULL LIMIT 1")
                if cur.fetchone():
                    raise ValueError("Every batch item must belong to a batch order")
                cur.execute("SELECT 1 FROM batch_orders o LEFT JOIN batch_order_items i USING (order_id) WHERE i.order_id IS NULL LIMIT 1")
                if cur.fetchone():
                    raise ValueError("Every batch order must include at least one item")
                cur.execute("SELECT 1 FROM batch_order_items b JOIN raw.order_items r USING (order_item_id) WHERE b.order_id <> r.order_id LIMIT 1")
                if cur.fetchone():
                    raise ValueError("An order item cannot move between orders")
                for table, columns in TABLE_FIELDS.items():
                    key = columns[0]
                    fields = ", ".join(columns)
                    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in columns[1:])
                    cur.execute(f"INSERT INTO raw.{table} ({fields}) SELECT {fields} FROM batch_{table} ON CONFLICT ({key}) DO UPDATE SET {updates}")
                cur.execute("DELETE FROM raw.order_items i USING batch_orders o WHERE i.order_id = o.order_id AND NOT EXISTS (SELECT 1 FROM batch_order_items b WHERE b.order_item_id = i.order_item_id)")
            # Cross-table business constraints cannot be expressed as CHECK clauses.
            cur.execute("SELECT 1 FROM raw.orders o JOIN raw.sessions s USING (session_id) WHERE o.customer_id <> s.customer_id OR o.order_ts < s.session_ts LIMIT 1")
            if cur.fetchone():
                raise ValueError("Order customer/time must agree with its session")
            cur.execute("SELECT 1 FROM raw.orders o LEFT JOIN raw.order_items i USING (order_id) WHERE i.order_id IS NULL LIMIT 1")
            if cur.fetchone():
                raise ValueError("Every order must have at least one item")
            for table in TABLE_FIELDS:
                cur.execute(f"SELECT count(*) FROM raw.{table}")
                counts[table] = cur.fetchone()[0]
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=Path("data/sample"))
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    args = parser.parse_args()
    counts = run(args.directory, mode=args.mode)
    print("Imported:", counts)


if __name__ == "__main__":
    main()
