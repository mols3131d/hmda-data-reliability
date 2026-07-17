## Why

Python runner와 Dagster가 같은 실행 순서를 중복 관리한다. Dagster만 조율하고 Python은 단계 로직만 제공하도록 단순화한다.

## What Changes

- **BREAKING** 독립 CLI, `run_pipeline()`, `PipelineRunResult`를 제거한다.
- 단계 함수와 결과 계약은 유지한다.
- 실행 순서와 의존성은 Dagster asset graph만 소유한다.
- CLI/runner 통합 테스트를 Dagster materialization 테스트로 대체한다.
- `mvp-pipeline-runtime` 스펙을 폐기하고 단계 계약을 분리한다.
- README는 Dagster 실행만 안내한다.

## Capabilities

### New Capabilities

- `pipeline-stage-runtime`: Dagster 비종속 단계 함수와 결과 계약을 정의한다.

### Modified Capabilities

- `standard-dagster-orchestration`: Dagster를 유일한 전체 pipeline 조율 경로로 지정한다.

## Impact

- 삭제: CLI, 전체 runner/result, 전용 스크립트와 테스트.
- 폐기: `mvp-pipeline-runtime` main spec.
- 유지: Dagster 정의, `DataOperationRequest`, 단계 함수와 결과 모델.
- 전체 실행은 Dagster UI/CLI의 `pipeline_job`으로 이동한다.
