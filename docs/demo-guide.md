# Reproducible demo and interview walkthrough

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

On the original development machine use `source .venv311/bin/activate` instead of creating a
new environment. On systems without Make use the explicit commands in the README.
`make demo` replaces the local demo raw data, builds models, runs dbt tests, reconciles metrics
and executes all Python integration tests. It stops on an error. Dashboard: localhost:8501.
Use `make verify` to recheck a built default demo; `make down` stops PostgreSQL and preserves
its data volume. Never point this demo workflow at a production database.

## Ten-minute walkthrough

1. **Problem and scope (1 min):** consistent revenue and conversion across reports. Synthetic
   ecommerce data, personal AI-assisted project, no claimed business improvement.
2. **Architecture (2 min):** trace CSV → transactional COPY → raw constraints → staging →
   order enrichment → marts → dashboard. Explain each layer's responsibility.
3. **SQL (2 min):** open `int_orders_enriched.sql` and `mart_channel_performance.sql`.
   Explain grain, SUM, GROUP BY, LEFT JOIN, COALESCE and NULLIF. Identify why direct
   session-to-item joins would overcount sessions.
4. **Reliability (2 min):** show CI and the isolated-database tests. Explain what happens
   when quantity = 0 in the last CSV: the entire transaction rolls back.
5. **Reporting (2 min):** switch views, change the trend window, collapse to the icon rail,
   search a channel and export its CSV. Explain why the KPI cards do not change.
6. **Trade-offs (1 min):** full reload, simplified refunds and synthetic data; describe how
   incremental processing and dimensional models would change the implementation.

## Before an interview

Practice the walkthrough yourself. Be able to calculate revenue for three orders from the
CSV, explain each join, locate one failing test, and describe which code was AI-assisted.
A successful automated run is implementation evidence, not a substitute for these skills.

## Sharing

Public source: https://github.com/dutuvalentin16-dev/commerce-intelligence

Interactive reporting demo: https://dutuvalentin16-dev.github.io/commerce-intelligence/

The hosted demo uses verified aggregate snapshots and browser-side interactions. The
full Python/PostgreSQL/dbt/Streamlit application runs locally. Only validated synthetic
reporting data is published; no database credentials or connection are needed by visitors.
