## Context

CLI는 `run_pipeline()`을, Dagster assets는 같은 단계 함수를 호출한다. 실행 순서가 runner와 asset graph에 중복되어 있다. 운영 경로는 Dagster로 통일하되 Dagster 비종속 단계 함수는 유지한다.

## Goals / Non-Goals

**Goals:**

- Dagster asset graph만 전체 실행 순서를 소유한다.
- 단계 로직과 결과 모델은 Dagster에 종속되지 않는다.
- CLI 검증과 문서를 Dagster 경계로 옮긴다.

**Non-Goals:**

- asset graph, metadata, 단계 내부 동작은 바꾸지 않는다.
- schedule, sensor, partition, retry policy는 추가하지 않는다.
- Dagster CLI는 유지한다.

## Decisions

### Dagster 단일 조율

Dagster asset graph만 전체 순서를 정의하고 `pipeline_job`은 named 실행 경로를 제공한다. Dagster의 implicit asset job도 같은 graph를 사용한다. `run_pipeline()` 병행은 계약 중복 때문에 제외한다.

### 단계 함수는 유지한다

`load_raw_data()`, `run_dbt_build()`, `run_incident_lifecycle()`과 결과 모델을 유지한다. 로직을 asset에 옮기면 결합도만 높아진다.

### CLI 계약 제거

`PipelineRunResult`, `pipeline.cli`, 실행 스크립트를 함께 제거한다. 호환 shim은 두지 않는다.

### Dagster 경계 검증

단계 순서·성공·backfill은 Dagster materialization에서 검증한다. 단계 내부 검증은 기존 도메인 테스트가 맡는다.

### 스펙 책임 분리

`mvp-pipeline-runtime`은 폐기한다. 단계 계약은 `pipeline-stage-runtime`, 전체 조율 계약은 `standard-dagster-orchestration`이 소유한다. OpenSpec delta는 capability 폴더를 삭제하지 않으므로 기존 main spec 삭제를 구현 작업에 포함한다.

## Risks / Trade-offs

- [수동 전체 실행 제거] README에 Dagster UI/CLI 실행법을 제공한다.
- [기존 import 파손] 저장소 참조를 제거하고 breaking change로 명시한다.
- [통합 신호 손실] 기존 시나리오를 Dagster materialization으로 옮긴다.
- [archive가 폐기 스펙을 남김] main spec을 구현 중 삭제하고 해당 capability delta는 만들지 않는다.

## Migration Plan

1. 기존 통합 시나리오를 Dagster 테스트로 옮긴다.
2. runner/result/CLI/스크립트를 제거한다.
3. `mvp-pipeline-runtime` main spec을 삭제한다.
4. export, 참조, README를 정리하고 검증한다.

롤백은 삭제 파일과 export 복원만 필요하다. 데이터 변경은 없다.

## Open Questions

없음.
