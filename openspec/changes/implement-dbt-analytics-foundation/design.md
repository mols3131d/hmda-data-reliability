## Context

현재 `taxi_data` 인제스션은 DuckDB의 `raw.yellow_tripdata`, `raw.taxi_zones`를 만들고 파티션 오버라이트 멱등성을 보장한다. 다음 단계의 profile/evidence/detection은 raw 테이블을 직접 읽기보다 안정된 분석 모델과 dbt artifact를 입력으로 삼아야 한다.

dbt 의존성은 이미 프로젝트에 포함되어 있으나 `dbt/` 구성과 모델은 아직 비어 있다. 이번 변경은 Dagster 도입 전, 함수/CLI로 실행 가능한 dbt 분석 파운데이션을 먼저 고정한다.

## Goals / Non-Goals

**Goals:**

- DuckDB raw 테이블을 source로 선언하는 dbt 프로젝트를 구성한다.
- `stg_yellow_tripdata`, `stg_taxi_zones` 모델에서 분석용 컬럼 계약을 고정한다.
- `mart_daily_taxi_trips` 모델에서 `pickup_date`, `pickup_location_id` grain의 핵심 지표를 만든다.
- dbt test와 artifact 생성(`manifest.json`, `run_results.json`)을 검증한다.
- 후속 lineage/profile/Dagster 단계가 참조할 모델명, partition 컬럼, artifact 경로를 예측 가능하게 둔다.

**Non-Goals:**

- Dagster asset/op 정의
- DataHub 같은 외부 카탈로그 연동
- 복잡한 incremental 전략 또는 대규모 warehouse 최적화
- 자동 remediation, backfill, approval workflow
- dbt 실행용 Python runner 또는 자체 orchestration 추상화

## Decisions

### dbt 프로젝트는 `dbt/` 하위에 둔다

`dbt_project.yml`, `profiles.yml`, `models/`를 repo의 `dbt/` 아래에 둔다. Python 패키지 내부에 넣지 않는다.

이유: dbt는 독립 CLI 도구이고, 모델/테스트/artifact는 애플리케이션 모듈보다 분석 프로젝트에 가깝다. `src/project_pivot`에 넣으면 Python import 경계와 dbt resource 경계가 섞인다.

대안: `src/project_pivot/dbt`에 포함. 배포 패키지와 dbt 작업 경계가 섞여 제외한다.

### raw source는 dbt source로만 참조한다

staging 모델은 `source('raw', 'yellow_tripdata')`, `source('raw', 'taxi_zones')`를 통해 raw 테이블을 읽는다. raw 테이블 생성은 기존 인제스션 책임으로 남긴다.

이유: dbt가 원천 적재까지 소유하면 partition ingestion과 책임이 겹친다. dbt는 분석 변환, 테스트, lineage artifact 생성에 집중한다.

대안: seed/external table로 raw를 dbt에서 직접 생성. 기존 멱등 인제스션 경계와 충돌하므로 제외한다.

### staging과 mart를 최소 2계층으로 둔다

staging은 타입/컬럼명/기본 파생 컬럼 정리만 수행한다. mart는 `pickup_date`, `pickup_location_id` grain의 집계를 담당한다.

이유: 후속 profile과 incident 탐지는 raw 품질 문제와 mart 영향 범위를 구분해야 한다. 계층이 없으면 lineage가 너무 짧아지고 impact analysis 데모 가치가 낮다.

대안: mart 하나로 바로 집계. 빠르지만 lineage와 테스트 위치가 빈약해 제외한다.

### 모델명은 Dagster asset key와 맞게 고정한다

dbt 모델명은 `stg_yellow_tripdata`, `stg_taxi_zones`, `mart_daily_taxi_trips`로 고정한다. mart는 `pickup_date`를 daily partition key 후보로 유지한다.

이유: Dagster 도입 후 dbt 모델을 asset으로 감쌀 때 모델명과 partition 컬럼이 흔들리면 asset key, backfill 범위, profile 대상이 함께 흔들린다. 지금은 Dagster 코드를 만들지 않되, 나중에 그대로 감쌀 수 있는 경계를 만든다.

대안: dbt 구현 이후 Dagster 도입 시 모델명을 재조정. lineage artifact와 테스트 이름이 바뀌어 비용이 커지므로 제외한다.

### artifact는 dbt 기본 `target/`을 사용한다

`manifest.json`, `run_results.json`은 dbt project의 `dbt/target/`에 생성한다. 후속 단계에서는 이 경로를 설정값으로 받을 수 있게 한다.

이유: dbt 표준 경로를 따르면 별도 복사 로직이 필요 없다.

대안: `data/artifacts/dbt/`로 복사. 추후 필요하면 추가하되 이번 기반 단계에서는 제외한다.

### foundation 단계는 table/view materialization만 사용한다

이번 단계에서는 append-only incremental 모델을 만들지 않는다. 동일 raw 입력에 대해 `dbt build`를 반복해도 같은 결과가 나오도록 table 또는 view materialization을 사용한다.

이유: 현재 raw 인제스션이 partition overwrite로 멱등성을 보장한다. dbt가 append 누적을 시작하면 downstream profile과 incident 판단이 중복 행에 오염된다.

대안: 처음부터 incremental + partition filter를 구현. Dagster partition/backfill 설계와 함께 잡는 편이 안전하므로 제외한다.

## Risks / Trade-offs

- [Risk] raw 테이블이 없으면 `dbt build`가 실패한다. -> 인제스션 실행을 선행 조건으로 문서화하고 테스트 fixture에서는 DuckDB raw 테이블을 준비한다.
- [Risk] DuckDB 파일 경로가 환경마다 다르다. -> `profiles.yml`은 환경 변수 기반 경로를 우선 사용하고 기본값은 로컬 개발 경로로 둔다.
- [Risk] 모델 grain이 나중에 바뀔 수 있다. -> mart는 최소 일자/지역 grain으로 시작하고, 비즈니스 지표 확장은 후속 change로 분리한다.
- [Risk] dbt test가 너무 강하면 합성 이상치 케이스에서 build 자체가 막힌다. -> foundation 단계의 test는 source/staging/mart 구조 안정성 중심으로 둔다.
- [Risk] Dagster 도입 시 asset 경계가 다시 바뀔 수 있다. -> 모델명, daily grain, artifact 경로를 이번 스펙에서 고정하고 orchestration 구현은 미룬다.
