# Domain Guides: Ownership And Reading Paths

이 directory는 각 domain의 책임, 비책임과 주요 reading path를 사람이 빠르게 이해하도록 설명한다. **Normative capability contract의 canonical source는 [`../../openspec/specs/`](../../openspec/specs/)다.** Domain guide는 OpenSpec Spec을 대체하거나 독립적으로 override하지 않는다.

## Ownership Map

| Domain | Owns | Main input and output | Does not own |
| --- | --- | --- | --- |
| [HMDA Data](hmda-data.md) | 원천 파일 발견·검증, Bronze 적재, descriptive EDA, 합성 결함 파일 | CSV/Parquet → `raw.hmda_loans`, EDA evidence, synthetic Parquet | 실행 조합, dbt 변환, incident 판단 |
| [Data Operations](data-operations.md) | 실행 request·순서·결과, dbt execution/promotion, 오류 경계 | request → raw load, dbt build, lifecycle result | 파일 파싱, DuckDB 세부 구현, incident 규칙 |
| [Data Platform](data-platform.md) | DuckDB helper, dbt source·model·test·lineage, artifact projection primitive | `raw.hmda_loans` → staging/mart, dbt artifact pair identity | 원천 적재, dbt subprocess 실행, promotion 결정, orchestration |
| [Reliability](reliability.md) | profile, incident, 영향 분석, remediation, recovery, evaluation | raw table + dbt artifacts → lifecycle/recovery/evaluation result | 외부 approval 결정과 Dagster orchestration |
| [Orchestration](orchestration.md) | Dagster asset graph와 config 변환 | `raw_hmda_loans` → `dbt_loan_analytics` | domain business logic, reliability control-plane |

이 표는 architecture/domain ownership을 설명하는 guide다. Normative behavior나 capability requirement가 필요하면 대응 `openspec/specs/**`를 확인하고, 실제 구현 상태는 source/tests와 matching-revision evidence로 검증한다.

## Goal-Based Reading Paths

| Goal | Read in order |
| --- | --- |
| 원천 파일부터 분석 mart까지 이해 | [HMDA Data](hmda-data.md) → [Data Platform](data-platform.md) → [Data Operations](data-operations.md) |
| HMDA descriptive EDA 이해 | [HMDA Data](hmda-data.md) |
| 품질 incident와 recovery 이해 | [Reliability](reliability.md) → [Data Operations](data-operations.md) → [Data Platform](data-platform.md) |
| Dagster 실행 경계 이해 | [Orchestration](orchestration.md) → [Data Operations](data-operations.md) |

시스템 흐름과 공통 경계는 [`ARCHITECTURE`](../ARCHITECTURE.md)에서 확인한다.
