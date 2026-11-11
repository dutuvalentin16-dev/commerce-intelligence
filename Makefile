.PHONY: setup up generate ingest build dashboard test down demo verify
setup:
	python -m pip install -r requirements-lock.txt
up:
	docker compose up -d --wait postgres
generate:
	python -m commerce_pipeline.generate_sample_data
ingest:
	python -m commerce_pipeline.ingest
build:
	dbt build --profiles-dir .
dashboard:
	streamlit run dashboard/app.py
test:
	python -m pytest -q
down:
	docker compose down
verify:
	python -m commerce_pipeline.verify_metrics
	COMMERCE_INTEGRATION_TESTS=1 COMMERCE_DASHBOARD_TESTS=1 python -m pytest -q
demo:
	$(MAKE) up
	$(MAKE) generate
	$(MAKE) ingest
	$(MAKE) build
	$(MAKE) verify
