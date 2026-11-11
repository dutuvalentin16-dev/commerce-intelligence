"""Portfolio reporting workspace backed by tested dbt analytics marts."""
from __future__ import annotations

import os
from html import escape
from pathlib import Path
from urllib.parse import quote

import altair as alt
import pandas as pd
import psycopg
import streamlit as st

from dashboard.ui import icon, sparkline

st.set_page_config(page_title="Commerce · Intelligence", page_icon="◒", layout="wide", initial_sidebar_state="expanded")
st.html(f"<style>{Path(__file__).with_name('styles.css').read_text()}</style>")
icon_css = (
    '[data-testid="stSidebar"] .stTextInput input, .stTextInput input {background-image:url("data:image/svg+xml,' + quote(icon('search'))
    + '");background-position:12px center;background-size:16px;background-repeat:no-repeat;padding-left:36px;}'
    + '.stDownloadButton button::before {content:"";width:16px;height:16px;display:block;'
    + 'background:center/contain no-repeat url("data:image/svg+xml,' + quote(icon('download')) + '");}'
    + '.st-key-refresh-data button::before {content:"";width:16px;height:16px;display:block;'
    + 'background:center/contain no-repeat url("data:image/svg+xml,' + quote(icon('refresh')) + '");}'
)
st.html('<style>' + icon_css + '</style>')
st.session_state.setdefault("sidebar_collapsed", False)
collapsed = st.session_state.sidebar_collapsed


def toggle_sidebar():
    st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed
    st.session_state["workspace-search"] = ""


toggle_icon = quote(icon('expand' if collapsed else 'collapse'))
sidebar_control_css = (
    '.st-key-sidebar-toggle button::after {content:"";width:18px;height:18px;display:block;'
    + f'background:center/contain no-repeat url("data:image/svg+xml,{toggle_icon}");}}'
)
if collapsed:
    sidebar_control_css += """
    [data-testid="stSidebar"] {width:72px!important;min-width:72px!important;max-width:72px!important;}
    [data-testid="stSidebarUserContent"] {padding:19px 12px;}
    .brand {margin-bottom:65px;gap:0;}
    .brand > div:not(.brand-mark), .brand-toggle, .nav-label, .side-note, .side-tag,
    .sidebar-footer, [data-testid="stSidebar"] .stTextInput, [data-testid="stSidebar"] hr,
    .st-key-refresh-data {display:none!important;}
    [data-testid="stSidebar"] [data-testid="stRadioOption"] {width:48px!important;min-width:48px!important;justify-content:center;padding:11px 0;}
    [data-testid="stSidebar"] [data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] {
      position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;
    }
    .st-key-sidebar-toggle {top:80px!important;right:22px!important;}
    """
st.html('<style>' + sidebar_control_css + '</style>')


GREEN, GOLD, INK = "#17191f", "#9ba0a6", "#17191f"
CHANNEL_NAMES = {"organic": "Organic search", "paid_search": "Paid search", "direct": "Direct",
                 "email": "Email", "social": "Social"}


@st.cache_data(ttl=60)
def query(sql: str) -> pd.DataFrame:
    config = {"host": os.getenv("PGHOST", "localhost"),
              "port": int(os.getenv("PGPORT", "5434")),
              "dbname": os.getenv("PGDATABASE", "commerce"),
              "user": os.getenv("PGUSER", "commerce"),
              "password": os.getenv("PGPASSWORD", "commerce"), "connect_timeout": 5}
    with psycopg.connect(**config) as conn, conn.cursor() as cur:
        cur.execute(sql)
        return pd.DataFrame(cur.fetchall(), columns=[column.name for column in cur.description])


def panel(title: str, subtitle: str):
    st.markdown(f'<div class="panel-title">{escape(title)}</div>'
                f'<div class="panel-sub">{escape(subtitle)}</div>', unsafe_allow_html=True)


