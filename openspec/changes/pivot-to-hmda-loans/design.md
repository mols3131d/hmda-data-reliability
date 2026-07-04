## Context

현재 프로젝트는 TLC/NYC Taxi 데이터를 `data/raw/tlc`에서 DuckDB raw 레이어로 적재하고, dbt staging/mart와 Dagster asset을 통해 로컬 MVP 파이프라인을 실행한다. 기본 분석 방향을 택시 운영 분석이 아니라 HMDA 대출 데이터 기반의 대출 승인/리스크 의사결정 데이터 제품으로 전환하려고 한다.

기존 reliability, pipeline, dbt, Dagster 구조는 유지 가치가 있다. 바뀌어야 하는 것은 기본 도메인, 원천 데이터 경로, raw/staging/mart 계약, asset 명칭과 metadata다.

## Goals / Non-Goals

**Goals:**

- 기본 원천 데이터 경로를 `data/raw/hmda`로 전환한다.
- `taxi_data` 중심 모듈을 HMDA/loan 중심 모듈로 대체할 구현 계획을 고정한다.
- DuckDB raw, dbt staging/mart, Dagster asset, CLI, 테스트, 문서의 도메인 용어를 일관되게 바꾼다.
- TLC 의존 코드를 기본 경로에서 제거해 새 데이터 제품 방향이 혼재되지 않게 한다.

**Non-Goals:**

- HMDA 원천 데이터를 다운로드하는 네트워크 클라이언트는 포함하지 않는다.
- 신용 점수 모델, 승인 정책 최적화, SHAP 등 ML 모델링은 이번 전환 범위에 포함하지 않는다.
- 기존 reliability contract 자체를 재설계하지 않는다. 필요한 입력 asset 명칭과 evidence metadata만 새 도메인에 맞춘다.

## Decisions

### HMDA를 새 도메인 모듈로 분리한다

`src/project_pivot/taxi_data`를 그대로 일반화하기보다 `hmda_data` 또는 `loan_data` 중심 모듈로 전환한다. 구현 시 공개 API와 테스트 명칭은 HMDA 원천의 의미가 드러나게 정리한다.

대안으로 `raw_data` 같은 중립 모듈을 둘 수 있지만, 프로젝트 방향이 대출 데이터에 맞춰져 있으므로 도메인 이름을 숨기지 않는 편이 낫다.

### raw 레이어는 HMDA 신청 레코드를 중심으로 둔다

DuckDB raw 스키마에는 HMDA loan/application 레코드 원본을 보존하는 테이블을 둔다. 구현은 CSV 또는 Parquet를 모두 허용하되, 스키마 감지는 DuckDB의 구조 감지 기능을 사용하고 `source_file`, `source_year`, `ingested_at` 같은 추적 컬럼을 붙인다.

대안으로 처음부터 정규화된 여러 raw 테이블을 만들 수 있지만, 초기 전환 단계에서는 원천 보존과 재현성이 우선이다.

### 파티션 키는 연도/파일 단위로 잡는다

택시 데이터의 `pickup_date` 일자 파티션은 HMDA에 맞지 않는다. HMDA는 공개 데이터의 연도 단위 배포와 파일 단위 재처리가 자연스러우므로 `source_year`와 `source_file` 기준 멱등 적재를 요구한다.

대안으로 신청일 기반 파티션을 둘 수 있지만, HMDA public LAR에는 운영 이벤트 일자보다 제출 연도와 파일 버전 관리가 더 안정적인 재처리 기준이다.

### dbt mart는 리스크 모델이 아니라 의사결정 분석 기반을 만든다

이번 변경의 dbt mart는 모델 예측 결과가 아니라 승인율, 거절율, 대출 목적, 소득 구간, 지역/인구통계 분석에 필요한 집계 기반을 제공한다. ML은 이후 capability로 분리한다.

### Dagster asset은 noun-based HMDA asset key를 사용한다

Dagster asset은 `raw_taxi_data` 같은 기존 이름을 `raw_hmda_loans`, `dbt_loan_analytics`, `mvp_incident_lifecycle` 같은 산출물 중심 이름으로 바꾼다. asset 함수는 기존처럼 도메인 로직을 중복하지 않고 pipeline/reliability 실행 함수를 감싼다.

## Risks / Trade-offs

- HMDA 컬럼은 연도별로 일부 차이가 날 수 있다. → raw 적재는 원천 컬럼을 보존하고, staging에서 필수 컬럼 계약과 누락 처리 정책을 명시한다.
- 기존 taxi 테스트와 문서를 한 번에 제거하면 변경 폭이 크다. → OpenSpec task를 식별, 대체, 삭제 순서로 나누고 각 단계마다 테스트를 유지한다.
- `taxi-data-foundation` 기존 스펙이 archive에 남아 혼란을 줄 수 있다. → 새 capability를 추가하고 downstream capability를 HMDA 기준으로 수정해 active 요구사항의 기준을 분명히 한다.
- HMDA 도메인 해석이 과장될 수 있다. → 이번 범위는 데이터 파운데이션과 분석 mart까지로 제한하고, 승인/리스크 모델링은 후속 변경으로 둔다.

## Migration Plan

1. `data/raw/hmda` 샘플 파일 구조와 필수 컬럼을 확인한다.
2. HMDA raw 적재 모듈과 테스트를 만들고 taxi raw 적재 경로를 기본 실행 경로에서 제거한다.
3. dbt source/staging/mart를 HMDA 모델로 교체한다.
4. pipeline CLI와 Dagster asset key/metadata를 HMDA 명칭으로 바꾼다.
5. README, architecture, vision 문서를 HMDA 대출 데이터 제품 방향으로 갱신한다.
6. 전체 테스트와 dbt/Dagster 정의 검증을 실행한다.

Rollback은 `main`의 TLC 기반 구현으로 돌아가는 방식으로 처리한다. 이 변경은 breaking pivot이므로 동일 브랜치에서 양 도메인을 동시에 지원하는 롤백 경로를 만들지 않는다.

## Open Questions

- `data/raw/hmda`에 들어올 첫 파일 형식은 CSV인지 Parquet인지 확인이 필요하다.
- HMDA mart의 첫 grain은 `activity_year + state + loan_purpose`로 충분한지, 아니면 county/tract 수준까지 내려갈지 결정해야 한다.
- 모듈명은 `hmda_data`와 `loan_data` 중 어느 쪽을 최종 표준으로 삼을지 구현 전 확정해야 한다.
