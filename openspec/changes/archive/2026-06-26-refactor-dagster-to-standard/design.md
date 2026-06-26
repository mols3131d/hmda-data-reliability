## Context

프로젝트 운영 목표는 Dagster GUI에서 데이터 파이프라인을 실행하고 상태를 확인하는 것이다. 현재 asset은 `raw_taxi_data`, `dbt_analytics`, `mvp_incident_lifecycle`로 나뉘어 있지만, Dagster UI에 표시되는 레이어, 실행 결과, 품질 metadata가 제한적이다.

이 변경은 Dagster를 비즈니스 로직 구현 장소로 만들지 않는다. Dagster는 orchestration과 관측 표면을 담당하고, 적재/변환/탐지/복구 로직은 기존 모듈에 둔다.

## Goals / Non-Goals

**Goals:**

- `dagster dev -m project_pivot.orchestration.dagster.definitions` 로컬 UI 기동 보장.
- Bronze, Silver/Gold, Control asset 경계를 Dagster UI에서 명확히 표시.
- asset materialization 결과에 row count, dbt artifact, incident type, report path 같은 metadata 노출.
- Dagster 설정 구조를 단순화하고 테스트 가능하게 유지.

**Non-Goals:**

- `src/project_pivot/pipeline/runner.py` 내부 핵심 도메인 로직 변경.
- dbt 모델 구조 변경.
- 전용 incident 승인 UI 구현.
- profile snapshot 영속 저장소 구현.

## Decisions

### 1. Dagster는 orchestration 표면으로 둔다

- **이유**: DuckDB 적재, dbt 실행, incident lifecycle은 이미 독립 함수로 테스트된다.
- **결정**: Asset 함수는 기존 runner 함수를 호출하고, Dagster 의존성/metadata/logging을 책임진다.

```text
Dagster asset
  -> pipeline/reliability 함수 호출
  -> MaterializeResult metadata 반환
  -> Dagster UI에 상태 표시
```

### 2. Asset group은 메달리온 경계에 맞춘다

| Asset | Group | 책임 |
|---|---|---|
| `raw_taxi_data` | `bronze` | raw DuckDB table 적재 |
| `dbt_analytics` | `silver_gold` | dbt staging/mart build |
| `mvp_incident_lifecycle` | `control` | evidence, detection, remediation, evaluation |

### 3. MaterializeResult로 observability를 높인다

- `raw_taxi_data`: source file count, taxi zone row count, yellow tripdata row count
- `dbt_analytics`: dbt return code, manifest path, run results path, skipped 여부
- `mvp_incident_lifecycle`: detected incident types, affected assets, report path, success rate

### 4. Config/resource는 과도하게 감싸지 않는다

- 단일 실행 요청을 만들기 위한 설정은 필요하다.
- 설정 객체는 `MvpPipelineRunRequest`로 변환 가능한 형태를 유지한다.
- resource를 유지하더라도 domain logic을 넣지 않는다.

### 5. `dagster-webserver` 의존성은 명시적으로 유지한다

- **이유**: 로컬 Dagster UI 구동은 MVP 운영 경험의 핵심이다.
- 현재 `pyproject.toml`에 의존성이 있으면 유지하고, 누락 시 추가한다.

## Risks / Trade-offs

- **[Risk]** Asset metadata 추가 중 테스트가 기존 `dict` 반환에 의존할 수 있다.
  - **Mitigation**: orchestration 테스트를 asset key/job 등록뿐 아니라 metadata contract 중심으로 갱신한다.
- **[Risk]** Dagster asset 내부로 로직이 과도하게 이동할 수 있다.
  - **Mitigation**: runner/reliability 함수 호출 경계를 유지한다.
- **[Risk]** `dagster dev`는 장기 실행 프로세스라 자동 테스트와 맞지 않는다.
  - **Mitigation**: `pytest tests/orchestration`과 import/definitions 검증을 기본으로 두고, 로컬 기동은 수동 smoke test로 기록한다.
