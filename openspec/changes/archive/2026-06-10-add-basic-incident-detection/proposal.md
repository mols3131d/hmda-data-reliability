## Why

profile snapshot은 계산되지만 아직 품질 이상을 incident lifecycle로 승격하는 단계가 없다. MVP가 탐지부터 evidence까지 이어지려면 baseline/current profile 비교로 기본 인시던트를 생성해야 한다.

## What Changes

- `ProfileSnapshot` baseline과 current를 비교하는 rule-based detector를 추가한다.
- row count drop, null spike, schema drift, freshness delay 4가지 기본 이상을 탐지한다.
- 이상 감지 시 `Evidence`와 `Incident`를 함께 생성하고 `evidence_refs`를 연결한다.
- threshold 설정은 작은 Pydantic request/config 모델로 고정한다.
- 머신러닝 탐지, 영구 저장소, remediation/approval 실행은 제외한다.

## Capabilities

### New Capabilities

- `basic-incident-detection`: profile snapshot 비교 결과를 `Incident`와 `Evidence` contract로 승격한다.

### Modified Capabilities

- 없음

## Impact

- `src/project_pivot/reliability/` 아래 detection 모듈이 추가된다.
- `tests/reliability/` 아래 기본 탐지 테스트가 추가된다.
- 새 runtime dependency는 추가하지 않는다.
