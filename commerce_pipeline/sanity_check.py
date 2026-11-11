"""Offline sanity check of source-data semantics (does not replace dbt tests)."""
from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal

from commerce_pipeline.generate_sample_data import generate


def check() -> dict[str, object]:
    data = generate()
    sessions = {r["session_id"]: r for r in data["sessions"]}
    orders = {r["order_id"]: r for r in data["orders"]}
    items_by_order = defaultdict(list)
    for item in data["order_items"]:
        items_by_order[item["order_id"]].append(item)
    channel_counts = Counter(s["channel"] for s in sessions.values())
    channel_paid_sessions = Counter()
    channel_revenue = defaultdict(Decimal)
    total_revenue = Decimal(0)
    paid_orders = 0
    for order in orders.values():
        channel = sessions[order["session_id"]]["channel"]
        if order["status"] != "paid":
            continue
        paid_orders += 1
        channel_paid_sessions[channel] += 1
        order_revenue = sum(
            (Decimal(i["unit_price"]) * int(i["quantity"]) for i in items_by_order[order["order_id"]]),
            Decimal(0),
        )
        channel_revenue[channel] += order_revenue
        total_revenue += order_revenue
    assert total_revenue == sum(channel_revenue.values(), Decimal(0))
    assert all(channel_paid_sessions[c] <= n for c, n in channel_counts.items())
    return {"sessions": len(sessions), "orders": len(orders),
            "paid_orders": paid_orders, "revenue": str(total_revenue),
            "channels": dict(channel_counts)}


if __name__ == "__main__":
    print(check())
