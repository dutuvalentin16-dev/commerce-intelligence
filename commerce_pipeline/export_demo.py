"""Publish a read-only reporting snapshot only after successful pipeline validation."""
from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from commerce_pipeline.verify_metrics import verify


def export(output: Path) -> None:
    results = json.loads(Path('target/run_results.json').read_text())['results']
    if len(results) != 42 or any(r['status'] not in ('success', 'pass') for r in results):
        raise ValueError('Run a successful complete dbt build before exporting the demo')
    baseline = verify(Path('data/sample'))
    config = {'host': os.getenv('PGHOST', 'localhost'), 'port': int(os.getenv('PGPORT', '5434')),
              'dbname': os.getenv('PGDATABASE', 'commerce'), 'user': os.getenv('PGUSER', 'commerce'),
              'password': os.getenv('PGPASSWORD', 'commerce'), 'connect_timeout': 5}
    tables = {'daily': ('mart_daily_sales', 'order_date'),
              'channels': ('mart_channel_performance', 'net_revenue DESC'),
              'categories': ('mart_category_performance', 'net_revenue DESC'),
              'repeat': ('mart_customer_repeat', 'paying_customers')}
    payload = {'metadata': {'generated_at': datetime.now(UTC).isoformat(),
                            'commit': os.getenv('GITHUB_SHA', 'local-build'),
                            'mode': 'Verified synthetic reporting snapshot', 'baseline': baseline}}
    with psycopg.connect(**config, row_factory=dict_row) as conn:
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        for key, (table, order) in tables.items():
            payload[key] = conn.execute(f'SELECT * FROM analytics.{table} ORDER BY {order}').fetchall()
    def encode(value):
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        raise TypeError(type(value).__name__)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, default=encode, indent=2) + '\n', encoding='utf-8')
    print('Verified demo snapshot written:', output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('demo/data.json'))
    export(parser.parse_args().output)


if __name__ == '__main__':
    main()
