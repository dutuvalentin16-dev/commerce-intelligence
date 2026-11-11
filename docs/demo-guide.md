# Reproducible demo and technical walkthrough

## Start the demo

Requirements: Python 3.11+, Docker Desktop running, Git, and Make for the shortcut.
Clone the public repository, then prepare the local environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
make demo
make dashboard
```

On systems without Make use the explicit commands in the README.
`make demo` replaces the local demo raw data, builds models, runs dbt tests, reconciles metrics
and executes all Python integration tests. It stops on an error. Dashboard: localhost:8501.
Use `make verify` to recheck a built default demo; `make down` stops PostgreSQL and preserves
its data volume. Never point this demo workflow at a production database.

## Ten-minute walkthrough

1. **Problem and scope (1 min):** consistent revenue and conversion across reports. Synthetic
   ecommerce data and reproducible fixture outputs, without measured commercial outcomes.
2. **Architecture (2 min):** trace CSV → transactional COPY → raw constraints → staging →
   order/item facts and customer/product dimensions → marts → dashboard. Explain each layer's responsibility.
3. **SQL (2 min):** open `fct_orders.sql`, `int_orders_enriched.sql` and `mart_channel_performance.sql`.
   Explain grain, SUM, GROUP BY, LEFT JOIN, COALESCE and NULLIF. Identify why direct
   session-to-item joins would overcount sessions.
4. **Reliability (2 min):** show CI and the isolated-database tests. Explain what happens
   when quantity = 0 in the last CSV: the entire transaction rolls back.
5. **Reporting (2 min):** switch views, change the trend window, collapse to the icon rail,
   search a channel and export its CSV. Explain why the KPI cards do not change.
6. **Trade-offs (1 min):** full and incremental ingestion, simplified refunds and synthetic data.
   Explain complete item snapshots, Type 1 dimensions and full dbt rebuilds.

## Inspecting correctness

Calculate revenue for three orders directly from the CSV and trace the corresponding fact
and mart rows. Inspect join cardinality, rerun an incremental batch, and verify that an
invalid quantity rolls back the entire load. Compare source calculations with mart totals.

## Sharing

Public source: https://github.com/dutuvalentin16-dev/commerce-intelligence

Interactive reporting demo: https://dutuvalentin16-dev.github.io/commerce-intelligence/

The hosted demo uses verified aggregate snapshots and browser-side interactions. The
full Python/PostgreSQL/dbt/Streamlit application runs locally. Only validated synthetic
reporting data is published; no database credentials or connection are needed by visitors.
