# Vision

> HMDA 데이터 품질 이상을 근거 기반으로 재현하고 검증하는 Data Reliability Incident 운영 기반.

## 지향점

단순 성공 여부 확인 아님. 이상 발생 시 판단 흐름을 incident lifecycle 통합.

- 기본 분석 대상은 HMDA 공개 LAR 대출 신청 데이터와 연도·주·대출 목적별 결과 mart다.
- 이상 탐지 -> severity/owner 포함 incident 승격.
- profile/metadata/lineage/catalog -> RCA evidence 활용.
- downstream 영향 범위/재처리 대상 명확 산출.
- dbt test remediation 제안 + compile 검증.
- 위험 작업 -> human approval 후 Dagster 실행.
- synthetic incident + evaluation report -> Agent 판단 품질 평가.

## 핵심 원칙

- **Evidence-first**: Agent 응답에 근거(metadata/artifact) 필수.
- **Workflow-first**: 탐지-RCA-영향-remediation-재처리-평가 연결 우선.
- **Human-controlled**: 자동 복구 없음. Agent 제안 + 승인 필수.
- **Locally reproducible**: 로컬 전체 workflow 반복 실행 보장.
- **Scope-bounded**: 현재 구현은 로컬 DuckDB, dbt, Dagster, reliability contract에 한정.

## 성공 모습

HMDA 원천 적재부터 dbt 분석, volume drop 탐지, 영향 분석, remediation 초안, 승인 기반 재처리, 평가 보고서까지 한 흐름으로 재현한다.

## 비목표

- 전체 lakehouse 구현
- 대규모 분산처리 성능 증명
- production cloud deployment
- 승인 없는 자동 복구
- full data catalog / observability platform
- 대출 승인 정책 또는 신용 위험 ML 모델
