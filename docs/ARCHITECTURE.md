# Architecture: Local HMDA Reliability Pipeline

**핵심 경계는 분석과 위험 작업의 분리다.** 로컬 HMDA 데이터를 DuckDB Bronze에 적재하고 dbt로 Silver·Gold를 만든다. Reliability lifecycle은 raw table과 dbt artifact를 읽어 incident와 remediation draft를 계산하지만, approval 이후 recovery와 evaluation은 별도 API가 담당한다.

## System Flow

```mermaid
flowchart LR
    files[HMDA CSV / Parquet] --> raw[Bronze]
    raw --> dbt[Silver / Gold]
    dbt --> artifacts[dbt artifacts]
    raw --> lifecycle[Reliability lifecycle]
    artifacts --> lifecycle
    lifecycle --> draft[Remediation draft]
    approval[External approval] --> recovery[Backfill + validation]
```

## Execution Boundaries

| Area | Rule |
| --- | --- |
| Pipeline | Dagster `pipeline_job`은 Bronze 적재 후 dbt 분석만 실행한다. |
| Reliability lifecycle | Read-only다. approval, backfill, validation, evaluation, report file write를 수행하지 않는다. |
| Recovery | 외부 approval 뒤 별도 API로 실행한다. |
| Evaluation | Synthetic case 결과를 별도 API로 집계하고 report를 별도로 작성한다. |

## Design Constraints

- lifecycle은 caller가 제공한 baseline을 받아 profile, detection, impact, remediation draft만 계산한다.
- Dagster는 data plane 실행만 담당하며 reliability lifecycle을 자동으로 묶지 않는다.
- approval은 lifecycle 외부에서 결정하고, recovery API는 승인 정보를 입력으로 요구한다.
- ingestion과 dbt는 재실행 가능해야 하며, 같은 partition의 중복 row를 만들지 않는다.
- candidate dbt evidence와 current last-known-good artifact projection은 분리하며, current projection 변경은 검증된 target에 한정한다.

## Canonical Domain Contracts

세부 계약의 canonical source는 [`docs/domains/OVERVIEW`](domains/OVERVIEW.md)와 연결된 도메인 문서다.

| Need | Document |
| --- | --- |
| 원천 파일, Bronze 적재, descriptive EDA, 합성 결함 | [`HMDA Data`](domains/hmda-data.md) |
| 실행 request, 결과, dbt build와 promotion | [`Data Operations`](domains/data-operations.md) |
| DuckDB, dbt model·lineage, artifact projection primitive | [`Data Platform`](domains/data-platform.md) |
| Incident, impact, remediation, recovery, evaluation | [`Reliability`](domains/reliability.md) |
| Dagster asset graph와 config | [`Orchestration`](domains/orchestration.md) |

## Project Scope

| In scope | Out of scope |
| --- | --- |
| 로컬 DuckDB, HMDA 적재, dbt model, reliability control plane | 원천 다운로드, lakehouse, 분산 처리 |
| 승인된 backfill 검증과 evaluation report | human approval UI, 감사 시스템 |
| 로컬 Dagster graph | cloud 배포, production SLO, 장기 모니터링 |
