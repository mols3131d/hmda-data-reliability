---
type: brief
title: RPI Domain Hardcoding Resolution
description: 2026-08-08 hardcoding review findings을 domain별 OpenSpec Change로 계획·구현·독립 리뷰한 결과.
tags:
  - rpi
  - configuration
  - hardcoding
---

> [!NOTE]
> `data_operations`, `data_platform`, `hmda_data`, `orchestration`의 material hardcoding finding을 각각 독립 Change로 처리했다. 각 Change는 approved Plan Review, strict OpenSpec validation, independent re-review `No findings` 상태다. `reliability`는 입력 review에서 Pass여서 변경하지 않았다.

## Inputs

- [Source Code Hardcoding Review](../../2026-08-08/20-58-review-source-code-hardcoding.md)
- [Data Operations Hardcoding Review](../../2026-08-08/21-15-review-data-operations-hardcoding.md)
- [Data Platform Hardcoding Review](../../2026-08-08/21-15-review-data-platform-hardcoding.md)
- [HMDA Data Hardcoding Review](../../2026-08-08/21-15-review-hmda-data-hardcoding.md)
- [Orchestration Hardcoding Review](../../2026-08-08/21-15-review-orchestration-hardcoding.md)
- [Reliability Hardcoding Review](../../2026-08-08/21-15-review-reliability-hardcoding.md)

## RPI Handoff

| Domain | Change | Research | Plan Review | Apply | Implementation Review | Gate |
| --- | --- | --- | --- | --- | --- | --- |
| `data_operations` | `data-operations-centralize-runtime-settings` | review findings transferred to proposal/spec/design | approved, loop 3 | complete | findings routed to orchestration scope; public API gap fixed | ready |
| `data_platform` | `data-platform-require-database-path` | review finding transferred to proposal/spec/design | approved, loop 1 | complete | No findings | ready |
| `hmda_data` | `hmda-data-align-ingestion-contracts` | review findings transferred to proposal/spec/design | approved, loop 2 | complete | No findings after three repair loops | ready |
| `orchestration` | `orchestration-consume-runtime-settings` | review finding transferred to proposal/spec/design | approved, loop 2 | complete | precedence and empty-config findings fixed | ready |
| `reliability` | none | input review Pass | not required | not required | not required | no material configuration finding |

## Accepted Outcomes

- Data Operations owns environment-to-request parsing through `data_operation_request_from_environment()`.
- Dagster resource consumes the canonical request defaults and only applies explicit resource overrides.
- dbt profile requires `PROJECT_PIVOT_DUCKDB_PATH`; it no longer chooses an independent DuckDB default.
- HMDA full/partition loaders create the requested one- or two-part target schema and reject unsupported multipart targets before load.
- HMDA ingestion and EDA share header/null string/sample-size CSV parse semantics without adding ingestion provenance columns to EDA evidence.

## Validation

| Check | Result |
| --- | --- |
| Four Change strict OpenSpec validations | Pass |
| Cross-domain regression suite | 67 passed |
| Final HMDA ingestion and EDA suite | 36 passed |
| Final independent HMDA implementation review | No findings |

## Remaining Risks

- 이 작업은 configuration ownership과 HMDA parse/table-target contracts에 한정했다. MVP vertical slice의 P1 runtime risk인 dbt artifact retention과 Dagster dbt skip/materialization semantics는 별도 Change가 필요하다.
- 세 Change는 아직 archive되지 않았다. archive 전에 current specs와의 sync/ownership 절차를 수행해야 한다.
