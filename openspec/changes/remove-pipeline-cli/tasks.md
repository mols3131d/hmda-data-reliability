## 1. Dagster 통합 검증 전환

- [x] 1.1 `run_pipeline()`의 단계 실행·backfill 시나리오를 Dagster materialization 테스트로 옮긴다.
- [x] 1.2 asset 순서와 Dagster 단일 조율 경계를 검증한다.

## 2. 중복 실행 경로 제거

- [x] 2.1 `_runner.py`에서 `run_pipeline()`과 미사용 import를 제거한다.
- [x] 2.2 `PipelineRunResult`, CLI, 실행 스크립트와 전용 테스트를 제거한다.
- [x] 2.3 공개 export와 남은 참조를 정리한다.

## 3. 스펙 책임 정리

- [x] 3.1 main spec에서 `mvp-pipeline-runtime`을 삭제한다.
- [x] 3.2 단계 계약은 `pipeline-stage-runtime`, 조율 계약은 `standard-dagster-orchestration`에만 남았는지 확인한다.

## 4. 문서 및 검증

- [x] 4.1 README의 독립 CLI 안내를 Dagster 실행 안내로 바꾼다.
- [x] 4.2 테스트·정적 검사를 실행하고 제거된 API 참조가 없는지 확인한다.
