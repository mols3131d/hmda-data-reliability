# Domain Contracts: Ownership And Reading Paths

**각 domain 문서는 책임과 비책임의 canonical source다.** 로컬 HMDA 데이터 파이프라인의 공개 API, 입력·출력, 비포함 범위를 domain별로 설명한다.

## Ownership Map

| Domain | Owns | Main input and output | Does not own |
| --- | --- | --- | --- |
| [HMDA Data](hmda-data.md) | 원천 파일 발견·검증, Bronze 적재, descriptive EDA, 합성 결함 파일 | CSV/Parquet → `raw.hmda_loans`, EDA evidence, synthetic Parquet | 실행 조합, dbt 변환, incident 판단 |
| [Data Operations](data-operations.md) | 실행 request·순서·결과, 오류 경계 | request → raw load, dbt build, lifecycle result | 파일 파싱, DuckDB 세부 구현, incident 규칙 |
| [Data Platform](data-platform.md) | DuckDB helper, dbt source·model·test·lineage | `raw.hmda_loans` → staging view → mart table | 원천 적재, dbt subprocess 실행, orchestration |
| [Reliability](reliability.md) | profile, incident, 영향 분석, remediation draft | raw table + dbt artifacts → lifecycle result | lifecycle 내 승인·backfill·report 작성 |
| [Orchestration](orchestration.md) | Dagster asset graph와 config 변환 | `raw_hmda_loans` → `dbt_loan_analytics` | domain business logic, reliability lifecycle |

## Goal-Based Reading Paths

| Goal | Read in order |
| --- | --- |
| 원천 파일부터 분석 mart까지 이해 | [HMDA Data](hmda-data.md) → [Data Platform](data-platform.md) → [Data Operations](data-operations.md) |
| HMDA descriptive EDA 이해 | [HMDA Data](hmda-data.md) |
| 품질 incident와 후속 조치 이해 | [Reliability](reliability.md) → [Data Operations](data-operations.md) |
| Dagster 실행 경계 이해 | [Orchestration](orchestration.md) → [Data Operations](data-operations.md) |

시스템 흐름과 공통 경계는 [`ARCHITECTURE`](../ARCHITECTURE.md)에서 확인한다.
