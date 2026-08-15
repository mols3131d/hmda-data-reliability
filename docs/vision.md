# Vision: Evidence-First Data Reliability

> **목표:** HMDA 데이터 품질 이상을 근거와 함께 재현·검증하는 로컬 Data Reliability Incident 기반을 만든다.

**파이프라인 성공만으로 품질 이상과 downstream 영향을 판단할 수 없다.** HMDA LAR와 연도·주·대출 목적별 mart를 대상으로 탐지부터 복구 검증까지 재현한다.

## 목표

- Severity·owner를 가진 incident와 profile·metadata·lineage evidence 연결.
- Downstream 영향, 재처리 대상, remediation draft 산출.
- Remediation 적용 전 격리된 dbt 검증.
- 외부 human approval 확인 후 위험 작업 실행.
- Synthetic suite와 report로 workflow 품질 측정.

## Current Capability

| 영역 | 상태 |
| --- | --- |
| Data plane | HMDA CSV/Parquet 멱등 적재, dbt staging/mart/test/artifact 생성 |
| Lifecycle | Caller baseline과 실제 current로 4개 규칙 탐지; impact와 remediation draft 반환 |
| Recovery | Lifecycle과 분리된 approval gate와 backfill validation API |
| Evaluation | Lifecycle과 분리된 synthetic case 평가와 Markdown report |

> [!IMPORTANT]
> **현재 recovery는 외부 human approval 연동을 포함하지 않는다.** Remediation은 코드나 dbt test를 수정하지 않는다.

탐지 규칙은 volume drop, Null spike, schema drift, freshness delay다.

## 원칙

- **Evidence-first**: 판단은 profile, metadata, dbt artifact 기반.
- **Human-controlled**: 위험 작업은 외부 승인 후 실행.
- **Reproducible**: 같은 입력·설정은 같은 workflow 재현.
- **Scope-bounded**: DuckDB, dbt, Dagster, reliability contract만 소유.

## Current MVP

현재 MVP의 목표, milestone과 완료 경계는 [`development/mvp/README.md`](development/mvp/README.md)를 따른다. 다른 incident 유형과 운영 control-plane 확장은 MVP 이후 범위다.

## Beyond MVP

- `null_spike`, `schema_drift`, `freshness_delay` vertical slice 확장.
- Dagster reliability control-plane과 approval/audit integration 검토.

## Non-Goals

Lakehouse, 대규모 분산처리, cloud 배포, 승인 없는 자동 복구, full catalog/observability, 범용 자동 RCA, 대출 정책·신용 위험 ML.