def report_table(frame, percent_columns=()):
    headings = ''.join(f'<th scope="col">{escape(str(c))}</th>' for c in frame.columns)
    rows = []
    for row in frame.itertuples(index=False, name=None):
        cells = []
        for i, (col, value) in enumerate(zip(frame.columns, row)):
            if col in percent_columns:
                text = f'<span class="score-badge">{float(value):.2f}%</span>'
            elif isinstance(value, (int, float)):
                text = f'{value:,.2f}' if 'RON' in str(col) else f'{value:,.0f}'
            else:
                text = escape(str(value))
            if i == 0:
                text = '<span class="table-icon">' + icon('acquisition', 16) + '</span>' + text
            cells.append(f'<td>{text}</td>')
        rows.append('<tr>' + ''.join(cells) + '</tr>')
    st.markdown('<div class="report-table-wrap"><table class="report-table"><thead><tr>' + headings
                + '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>', unsafe_allow_html=True)


def chart_style(chart):
    return (chart.configure_view(strokeWidth=0)
            .configure_axis(labelColor="#667085", titleColor="#475467", labelFontSize=11, labelFont="Inter", titleFont="Inter",
                            titleFontSize=10, domain=False, tickSize=0, gridColor="#edf1f2",
                            labelPadding=10, titlePadding=12)
            .configure_legend(labelColor="#475467", title=None))


def bar_chart(frame, dimension, value, title, color=GREEN, height=210):
    chart = alt.Chart(frame).mark_bar(color=color, cornerRadiusEnd=4, size=19).encode(
        x=alt.X(f"{value}:Q", title=None, axis=alt.Axis(format="~s", grid=True)),
        y=alt.Y(f"{dimension}:N", sort="-x", title=None, axis=alt.Axis(grid=False)),
        tooltip=[alt.Tooltip(f"{dimension}:N", title=dimension.title()),
                 alt.Tooltip(f"{value}:Q", title=title, format=",.2f")],
    ).properties(height=height)
    st.altair_chart(chart_style(chart), width="stretch", theme=None)


with st.sidebar:
    st.button("Expand navigation" if collapsed else "Collapse navigation",
              key="sidebar-toggle", on_click=toggle_sidebar)
    st.markdown('<div class="brand"><div class="brand-mark">' + icon('layers', 25) + '</div><div>'
                '<div class="brand-name">Commerce Studio</div><div class="brand-sub">Analytics workspace</div>'
                '</div><span class="brand-toggle">' + icon('chevrons', 14) + '</span></div>', unsafe_allow_html=True)
    nav_search = st.text_input("Find a view", placeholder="Search workspace…", label_visibility="collapsed", key="workspace-search")
    all_views = {"Overview": "overview", "Acquisition": "acquisition", "Categories": "categories", "Metric guide": "guide"}
    options = [name for name in all_views if nav_search.lower().strip() in name.lower()]
    st.markdown('<div class="nav-label">WORKSPACE</div>', unsafe_allow_html=True)
    if options:
        nav_css = ''.join(
            f'[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child({i + 1}) label::before '
            + '{content:"";display:block;width:17px;height:17px;flex-shrink:0;'
            + f'background:center/contain no-repeat url("data:image/svg+xml,{quote(icon(all_views[name]))}");}}'
            for i, name in enumerate(options))
        st.html('<style>' + nav_css + '</style>')
        view = st.radio("Workspace", options, label_visibility="collapsed")
    else:
        st.caption("No matching views. Clear search to see all pages.")
        view = "Overview"
    st.divider()
    st.markdown('<div class="side-note"><strong>Dataset</strong><br>Commerce demo · Q1 2026<br>Fictional RON · UTC</div>'
                '<div class="side-tag">Synthetic data</div>', unsafe_allow_html=True)
    if st.button("Refresh data", width="stretch", key="refresh-data"):
        query.clear()
        st.rerun()
    st.markdown('<div class="sidebar-footer"><div class="sidebar-avatar">CI</div><div>'
                '<strong>Portfolio workspace</strong><p>Commerce Intelligence Platform</p></div></div>', unsafe_allow_html=True)

try:
    daily = query("SELECT * FROM analytics.mart_daily_sales ORDER BY order_date")
    channels = query("SELECT * FROM analytics.mart_channel_performance ORDER BY net_revenue DESC")
    categories = query("SELECT * FROM analytics.mart_category_performance ORDER BY net_revenue DESC")
    repeat = query("SELECT * FROM analytics.mart_customer_repeat")
    source = query("SELECT COALESCE(SUM(i.quantity * i.unit_price), 0) AS revenue "
                   "FROM raw.order_items i JOIN raw.orders o USING (order_id) WHERE o.status = 'paid'")
