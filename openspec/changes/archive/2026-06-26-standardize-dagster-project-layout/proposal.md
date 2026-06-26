## Why

현재 Dagster 정의는 orchestration 하위 중첩 패키지에 있고 `defs/` 디렉터리는 비어 있다. `dg scaffold defs`가 기대하는 표준 위치와 달라서 이후 asset, schedule, sensor, component를 추가할 때 구조가 혼란스러워진다.

## What Changes

- Dagster project root를 `project_pivot.orchestration`으로 정리한다.
- Dagster 정의 파일을 `src/project_pivot/orchestration/defs/` 아래로 이동한다.
- `definitions.py`는 `defs/`의 asset/resource를 모아 Dagster에 노출하는 entrypoint로 유지한다.
- `pyproject.toml`의 `tool.dg.project.root_module`을 새 root module에 맞춘다.
- 기존 asset key, group, metadata, `mvp_pipeline_job` 이름은 유지한다.
- 기존 Dagster 중첩 패키지는 제거하고 호환 shim은 두지 않는다.

## Capabilities

### New Capabilities

- `dagster-project-layout`: Dagster project root와 `defs/` 기반 definition layout을 표준화한다.

### Modified Capabilities

- 없음

## Impact

- `src/project_pivot/orchestration/` 패키지 구조 변경
- `pyproject.toml`의 `tool.dg.project.root_module` 변경
- Dagster import 경로와 orchestration 테스트 수정
- 개발 실행 명령 변경: 새 entrypoint `project_pivot.orchestration.definitions` 사용
