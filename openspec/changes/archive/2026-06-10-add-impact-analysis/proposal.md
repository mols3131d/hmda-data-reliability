## Why

incident는 생성되지만 downstream 영향 범위가 비어 있어 어떤 mart/report가 오염됐는지 판단할 수 없다. MVP는 dbt lineage artifact를 근거로 affected assets를 계산해야 한다.

## What Changes

- dbt `manifest.json`을 읽는 lineage graph parser를 추가한다.
- incident asset에서 downstream dbt nodes를 transitive로 탐색한다.
- 탐색 결과를 `LineageEvidence`로 반환하고 incident의 `affected_assets`에 반영한다.
- `run_results.json` 경로를 evidence에 보존해 후속 검증 단계가 참조할 수 있게 한다.

## Capabilities

### New Capabilities

- `impact-analysis`: dbt lineage artifact로 downstream 영향을 계산하고 incident에 affected assets를 연결한다.

### Modified Capabilities

- 없음

## Impact

- `src/project_pivot/reliability/impact/` 모듈이 추가된다.
- `tests/reliability/test_impact_analysis.py`가 추가된다.
- 새 dependency는 없다.
