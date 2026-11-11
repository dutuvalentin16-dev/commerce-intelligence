"""Real-database dashboard checks; run after the demo ingestion and dbt build."""
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("COMMERCE_DASHBOARD_TESTS") != "1",
    reason="Set COMMERCE_DASHBOARD_TESTS=1 after loading the default demo and dbt build",
)


def test_dashboard_views_and_chart_filter_preserve_dataset_kpis():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(Path(__file__).parents[1] / "dashboard/app.py")).run(timeout=30)
    expected = {"Paid revenue · RON": "199,131", "Paid orders": "373",
                "Average order value": "534 RON", "Session conversion": "33.9%",
                "Repeat buyer rate": "61.3%"}

    def check():
        assert not app.exception
        assert not app.error
        assert {m.label: m.value for m in app.metric} == expected

    check()
    for page in ("Acquisition", "Categories", "Metric guide", "Overview"):
        app.radio[0].set_value(page).run()
        check()
    for window in ("Last 30 days", "Last 14 days", "Full period"):
        app.segmented_control[0].set_value(window).run()
        check()
    app.button(key="sidebar-toggle").click().run()
    assert app.session_state["sidebar_collapsed"] is True
    check()
    app.button(key="sidebar-toggle").click().run()
    assert app.session_state["sidebar_collapsed"] is False
    check()
    app.text_input(key="channel-search").set_value("organic").run()
    tables = [m.value for m in app.markdown if 'class="report-table"' in m.value]
    assert len(tables) == 1
    assert "Organic search" in tables[0]
    assert "Paid search" not in tables[0]
    check()
    app.text_input(key="workspace-search").set_value("acquisition").run()
    assert app.radio[0].value == "Acquisition"
    check()
