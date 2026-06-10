## Why

foundation은 raw/dbt/contract를 준비했지만 detector가 비교할 수치형 품질 입력은 아직 없다. MVP incident lifecycle을 시작하려면 partition별 row count, null rate, schema hash, freshness를 `ProfileSnapshot` contract로 생성해야 한다.

## What Changes

- DuckDB 테이블과 파티션 조건을 입력받아 profile snapshot을 계산하는 모듈을 추가한다.
- row count, 컬럼별 null rate, 안정적인 schema hash, freshness timestamp를 계산한다.
- 계산 결과를 기존 `ProfileSnapshot` Pydantic contract로 반환하고 JSON 직렬화 가능성을 검증한다.
- 후속 detector가 사용할 수 있도록 metric payload를 결정적으로 구성한다.

## Capabilities

### New Capabilities

- `profile-snapshots`: DuckDB asset partition의 품질 지표를 계산해 `ProfileSnapshot` contract로 제공한다.

### Modified Capabilities

- 없음

## Impact

- `src/project_pivot/reliability/` 아래 profiling 모듈이 추가된다.
- `tests/reliability/` 아래 profile snapshot 계산 테스트가 추가된다.
- 새 runtime dependency는 추가하지 않는다.
