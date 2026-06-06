# define-reliability-contracts

## 목적

Data Reliability Incident workflow의 핵심 입출력 contract를 먼저 고정한다. Detector, LangGraph Agent, dbt lineage, backfill approval, evaluation이 같은 구조를 공유해야 후속 구현의 경계가 흔들리지 않는다.

## 배경

현재 아키텍처는 profile evidence를 incident로 승격하고, lineage로 영향 범위를 계산한 뒤, human approval 이후에만 backfill과 validation을 실행하는 흐름을 전제한다. 하지만 `Incident`, `Evidence`, `ProfileSnapshot`, `LineageEvidence`, `Approval`의 필드와 상태 값이 아직 명확하지 않다.

## 변경 내용

- Pydantic 기반 reliability contract 모델을 정의한다.
- incident lifecycle에 필요한 enum 값을 고정한다.
- evidence 참조 규칙을 정한다.
- profile, lineage, approval 구조를 detector와 agent가 재사용할 수 있게 분리한다.
- JSON 직렬화와 validation 기준을 테스트로 고정한다.

## 비목표

- Detector 로직 구현
- LangGraph RCA workflow 구현
- dbt model 또는 Dagster asset 구현
- backfill 실행 구현
- dashboard UI 구현

## 성공 기준

- 후속 작업이 같은 contract를 import해서 사용할 수 있다.
- 승인되지 않은 incident는 backfill 또는 validation 실행 대상으로 표현되지 않는다.
- contract validation 실패가 명확한 application error로 드러난다.
- synthetic incident fixture를 만들 수 있는 최소 필드가 준비된다.
