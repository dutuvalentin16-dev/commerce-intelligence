from decimal import Decimal
from commerce_pipeline.sanity_check import check


def test_reconciled_revenue_and_sessions():
    result = check()
    assert result["paid_orders"] <= result["orders"] <= result["sessions"]
    assert Decimal(result["revenue"]) > 0
