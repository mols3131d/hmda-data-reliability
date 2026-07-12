# Vision

> Data Reliability Incident 운영 Agent 플랫폼. 알림 넘어선 재현/검증 가능 처리.

## 지향점

단순 성공 여부 확인 아님. 이상 발생 시 판단 흐름을 incident lifecycle 통합.

- 기본 분석 대상은 HMDA 대출 신청 데이터와 승인/거절 결과 mart다.
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
- **MVP-bounded**: 책임 범위 내 기술(Iceberg, Dagster, dbt, LangGraph) 한정.

## 성공 모습

10분 데모. HMDA 원천에서 1개 synthetic incident 발생 -> evidence 수집/RCA/affected assets/test suggestion/evaluation 생성. "데이터 품질 장애의 운영 문제 모델링" 증명.

## 비목표

- 전체 lakehouse 구현
- 대규모 분산처리 성능 증명
- production cloud deployment
- 승인 없는 자동 복구
- full data catalog / observability platform
