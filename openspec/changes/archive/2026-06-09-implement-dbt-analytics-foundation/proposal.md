## Why

raw 택시 데이터와 파티션 인제스션은 준비되었지만, 후속 profile, incident detection, impact analysis가 사용할 분석 레이어와 dbt artifact가 아직 없다. 지금 dbt 기반 staging/mart/test/lineage를 고정해야 이후 evidence와 영향 분석의 입력이 흔들리지 않는다.

## What Changes

- DuckDB raw 테이블을 읽는 dbt 프로젝트 기반을 구성한다.
- `raw.yellow_tripdata`와 `raw.taxi_zones`를 source로 선언한다.
- staging 모델에서 타입, 명명, 파티션 컬럼을 분석 친화적으로 정리한다.
- mart 모델에서 일자/지역 단위 택시 운행 지표를 생성한다.
- 핵심 dbt test를 추가하고 `dbt build`로 검증한다.
- `manifest.json`과 `run_results.json` 생성 경로를 후속 lineage/evidence 단계에서 사용할 수 있게 고정한다.

## Capabilities

### New Capabilities

- `dbt-analytics-foundation`: DuckDB raw 데이터 위에 dbt staging, mart, test, lineage artifact 기반을 제공한다.

### Modified Capabilities

- 없음

## Impact

- `dbt/` 아래 dbt project, profiles, models, tests, macros 구성이 추가된다.
- 로컬 DuckDB 데이터베이스 경로와 dbt profile 설정이 필요하다.
- `dbt build`가 테스트/검증 명령에 추가된다.
- 후속 `add-profile-snapshots`, `add-impact-analysis`는 dbt artifact를 입력으로 사용할 수 있다.
