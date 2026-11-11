"""Compare built marts with independent CSV calculations (read-only)."""
from __future__ import annotations

import argparse
import csv
import os
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import psycopg


def verify(directory: Path) -> dict[str, object]:
    data = {}
    for table in ("orders", "order_items", "sessions", "products"):
        with (directory / f"{table}.csv").open(newline="", encoding="utf-8") as source:
            data[table] = list(csv.DictReader(source))
    orders = {o["order_id"]: o for o in data["orders"]}
    sessions = {s["session_id"]: s for s in data["sessions"]}
    products = {p["product_id"]: p for p in data["products"]}
    paid = [o for o in orders.values() if o["status"] == "paid"]
    customers = Counter(o["customer_id"] for o in paid)
    daily_revenue = defaultdict(Decimal)
    channel_revenue = defaultdict(Decimal)
    category_revenue = defaultdict(Decimal)
    # Include zero-revenue dates/channels/categories, as the SQL models do.
    def date_of(order):
        return datetime.fromisoformat(order["order_ts"]).astimezone(UTC).date()
    for o in orders.values():
        daily_revenue[date_of(o)] += Decimal(0)
    for s in sessions.values():
        channel_revenue[s["channel"]] += Decimal(0)
    for item in data["order_items"]:
        o = orders[item["order_id"]]
        category = products[item["product_id"]]["category"]
        category_revenue[category] += Decimal(0)
        if o["status"] == "paid":
            value = Decimal(item["unit_price"]) * int(item["quantity"])
            daily_revenue[date_of(o)] += value
            channel_revenue[sessions[o["session_id"]]["channel"]] += value
            category_revenue[category] += value

    expected_revenue = sum(daily_revenue.values(), Decimal(0))
    config = {"host": os.getenv("PGHOST", "localhost"),
              "port": int(os.getenv("PGPORT", "5434")),
              "dbname": os.getenv("PGDATABASE", "commerce"),
              "user": os.getenv("PGUSER", "commerce"),
              "password": os.getenv("PGPASSWORD", "commerce"), "connect_timeout": 5}
    with psycopg.connect(**config) as conn:
        def matches(label, actual, expected):
            if actual != expected:
                raise ValueError(f"{label} mismatch: database={actual!r}, CSV={expected!r}")

        for mart, key, expected in (
            ("mart_daily_sales", "order_date", dict(daily_revenue)),
            ("mart_channel_performance", "channel", dict(channel_revenue)),
            ("mart_category_performance", "category", dict(category_revenue)),
        ):
            # Identifiers come exclusively from this constant tuple.
            actual = dict(conn.execute(f"SELECT {key}, net_revenue FROM analytics.{mart}"))
            matches(mart, actual, expected)
        actual = conn.execute(
            "SELECT SUM(all_orders), SUM(paid_orders) FROM analytics.mart_daily_sales"
        ).fetchone()
        matches("order counts", actual, (len(orders), len(paid)))
        actual = conn.execute(
            "SELECT SUM(sessions), SUM(converted_sessions) FROM analytics.mart_channel_performance"
        ).fetchone()
        matches("conversion counts", actual, (len(sessions), len({o["session_id"] for o in paid})))
        actual = conn.execute(
            "SELECT paying_customers, repeat_customers, total_customer_revenue "
            "FROM analytics.mart_customer_repeat"
        ).fetchone()
        matches("repeat customers", actual,
                (len(customers), sum(n >= 2 for n in customers.values()), expected_revenue))
    return {"revenue": str(expected_revenue), "orders": len(orders),
            "paid_orders": len(paid), "sessions": len(sessions),
            "paying_customers": len(customers),
            "repeat_customers": sum(n >= 2 for n in customers.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("data/sample"))
    args = parser.parse_args()
    print("CSV → mart verification passed:", verify(args.directory))


if __name__ == "__main__":
    main()
