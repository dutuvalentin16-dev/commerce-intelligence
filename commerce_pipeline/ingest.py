"""Atomic, rerunnable CSV -> PostgreSQL ingestion using COPY."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from commerce_pipeline.generate_sample_data import TABLE_FIELDS

ROOT = Path(__file__).resolve().parents[1]


def run(directory: Path) -> dict[str, int]:
    import psycopg

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
            # Single transaction: a failed import rolls back all imported tables.
            cur.execute("TRUNCATE raw.order_items, raw.orders, raw.sessions, raw.products, raw.customers")
            for table in TABLE_FIELDS:
                fields = ", ".join(TABLE_FIELDS[table])
                with cur.copy(f"COPY raw.{table} ({fields}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)") as copy:
                    with (directory / f"{table}.csv").open("rb") as f:
                        while block := f.read(1024 * 1024):
                            copy.write(block)
                cur.execute(f"SELECT count(*) FROM raw.{table}")
                counts[table] = cur.fetchone()[0]
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=Path("data/sample"))
    args = parser.parse_args()
    counts = run(args.directory)
    print("Imported:", counts)


if __name__ == "__main__":
    main()
