## Why

`run_incident_lifecycle()`이 실제 current profile 탐지, 합성 장애 평가, 자체 승인 backfill을 동시에 수행해 운영과 로컬 MVP 평가 경계가 섞인다. 실제 baseline/current 비교와 human approval을 분리한다.

## What Changes

- **BREAKING** `run_incident_lifecycle()`이 호출자가 제공한 baseline `ProfileSnapshot`과 DB에서 측정한 실제 current snapshot을 비교하도록 변경한다.
- 합성 current, 자체 승인, backfill 실행, evaluation report 생성을 lifecycle 단계에서 제거한다.
- 모든 detection에 대해 impact analysis와 remediation draft를 생성하고 요약 결과를 반환한다.
- **BREAKING** lifecycle 결과에서 evaluation과 recovery 전용 필드를 제거한다.
- **BREAKING** `DataOperationRequest`와 Dagster resource에서 합성 평가·복구 설정을 제거한다.
- baseline 공급 경로 정의 전까지 Dagster graph에서 `incident_lifecycle` asset을 제거한다.
- 기존 approval/backfill과 evaluation capability는 독립 reliability API로 유지한다.

## Capabilities

### New Capabilities

- `incident-lifecycle-runtime`: caller-supplied baseline과 실제 current profile을 이용한 탐지·영향 분석·remediation 계약.

### Modified Capabilities

- `standard-dagster-orchestration`: 표준 pipeline graph를 Bronze와 Silver/Gold asset으로 축소. Control lifecycle asset 요구사항 제거.
- `dagster-project-layout`: definitions와 job의 필수 asset·순서를 두 data-plane asset에 맞춤.

## Impact

- 공개 Python API: `run_incident_lifecycle()` 시그니처와 `LifecycleResult`가 호환성 없이 변경된다.
- 설정: `simulate_row_count_ratio`, `run_backfill`, `report_path`가 data operation request/resource에서 제거된다.
- Dagster: `incident_lifecycle` asset과 관련 materialization metadata가 제거된다.
- 문서·테스트: pipeline graph, lifecycle 입·출력, 합성 평가 위치 갱신.
- 데이터 migration이나 새 dependency는 없다.
