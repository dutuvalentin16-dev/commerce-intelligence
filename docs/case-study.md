# Case study: from commerce events to consistent reporting

## Business question

How can sales, acquisition and customer reports agree on the same revenue definition?
The system models a small fictional ecommerce business. The goal is reliable
metric computation and verifiable delivery, using deterministic synthetic data.

## Implementation

Python produces a seeded dataset and loads five CSV tables into PostgreSQL using COPY.
All replacement loads run in one transaction. PostgreSQL constraints reject invalid keys,
statuses, quantities and prices. Five dbt staging views normalize the sources; order and order-item facts plus current
customer/product dimensions define the star schema. An order compatibility view feeds
four marts reporting daily sales, category
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
  zero. This is a simplified revenue definition, not full accounting.
- **Independent verification:** compare mart results with source CSV calculations; comparing
  two marts alone can miss a shared modeling error.
- **Atomic ingestion:** full replacement and incremental UPSERT run in a single transaction.
  Each changed order includes its complete item list; removed lines are deleted, while
  omitted orders remain untouched. Reruns are idempotent and invalid batches roll back.
- **Restrained UI:** local SVG icons, real-data sparklines, searchable/exportable tables,
  persistent icon navigation and documented filter scope. The UI exposes metric provenance.

## Evidence

The seeded dataset yields 373 paid orders and 199,131.23 fictional RON of paid revenue.
AOV is 533.86 RON, session conversion is 33.91%, and 114 of 186 paying customers repeat.
These values are fixture outputs, not commercial outcomes or measured improvements.

Validation includes 51 dbt tests, 19 Python tests with both integration flags enabled,
independent CSV-to-mart reconciliation, and browser checks. Ingestion tests use isolated
PostgreSQL databases and verify both complete rerun equality and rollback after a late COPY
failure, incremental updates, duplicate keys and invalid batches. Dashboard tests cover views, chart filters, searches and navigation state.

## Boundaries and next iteration

The model uses two fact tables and two Type 1 dimensions, with documented grains and
relationships. Ingestion supports full loads and ordered incremental synthetic batches.
dbt facts and marts rebuild fully; dimensions do not retain historical versions. No external
API, orchestration platform or anomaly detection is implemented. A licensed public source
and persisted run history remain possible extensions.

See [data contracts](data-model.md), [demo walkthrough](demo-guide.md). Screenshots are in [the README](../README.md).
