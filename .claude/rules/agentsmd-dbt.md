---
paths:
  - dbt/**/*
---

# dbt

- Layers: `models/staging` → schema `staging`, materialize `view`; `models/marts` → schema `marts`, materialize `table`. Config: `dbt/dbt_project.yml`.
- Raw source of truth: `models/sources.yml` (`raw.hmda_loans`). Do not add an alternate raw source without a contract update.
- Staging `stg_hmda_loans`: analysis cleanup; keep `state_code` / `county_code` nullable when source allows.
- Mart `mart_hmda_loan_outcomes`: grain `activity_year + state_code + loan_purpose`; keep unique-grain tests in `schema.yml`.
- Schema names use only the `generate_schema_name` macro. Do not hard-code environment prefixes in models.
- Prefer YAML declarative tests over ad-hoc SQL.
