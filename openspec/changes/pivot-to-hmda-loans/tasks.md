## 1. Source Discovery

- [x] 1.1 Inspect `data/raw/hmda` and record supported file extensions, sample filenames, row counts, and available columns.
- [x] 1.2 Decide the implementation module name: `hmda_data` or `loan_data`.
- [x] 1.3 Identify all active TLC/Taxi references in source, dbt, tests, docs, and scripts that must be replaced or removed.

## 2. HMDA Raw Foundation

- [x] 2.1 Add HMDA custom exceptions with user-safe messages and context-rich logging metadata.
- [x] 2.2 Implement DuckDB raw schema initialization for HMDA loan/application records.
- [x] 2.3 Implement HMDA CSV/Parquet file discovery under `data/raw/hmda`.
- [x] 2.4 Implement full HMDA raw load with `source_file`, `source_year`, and `ingested_at` metadata.
- [x] 2.5 Implement HMDA required-column validation for raw loads.
- [x] 2.6 Add HMDA synthetic quality-case generation for row-count drop, null spike, schema drift, and freshness delay.
- [x] 2.7 Replace or remove TLC raw-load tests with HMDA raw-load tests.

## 3. Partition Ingestion

- [x] 3.1 Replace taxi pickup-date partition request fields with HMDA `source_year` and optional `source_file` partition inputs.
- [x] 3.2 Implement isolated HMDA year/file partition loading.
- [x] 3.3 Implement idempotent overwrite behavior for repeated HMDA year/file loads.
- [x] 3.4 Add tests proving HMDA outlier rows are preserved during partition ingestion.

## 4. dbt Analytics

- [x] 4.1 Replace dbt raw taxi sources with HMDA raw source declarations.
- [x] 4.2 Replace taxi staging models with `stg_hmda_loans`.
- [x] 4.3 Replace `mart_daily_taxi_trips` with `mart_hmda_loan_outcomes`.
- [x] 4.4 Add dbt tests for HMDA staging not-null columns and mart grain uniqueness.
- [x] 4.5 Update dbt analytics tests to validate HMDA models, artifacts, and idempotent builds.

## 5. Pipeline and Dagster

- [x] 5.1 Update pipeline runner and CLI defaults from TLC/Taxi to HMDA/Loan paths and labels.
- [x] 5.2 Rename or replace Dagster `raw_taxi_data` with `raw_hmda_loans`.
- [x] 5.3 Rename or replace Dagster `dbt_analytics` metadata with `dbt_loan_analytics` where the asset contract requires it.
- [x] 5.4 Ensure `mvp_pipeline_job` materializes `raw_hmda_loans`, `dbt_loan_analytics`, and `mvp_incident_lifecycle` in order.
- [x] 5.5 Update orchestration tests to assert HMDA asset keys and metadata.

## 6. Documentation and Cleanup

- [x] 6.1 Update README, architecture, and vision docs to describe the HMDA loan data product direction in Korean.
- [x] 6.2 Remove stale TLC/Taxi docs or clearly mark them as archived history if retained.
- [x] 6.3 Rename test packages and file paths away from `taxi_data` when the implementation module is renamed.
- [x] 6.4 Run formatting, unit tests, dbt validation, and Dagster definition validation.
- [x] 6.5 Review the final diff for leftover TLC/Taxi references that are not intentionally archived.