except (psycopg.Error, OSError):
    st.title("Your analytics workspace is offline")
    st.error("PostgreSQL is unavailable or the dbt models have not been built.")
    st.code("docker compose up -d --wait postgres\npython -m commerce_pipeline.ingest\ndbt build --profiles-dir .")
    st.stop()

if daily.empty or channels.empty or categories.empty:
    st.title("Your workspace is ready for data")
    st.info("Generate the demo data, run ingestion, then run dbt build to populate this workspace.")
    st.stop()

# Keep Decimal values until the exact reconciliation is complete.
source_revenue = source.iloc[0]["revenue"]
reconciled = all(total == source_revenue for total in (
    daily.net_revenue.sum(), channels.net_revenue.sum(), categories.net_revenue.sum(),
    repeat.total_customer_revenue.sum()))
for frame in (daily, channels, categories, repeat):
    for col in frame.columns:
        if col not in ("order_date", "channel", "category"):
            frame[col] = pd.to_numeric(frame[col])
daily["order_date"] = pd.to_datetime(daily["order_date"])
channels["channel_label"] = channels.channel.map(CHANNEL_NAMES).fillna(channels.channel)
start, end = daily.order_date.min(), daily.order_date.max()
period = f"{start:%d %b} – {end:%d %b %Y}"
revenue, paid = float(daily.net_revenue.sum()), int(daily.paid_orders.sum())
all_orders = int(daily.all_orders.sum())
sessions, converted = int(channels.sessions.sum()), int(channels.converted_sessions.sum())
aov = revenue / paid if paid else None
conversion = converted / sessions if sessions else None
repeat_row = repeat.iloc[0] if not repeat.empty else None
repeat_rate = float(repeat_row.repeat_customer_rate) if repeat_row is not None and pd.notna(repeat_row.repeat_customer_rate) else None

headings = {"Overview": ("Commerce overview", "The complete picture of your commerce performance."),
            "Acquisition": ("Acquisition performance", "Understand which channels bring traffic, conversions and revenue."),
            "Categories": ("Category performance", "Explore sales contribution and estimated product margin."),
            "Metric guide": ("Behind the numbers", "Clear definitions. Traceable sources. Honest limitations.")}
title, subtitle = headings[view]
st.markdown('<div class="eyebrow">COMMERCE INTELLIGENCE / ANALYTICS WORKSPACE</div>'
            f'<div class="hero"><div><h1>{title}</h1><p>{subtitle}</p></div>'
            f'<div class="date-badge">{icon("calendar", 16)}{period}</div></div>', unsafe_allow_html=True)

if reconciled:
    st.markdown('<div class="quality"><span class="quality-text">Revenue cross-check · '
                'all 4 marts match raw paid-order revenue</span>'
                f'<span class="quality-status">{icon("check", 12)} Reconciled</span></div>', unsafe_allow_html=True)
else:
    st.error("Revenue mismatch detected between raw data and reporting marts. Rebuild and investigate before interpreting these metrics.")

st.caption("FULL DATASET · All KPI cards and breakdowns use the complete reporting period.")
weekly = daily.set_index("order_date").resample("W").sum(numeric_only=True)
spark_values = [weekly.net_revenue, weekly.paid_orders,
                (weekly.net_revenue / weekly.paid_orders.replace(0, float("nan"))).dropna()]
metrics = st.columns(5, gap=None)
for column, label, value, help_text in (
    (metrics[0], "Paid revenue · RON", f"{revenue:,.0f}", "Paid item quantity × unit price; cancelled/refunded orders excluded."),
    (metrics[1], "Paid orders", f"{paid:,}", f"{all_orders:,} total orders, including cancelled and refunded."),
    (metrics[2], "Average order value", f"{aov:,.0f} RON" if aov is not None else "—", "Paid-order revenue / paid orders."),
    (metrics[3], "Session conversion", f"{conversion:.1%}" if conversion is not None else "—", f"{converted:,} converted sessions / {sessions:,} sessions, attributed by session date."),
    (metrics[4], "Repeat buyer rate", f"{repeat_rate:.1%}" if repeat_rate is not None else "—", "Customers with 2+ paid orders / customers with 1+ paid order in the dataset."),
):
    index = metrics.index(column)
    with column, st.container(key=f"kpi-{index}"):
        st.metric(label, value, help=help_text)
        if index < len(spark_values):
            st.markdown(sparkline(spark_values[index], f"metric-{index}"), unsafe_allow_html=True)

