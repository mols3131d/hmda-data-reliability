# Vision

> 데이터 품질 이상을 단순 알림이 아니라 재현 가능하고 검증 가능한 **Data Reliability Incident**로 다루는 운영형 Agent 플랫폼을 만든다.

## 지향점

이 프로젝트의 목표는 데이터 파이프라인 성공 여부를 확인하는 도구가 아니다. 품질 이상이 발생했을 때 필요한 판단 흐름을 하나의 incident lifecycle로 묶는 것이다.

- 이상 탐지 결과를 severity와 owner가 있는 incident로 승격한다.
- profile, Iceberg metadata, dbt lineage, catalog 정보를 RCA evidence로 사용한다.
- downstream 영향 범위와 재처리 대상 partition을 명확히 산출한다.
- dbt test remediation을 제안하고 compile 가능한 형태로 검증한다.
- 위험 작업은 human approval 이후 Dagster workflow로 실행한다.
- synthetic incident case와 evaluation report로 Agent 판단 품질을 평가한다.

## 핵심 원칙

- **Evidence-first**: Agent 응답은 metadata와 artifact 근거를 포함해야 한다.
- **Workflow-first**: 개별 기능보다 탐지, RCA, 영향 분석, remediation, 재처리, 평가의 연결성을 우선한다.
- **Human-controlled**: Agent는 복구를 제안하지만 승인 없이 데이터를 변경하지 않는다.
- **Locally reproducible**: 로컬에서 전체 workflow를 반복 실행할 수 있어야 한다.
- **MVP-bounded**: Iceberg, Dagster, dbt, LangGraph는 필요한 책임 범위 안에서만 사용한다.

## 성공 모습

10분 데모에서 하나의 synthetic incident가 발생하고, 시스템이 evidence 수집, RCA, affected assets, dbt test suggestion, backfill plan, evaluation report까지 일관되게 생성한다. 면접 관점에서는 “왜 이 기술을 썼는가”보다 “데이터 품질 장애 대응을 어떻게 운영 문제로 모델링했는가”가 분명해야 한다.

## 비목표

- 전체 lakehouse 구현
- 대규모 분산처리 성능 증명
- production cloud deployment
- 승인 없는 자동 복구
- full data catalog 또는 observability platform 구현
