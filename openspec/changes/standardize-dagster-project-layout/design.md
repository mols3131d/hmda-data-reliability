## Context

현재 Dagster project root는 `project_pivot.orchestration.dagster`로 설정되어 있다. 이 구조는 Dagster가 여러 orchestration backend 중 하나인 것처럼 보이지만, 프로젝트 방향은 Dagster를 단일 orchestration layer로 사용하는 것이다.

`dg scaffold defs`는 project root 아래 `defs/`를 기준으로 definition 파일을 생성한다. 따라서 `project_pivot.orchestration`을 root module로 두고 `orchestration/defs/`에 asset/resource를 배치하는 편이 더 일관적이다.

## Goals / Non-Goals

**Goals:**

- `project_pivot.orchestration`을 Dagster project root로 사용한다.
- Dagster definition 코드를 `src/project_pivot/orchestration/defs/` 아래로 이동한다.
- `definitions.py`는 `defs/`의 정의를 모아 `defs = Definitions(...)`를 노출한다.
- 기존 asset key, group, dependency, metadata, job 이름을 유지한다.
- `dg list defs`, `dg launch --job mvp_pipeline_job`, `dagster dev -m project_pivot.orchestration.definitions`가 새 경로에서 동작한다.

**Non-Goals:**

- pipeline/reliability 도메인 로직 변경.
- Dagster asset semantics 변경.
- asset check, schedule, sensor 추가.
- 기존 완료 change archive.
- 이전 `project_pivot.orchestration.dagster.*` import 경로 호환 유지.

## Decisions

### 1. `orchestration`을 Dagster project root로 둔다

현재:

```text
project_pivot/orchestration/dagster/definitions.py
project_pivot/orchestration/dagster/assets.py
project_pivot/orchestration/dagster/resource.py
```

변경 후:

```text
project_pivot/orchestration/definitions.py
project_pivot/orchestration/defs/assets.py
project_pivot/orchestration/defs/resource.py
```

이 구조는 `tool.dg.project.root_module = "project_pivot.orchestration"`와 맞는다.

### 2. `definitions.py`는 entrypoint로만 유지한다

`definitions.py`는 asset/resource/job을 직접 구현하지 않고 `defs/`에서 import해 `Definitions`를 구성한다. 이렇게 하면 Dagster entrypoint와 definition 구현 위치가 분리된다.

### 3. 이전 `orchestration/dagster` 패키지는 제거한다

신규 코드와 테스트는 새 import 경로만 사용한다. 오래된 import 경로를 유지하면 구조 혼란이 계속되므로 호환 shim은 만들지 않는다.

### 4. 실행 명령을 새 경로로 바꾼다

새 표준 실행 명령:

```bash
env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=src uv run dagster dev -m project_pivot.orchestration.definitions
```

`dg` CLI는 `tool.dg.project.root_module` 기준으로 definitions를 찾는다.

## Risks / Trade-offs

- **[Risk]** 구현 대상 파일이나 active docs가 `project_pivot.orchestration.dagster.*` 경로를 참조할 수 있다.
  - **Mitigation**: `src`, `tests`, `docs`, `scratch/docs`, active OpenSpec change에서 경로 참조를 찾아 새 경로로 갱신한다.
- **[Risk]** 빈 `dagster/defs` 폴더가 남으면 혼란을 만든다.
  - **Mitigation**: `orchestration/dagster` 패키지를 제거하고 새 구조만 남긴다.
- **[Risk]** import 이동 중 Dagster definitions 로딩이 깨질 수 있다.
  - **Mitigation**: `dg list defs`, `pytest tests/orchestration`, `dg launch --job mvp_pipeline_job`로 검증한다.

## Migration Plan

1. `orchestration/defs/` 패키지를 만든다.
2. 기존 `dagster/assets.py`, `dagster/resource.py`, `dagster/definitions.py`를 새 위치로 이동한다.
3. 내부 import와 테스트 import를 새 경로로 갱신한다.
4. active docs의 실행 명령과 import 경로를 새 경로로 갱신한다.
5. `pyproject.toml`의 root module을 `project_pivot.orchestration`으로 바꾼다.
6. 이전 `orchestration/dagster` 패키지와 빈 `defs/`를 제거한다.
7. `dg list defs`, pytest, mypy, Dagster smoke test를 실행한다.

## Open Questions

- 없음
