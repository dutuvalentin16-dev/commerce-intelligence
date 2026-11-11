"""Generate reproducible synthetic commerce data. No real customer PII."""
from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

TABLE_FIELDS = {
    "customers": ["customer_id", "signup_date", "region"],
    "products": ["product_id", "category", "unit_cost"],
    "sessions": ["session_id", "customer_id", "session_ts", "channel", "landing_page"],
    "orders": ["order_id", "customer_id", "session_id", "order_ts", "status"],
    "order_items": ["order_item_id", "order_id", "product_id", "quantity", "unit_price"],
}


def generate(seed: int = 42, days: int = 90, n_sessions: int = 1100) -> dict[str, list[dict]]:
    """Make deterministic rows; order -> session -> customer links are consistent."""
    if days <= 0 or n_sessions <= 0:
        raise ValueError("days and n_sessions must be positive")
    rng = random.Random(seed)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    regions = ["Bucuresti", "Cluj", "Iasi", "Timis", "Brasov"]
    categories = ["Fashion", "Home", "Electronics", "Beauty", "Sports"]
    channels = ["organic", "paid_search", "direct", "email", "social"]
    pages = ["/", "/products", "/category/fashion", "/category/home", "/category/beauty"]
    customers = [
        {"customer_id": i, "signup_date": (start - timedelta(days=rng.randint(0, 180))).date().isoformat(),
         "region": rng.choice(regions)}
        for i in range(1, 251)
    ]
    products = [
        {"product_id": i, "category": categories[(i - 1) % len(categories)],
         "unit_cost": f"{rng.uniform(12, 180):.2f}"}
        for i in range(1, 41)
    ]
    sessions: list[dict] = []
    orders: list[dict] = []
    items: list[dict] = []
    item_id = 1
    for sid in range(1, n_sessions + 1):
        customer_id = rng.randint(1, len(customers))
        session_ts = start + timedelta(days=rng.randrange(days), hours=rng.randint(0, 23),
                                       minutes=rng.randint(0, 59))
        channel = rng.choices(channels, weights=[38, 20, 22, 10, 10])[0]
        sessions.append({"session_id": sid, "customer_id": customer_id,
                         "session_ts": session_ts.isoformat(), "channel": channel,
                         "landing_page": rng.choice(pages)})
        # At most one order per session; intentionally all dates are UTC.
        chance = {"organic": .40, "paid_search": .32, "direct": .47,
                  "email": .53, "social": .20}[channel]
        if rng.random() >= chance:
            continue
        oid = len(orders) + 1
        order_ts = session_ts + timedelta(minutes=rng.randint(2, 52))
        status = rng.choices(["paid", "cancelled", "refunded"], weights=[87, 8, 5])[0]
        orders.append({"order_id": oid, "customer_id": customer_id,
                       "session_id": sid, "order_ts": order_ts.isoformat(), "status": status})
        for _ in range(rng.randint(1, 3)):
            product = rng.choice(products)
            cost = float(product["unit_cost"])
            price = cost * rng.uniform(1.25, 1.8)
            items.append({"order_item_id": item_id, "order_id": oid,
                          "product_id": product["product_id"], "quantity": rng.randint(1, 3),
                          "unit_price": f"{price:.2f}"})
            item_id += 1
    return {"customers": customers, "products": products, "sessions": sessions,
            "orders": orders, "order_items": items}


def write_csv(rows: dict[str, list[dict]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, fields in TABLE_FIELDS.items():
        with (output_dir / f"{name}.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows[name])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("data/sample"))
    args = parser.parse_args()
    rows = generate(seed=args.seed)
    write_csv(rows, args.output)
    print("Created synthetic CSVs:", ", ".join(f"{k}={len(v)}" for k, v in rows.items()))


if __name__ == "__main__":
    main()
