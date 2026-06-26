## 1. 패키지 구조 이동

- [x] 1.1 `src/project_pivot/orchestration/defs/` 패키지 생성
- [x] 1.2 기존 Dagster asset 정의를 `orchestration/defs/assets.py`로 이동
- [x] 1.3 기존 Dagster resource 정의를 `orchestration/defs/resource.py`로 이동
- [x] 1.4 `orchestration/definitions.py`를 새 entrypoint로 생성
- [x] 1.5 기존 Dagster 중첩 패키지 제거

## 2. Import 및 설정 갱신

- [x] 2.1 내부 import를 `project_pivot.orchestration.defs.*` 경로로 갱신
- [x] 2.2 테스트 import를 새 Dagster entrypoint와 defs 경로로 갱신
- [x] 2.3 `pyproject.toml`의 `tool.dg.project.root_module`을 `project_pivot.orchestration`으로 변경
- [x] 2.4 `docs`, `scratch/docs`, active OpenSpec change의 이전 Dagster 실행 명령을 새 경로로 갱신

## 3. 검증

- [x] 3.1 `src`, `tests`, `docs`, `scratch/docs`, active OpenSpec change에서 오래된 Dagster 중첩 경로 잔존 여부 확인
- [x] 3.2 `dg list defs --json`으로 새 root module 로딩 확인
- [x] 3.3 `pytest tests/orchestration tests/pipeline` 실행
- [x] 3.4 `mypy src tests` 실행
- [x] 3.5 `dagster dev -m project_pivot.orchestration.definitions` smoke test
- [x] 3.6 `dg launch --job mvp_pipeline_job` materialization 확인