if view == "Overview":
    trend_col, mix_col = st.columns([1.8, 1], gap="medium")
    with trend_col, st.container(border=True, key="panel-trend"):
        panel("Revenue over time", "Daily paid-order revenue, with a 7-day rolling average")
        window = st.segmented_control("Trend window", ["Full period", "Last 30 days", "Last 14 days"],
                                      default="Full period", label_visibility="collapsed")
        # Fill dates before computing the average, including days with no orders.
        trend = daily.set_index("order_date")[["net_revenue"]].reindex(pd.date_range(start, end), fill_value=0)
        trend.index.name = "order_date"
        trend["rolling_average"] = trend.net_revenue.rolling(7, min_periods=7).mean()
        if window != "Full period":
            days = 30 if window == "Last 30 days" else 14
            trend = trend.loc[end - pd.Timedelta(days=days - 1):]
        trend = trend.reset_index()
        base = alt.Chart(trend).encode(x=alt.X("order_date:T", title=None, axis=alt.Axis(format="%d %b", grid=False)))
        area = base.mark_area(color=GREEN, opacity=.13).encode(
            y=alt.Y("net_revenue:Q", title="RON", axis=alt.Axis(format="~s")),
            tooltip=[alt.Tooltip("order_date:T", title="Date", format="%d %b %Y"),
                     alt.Tooltip("net_revenue:Q", title="Revenue (RON)", format=",.2f")])
        average = base.mark_line(color=GREEN, strokeWidth=2.8).encode(y="rolling_average:Q")
        st.altair_chart(chart_style((area + average).properties(height=230)), width="stretch", theme=None)
        st.caption("Pale area: daily revenue · Solid line: 7-day average · Window affects this chart only.")
    with mix_col, st.container(border=True, key="panel-mix"):
        panel("Revenue by category", "Contribution to total paid-order revenue · RON")
        bar_chart(categories, "category", "net_revenue", "Revenue (RON)", height=265)
        top = categories.iloc[0]
        st.caption(f"{top.category} leads with {top.net_revenue / revenue:.1%} of revenue." if revenue else "No paid-order revenue.")

    top_channel = channels.iloc[0]
    best_conversion = channels.sort_values("conversion_rate", ascending=False).iloc[0]
    insights = st.columns(3)
    paying = int(repeat_row.paying_customers) if repeat_row is not None else 0
    repeats = int(repeat_row.repeat_customers) if repeat_row is not None else 0
    for col, label, value, note in (
        (insights[0], "Leading revenue channel", top_channel.channel_label,
         f"{top_channel.net_revenue / revenue:.1%} of paid-order revenue" if revenue else "No paid-order revenue"),
        (insights[1], "Highest session conversion", best_conversion.channel_label,
         f"{best_conversion.conversion_rate:.1%} of channel sessions converted"),
        (insights[2], "Returning buyers", f"{repeats} of {paying}", "Paying customers with at least two paid orders"),
    ):
        col.markdown(f'<div class="insight"><div class="insight-label">{escape(label)}</div>'
                     f'<div class="insight-value">{escape(value)}</div>'
                     f'<div class="insight-note">{escape(note)}</div></div>', unsafe_allow_html=True)

