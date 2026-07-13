# 비전

> HMDA 데이터 품질 이상을 근거와 함께 재현하고 검증하는 로컬 Data Reliability Incident 운영 기반을 만든다.

## 문제와 대상

파이프라인 성공 여부만으로는 데이터 품질 이상과 downstream 영향을 판단하기 어렵다. 이 프로젝트는 로컬 데이터 파이프라인을 개발·검증하는 사용자가 탐지부터 재처리 검증까지 같은 조건으로 반복 실행할 수 있게 한다.

기본 분석 대상은 HMDA 공개 LAR 대출 신청 데이터와 연도·주·대출 목적별 결과 mart다.

## 목표 상태

- 데이터 이상을 severity와 owner가 포함된 incident로 관리한다.
- profile, table metadata, dbt lineage artifact를 판단 근거로 연결한다.
- downstream 영향 범위와 재처리 대상을 명확히 산출한다.
- dbt test 개선안과 remediation 초안을 만들고, 적용 전에 격리된 dbt 검증을 수행한다.
- 위험 작업은 사람이 제공한 승인 기록을 확인한 뒤 Dagster에서 실행한다.
- synthetic incident suite와 evaluation report로 workflow 판단 품질을 측정한다.

## 현재 구현

| 영역 | 현재 상태 |
|---|---|
| 데이터 | HMDA CSV/Parquet를 DuckDB에 연도·파일 단위로 멱등 적재한다. |
| 분석 | dbt staging/mart를 만들고 test와 lineage artifact를 생성한다. |
| 탐지 | volume drop, Null spike, schema drift, freshness delay 규칙을 제공하며 end-to-end 실행은 volume drop을 시뮬레이션한다. |
| 근거와 영향 | raw table profile/metadata와 dbt manifest로 evidence와 downstream 영향을 만든다. |
| Remediation | 결정론적 LangGraph workflow가 초안과 검증 action을 제안하며 코드나 dbt test를 직접 수정하지 않는다. |
| 승인과 복구 | 승인 contract와 실행 gate를 제공한다. 로컬 평가의 `run_backfill=true` 경로는 승인 객체를 자동 생성하므로 실제 human approval 연동은 아니다. |
| 평가 | 단일 synthetic volume drop case의 탐지·action 성공률을 Markdown으로 기록한다. |

## 핵심 원칙

- **Evidence-first**: 모든 판단은 profile, metadata 또는 dbt artifact를 참조한다.
- **Workflow-first**: 탐지, 영향 분석, remediation, 재처리, 평가를 하나의 흐름으로 연결한다.
- **Human-controlled**: 실제 위험 작업은 외부 승인 연동 후에만 실행하는 것을 목표로 한다.
- **Locally reproducible**: 같은 입력과 설정으로 전체 workflow를 반복 실행할 수 있어야 한다.
- **Scope-bounded**: 현재 범위는 로컬 DuckDB, dbt, Dagster와 reliability contract로 제한한다.

## 현재 MVP 성공 기준

- 같은 source partition을 반복 적재해도 raw row가 중복되지 않는다.
- dbt build가 성공하고 최신 `manifest.json`과 `run_results.json`을 생성한다.
- 기본 synthetic case에서 `volume_drop`을 탐지하고 evidence, affected asset, remediation action을 반환한다.
- 정의된 synthetic case의 detection success rate와 action success rate가 100%다.
- 로컬 backfill 검증을 실행하면 재적재 row count와 profile row count가 일치한다.
- 승인되지 않은 backfill 요청은 실행 전에 차단된다.

## 다음 단계

- 외부 human approval 입력과 감사 이력을 Dagster 실행에 연결한다.
- remediation 제안을 격리된 dbt compile/build로 검증한다.
- Null spike, schema drift, freshness delay를 end-to-end evaluation case로 확장한다.

## 비목표

- 전체 lakehouse 구현
- 대규모 분산처리 성능 증명
- production cloud deployment
- 승인 없는 자동 복구
- full data catalog 또는 observability platform
- 범용 자동 RCA Agent
- 대출 승인 정책 또는 신용 위험 ML 모델
