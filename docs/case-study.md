# Case study: from commerce events to consistent reporting

## Business question

How can sales, acquisition and customer reports agree on the same revenue definition?
This personal project models a small fictional ecommerce business. The goal is reliable
metric computation and verifiable delivery, using synthetic data rather than employer data.

## Implementation

Python produces a seeded dataset and loads five CSV tables into PostgreSQL using COPY.
All replacement loads run in one transaction. PostgreSQL constraints reject invalid keys,
statuses, quantities and prices. Five dbt staging views normalize the sources; one
order-grain intermediate model sums line items; four marts report daily sales, category
performance, acquisition and repeat buyers. Streamlit displays these models in four views. A browser-based public demo presents a
validated snapshot of the same marts, deployed through GitHub Pages after CI succeeds.

The data contains 250 customers, 40 products, 1,100 sessions, 423 orders and 827 order items.
This is a local batch pipeline, with the same generation → ingestion → dbt → verification
sequence executed automatically by GitHub Actions on Ubuntu.

## Decisions worth explaining

- **Order grain before reporting:** aggregate line items before counting orders. This
  prevents multi-item orders from multiplying the paid-order count.
- **Session grain before conversion:** pre-aggregate orders per session and use a LEFT JOIN
  from sessions, retaining sessions without a purchase.
- **Revenue contract:** paid quantity × unit price; cancelled/refunded orders contribute
  zero. This is a simplified portfolio definition, not full accounting.
- **Independent verification:** compare mart results with source CSV calculations; comparing
  two marts alone can miss a shared modeling error.
- **Atomic replacement:** practical for the small demo and straightforward to test. It is
  explicitly not incremental ingestion and would need replacement for large mutable sources.
- **Restrained UI:** local SVG icons, real-data sparklines, searchable/exportable tables,
  persistent icon navigation and documented filter scope. The UI exposes metric provenance.

## Evidence

The seeded dataset yields 373 paid orders and 199,131.23 fictional RON of paid revenue.
AOV is 533.86 RON, session conversion is 33.91%, and 114 of 186 paying customers repeat.
These values are fixture outputs, not commercial outcomes or measured improvements.

Validation includes 32 dbt tests, 10 Python tests with both integration flags enabled,
independent CSV-to-mart reconciliation, and browser checks. Ingestion tests use isolated
PostgreSQL databases and verify both complete rerun equality and rollback after a late COPY
failure. Dashboard tests cover views, chart filters, searches and navigation state.

## Boundaries and next iteration

The current model is staging plus aggregates, not a dimensional star schema. No external
API, incremental loading, orchestration platform or anomaly detection is claimed.
Next iterations should add documented facts/dimensions, a licensed public source and run
history before introducing a deterministic anomaly system.

See [data contracts](data-model.md), [demo walkthrough](demo-guide.md). Screenshots are in [the README](../README.md).