if view in ("Overview", "Acquisition"):
    with st.container(border=True, key="panel-channels"):
        left, right = st.columns([4, 1])
        with left:
            panel("Channel performance", "Session-grain acquisition metrics · full dataset")
            channel_search = st.text_input("Search channels", placeholder="Search channels…", label_visibility="collapsed", key="channel-search")
        table = channels[["channel_label", "sessions", "converted_sessions", "conversion_rate", "net_revenue"]].copy()
        table.columns = ["Channel", "Sessions", "Converted sessions", "Conversion", "Revenue (RON)"]
        table = table[table.Channel.str.contains(channel_search, case=False, regex=False)]
        with right:
            st.download_button("Export CSV", table.to_csv(index=False).encode(), "channel-performance.csv", "text/csv", width="stretch")
        display = table.copy()
        display["Conversion"] *= 100
        report_table(display, percent_columns=("Conversion",))
    if view == "Acquisition":
        a, b = st.columns(2)
        with a, st.container(border=True, key="panel-left"):
            panel("Revenue by channel", "Paid revenue attributed to acquisition sessions · RON")
            bar_chart(channels, "channel_label", "net_revenue", "Revenue (RON)", height=270)
        with b, st.container(border=True, key="panel-right"):
            panel("Conversion by channel", "Sessions containing at least one paid order")
            rates = channels.assign(conversion_percent=channels.conversion_rate * 100)
            bar_chart(rates, "channel_label", "conversion_percent", "Conversion (%)", GOLD, 270)
        st.caption("Revenue is grouped by acquisition channel; conversion is converted sessions / sessions, not orders / sessions.")

if view == "Categories":
    a, b = st.columns(2)
    with a, st.container(border=True, key="panel-left"):
        panel("Revenue contribution", "Paid sales by product category · RON")
        bar_chart(categories, "category", "net_revenue", "Revenue (RON)", height=270)
    with b, st.container(border=True, key="panel-right"):
        panel("Estimated product margin", "Paid sales less synthetic product cost · RON")
        bar_chart(categories, "category", "estimated_product_margin", "Product margin (RON)", GOLD, 270)
    with st.container(border=True, key="panel-breakdown"):
        panel("Category breakdown", "Product margin excludes tax, shipping, overhead and acquisition cost")
        table = categories.rename(columns={"category": "Category", "paid_units": "Paid units",
                                          "net_revenue": "Revenue (RON)", "estimated_product_margin": "Product margin (RON)"})
        report_table(table)
        st.download_button("Export categories", table.to_csv(index=False).encode(), "category-performance.csv", "text/csv")

if view == "Metric guide":
    with st.container(border=True, key="panel-definitions"):
        panel("One definition for every metric", "Reporting contracts, not black-box numbers")
        st.dataframe(pd.DataFrame([
            ("Paid-order revenue", "Σ quantity × unit price for paid orders", "mart_daily_sales"),
            ("Paid orders", "Count of orders with status = paid", "mart_daily_sales"),
            ("Average order value", "Paid-order revenue / paid orders", "mart_daily_sales"),
            ("Session conversion", "Sessions with ≥1 paid order / all sessions", "mart_channel_performance"),
            ("Repeat buyer rate", "Customers with ≥2 paid orders / paying customers", "mart_customer_repeat"),
            ("Estimated product margin", "Paid quantity × (unit price − unit cost)", "mart_category_performance"),
        ], columns=["Metric", "Definition", "dbt model"]), hide_index=True, width="stretch")
    with st.container(border=True, key="panel-lineage"):
        panel("Source to insight", "An intentionally small, inspectable architecture")
        st.code("Synthetic CSVs → Python COPY → PostgreSQL raw\n    → dbt staging → order enrichment → 4 marts → this dashboard", language=None)
        st.markdown("**Revenue cross-check:** exact comparison of all four mart revenue totals against raw paid order items. "
                    "This is a cached read-time check, not a live pipeline monitoring service.")
        st.markdown("**Coverage:** all metrics cover the dataset above. Repeat buyers are measured within this period, "
                    "not lifetime retention. Dates use UTC; revenue is grouped by order date, sessions by session date.")
        st.markdown("**Limitations:** synthetic data and fictional RON. Cancelled and refunded orders contribute zero. "
                    "No partial refund, tax or shipping accounting. Product margin is not net profit. "
                    "No external source, incremental ingestion or anomaly detection has been implemented yet.")

st.markdown('<div class="footer"><span>COMMERCE INTELLIGENCE · PERSONAL PORTFOLIO PROJECT</span>'
            '<span>Synthetic data · Fictional RON · Data cached for up to 60 seconds</span></div>', unsafe_allow_html=True)
