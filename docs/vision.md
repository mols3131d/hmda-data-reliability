# 비전

> HMDA 데이터 품질 이상을 근거와 함께 재현·검증하는 로컬 Data Reliability Incident 기반.

파이프라인 성공만으로 품질 이상과 downstream 영향을 판단할 수 없다. HMDA LAR와 연도·주·대출 목적별 mart를 대상으로 탐지부터 복구 검증까지 재현한다.

## 목표

- Severity·owner를 가진 incident와 profile·metadata·lineage evidence 연결.
- Downstream 영향, 재처리 대상, remediation draft 산출.
- Remediation 적용 전 격리된 dbt 검증.
- 외부 human approval 확인 후 위험 작업 실행.
- Synthetic suite와 report로 workflow 품질 측정.

## 현재

| 영역 | 상태 |
|---|---|
| Data plane | HMDA CSV/Parquet 멱등 적재, dbt staging/mart/test/artifact 생성 |
| Lifecycle | Caller baseline과 실제 current로 4개 규칙 탐지; impact와 remediation draft 반환 |
| Recovery | Lifecycle과 분리된 approval gate와 backfill validation API |
| Evaluation | Lifecycle과 분리된 synthetic case 평가와 Markdown report |

탐지 규칙: volume drop, Null spike, schema drift, freshness delay. 실제 human approval 연동은 없다. Remediation은 코드·dbt test를 수정하지 않는다.

## 원칙

- **Evidence-first**: 판단은 profile, metadata, dbt artifact 기반.
- **Human-controlled**: 위험 작업은 외부 승인 후 실행.
- **Reproducible**: 같은 입력·설정은 같은 workflow 재현.
- **Scope-bounded**: DuckDB, dbt, Dagster, reliability contract만 소유.

## MVP 완료 기준

- 반복 적재에도 raw row 중복 없음.
- dbt build 성공과 최신 artifacts 생성.
- 모든 incident의 evidence, affected asset, remediation action 반환.
- Synthetic case detection/action 성공률 100%.
- 승인 backfill 후 적재 row count와 profile row count 일치.
- 미승인 backfill 실행 전 차단.

## 다음

1. 외부 approval과 감사 이력을 Dagster에 연결.
2. Remediation을 격리된 dbt compile/build로 검증.
3. Null spike, schema drift, freshness delay end-to-end evaluation 추가.

## 비목표

Lakehouse, 대규모 분산처리, cloud 배포, 승인 없는 자동 복구, full catalog/observability, 범용 자동 RCA, 대출 정책·신용 위험 ML.
