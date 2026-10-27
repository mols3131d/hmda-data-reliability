# Analytics Foundation Test Design

## Contract And Boundary

정본은 [dbt analytics Spec](../../openspec/specs/data-platform-dbt-analytics/spec.md)이다. [테스트](test_analytics_foundation.py)는 실제 CSV ingestion, 임시 DuckDB와 dbt CLI를 연결한다. 각 test의 database, target, log는 `tmp_path` 안에서 격리한다. 운영 runner의 quality gate, artifact pair identity와 promotion은 이 module의 범위 밖이다.

## Scenario Map

| Contract | Scenario | Independent Oracle | Test |
| --- | --- | --- | --- |
| Caller-owned database path | Profile의 경로에 caller 환경 변수를 사용한다. | Default 없는 고정 profile 표현 | `test_dbt_profile_requires_caller_database_path` |
| Source·staging·mart lineage | 실제 build 후 manifest dependency를 조회한다. | 선언된 source/model ID와 직접 edge | `test_dbt_build_creates_artifacts_lineage_and_idempotent_mart` |
| Staging row·type 보존 | nullable 지역과 invalid numeric을 포함한 10행을 build한다. | 10행, Spec의 9개 column type, 두 NULL row의 고정 값 | `test_dbt_build_creates_artifacts_lineage_and_idempotent_mart` |
| Full mart grain | 같은 state/purpose의 다른 year, 같은 year/state의 다른 purpose, 같은 year/purpose의 다른 state를 집계한다. | 손계산한 다섯 grain tuple | `test_dbt_build_creates_artifacts_lineage_and_idempotent_mart` |
| Outcome·rate·average | Action 1·2·4와 complete-key invalid numeric 행을 TX grain에 둔다. | Applications 3, approvals 2, denials 0, rate `0.666667`, averages `150000.0`·`75.0` | `test_dbt_build_creates_artifacts_lineage_and_idempotent_mart` |
| Eligible population | State가 NULL인 행과 complete-key numeric NULL 행을 함께 둔다. | 전자는 mart에서 제외되고 후자는 TX의 application denominator에 포함 | `test_dbt_build_creates_artifacts_lineage_and_idempotent_mart` |
| Deterministic rebuild | 같은 raw에서 두 차례 build한다. | 두 결과 모두 동일한 고정 tuple과 grain/row count | `test_dbt_build_creates_artifacts_lineage_and_idempotent_mart` |
| Quality failure | 성공 build 뒤 source year NULL, mart key NULL·duplicate를 주입해 `dbt test`를 실행한다. | Exit 1과 source/staging `source_year` not-null, mart key not-null/unique의 정확한 네 실패. 나머지 결과는 pass이며 error·예상 밖 status는 거부 | `test_dbt_quality_tests_detect_source_staging_and_mart_violations` |

## Fixed Fixture Arithmetic

TX는 `100000/50`, `200000/100`, `invalid/Exempt`의 세 행이다. Actions `1`, `2`, `4` 중 처음 두 행이 승인되어 `2/3`을 여섯 자리로 반올림하면 `0.666667`이다. 마지막 행은 평균에서 제외되지만 application count에는 포함된다. 이 결과는 action 2 누락, 반올림 제거·절삭, NULL의 zero 대체와 invalid numeric 행 제거를 구별한다. CA·NY의 기존 action `3`, `7`은 denial 의미를, action `4`는 미승인·미거절 application을 고정한다.

DB에서 읽은 metric은 값 변환 없이 고정 tuple과 비교한다. Count를 `int()`로 보정해 fractional 오집계를 숨기지 않는다.

Negative quality scenario의 의도된 fail은 네 개다. `dbt test` exit 1과 이 네 fail이 함께 있어도 추가 error를 허용하지 않는다. 실제 반례로 test 직전 mart의 `application_count` column을 제거하면 네 fail 외 실행 error가 생기며, 이 경우 oracle이 추가 status를 이유로 거부해야 한다.

## Limits

- 모든 metric 입력 공간이나 운영 규모 성능을 증명하지 않는다.
- All-null numeric grain, nullable activity year/purpose의 mart-only projection, 모든 필수 column별 quality mutation을 열거하지 않는다. 대표 NULL·duplicate 실패와 declarative schema 대조로 경계를 확인하며, 필수 year/purpose NULL은 source/staging quality가 build를 차단한다.
- Profile test는 선언의 회귀 보호다. Missing environment variable에 대한 dbt CLI error 문구를 계약으로 고정하지 않는다.
- 다른 adapter, external service, Airflow 실행과 data-operations orchestration을 검증하지 않는다.
