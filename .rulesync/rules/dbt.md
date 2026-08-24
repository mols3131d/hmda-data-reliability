---
root: false
targets:
  - claudecode
  - copilot
  - copilotcli
  - antigravity-ide
description: "Use when writing or editing dbt models, sources, macros, schema.yml, or tests under dbt/. Covers staging/marts materialization, HMDA grain, and source contracts."
globs:
  - "dbt/**"
copilot:
  name: "dbt"
---

- Layers: `models/staging` → schema `staging`, materialize `view`; `models/marts` → schema `marts`, materialize `table`. Config: `dbt/dbt_project.yml`.
- Raw source of truth: `models/sources.yml` (`raw.hmda_loans`). No alternate raw without contract update.
- Staging `stg_hmda_loans`: analysis cleanup; keep `state_code` / `county_code` nullable when source allows.
- Mart `mart_hmda_loan_outcomes`: grain `activity_year + state_code + loan_purpose`; keep unique-grain tests in `schema.yml`.
- Schema names: macro `generate_schema_name` only — no env-hardcoded prefixes in models.
- Prefer YAML declarative tests over ad-hoc SQL.
