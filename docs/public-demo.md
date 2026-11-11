# Public demo deployment

The online demo is a browser-only presentation of verified aggregate reporting data.
It does not run PostgreSQL, Python or Streamlit in the visitor browser.

On main-branch pushes, CI generates synthetic data, loads PostgreSQL 16, runs dbt models
and data tests, reconciles CSVs against marts, executes Python/dashboard tests, and calls
`python -m commerce_pipeline.export_demo`. The exporter requires a fully successful
dbt build covering every model and test in the manifest plus independent metric verification before writing `demo/data.json`.
GitHub Pages then deploys the demo artifact in a separate job dependent on those checks.
Pull requests run validation but cannot publish a demo.

The repository stores demo source, not a committed data snapshot. The deployed JSON
contains synthetic aggregate marts and build provenance; visitors never receive database
credentials. The complete local application remains the reproducible engineering demo.
