# Airflow DAGRun Test Design

## Contract And Scope

[orchestration-pipeline specification](../../openspec/specs/orchestration-pipeline/spec.md)의 ordered execution, quality gate failure, execution/data update evidence, disabled analytics와 task data boundary를 실제 Airflow CLI 실행으로 검증한다. 대응 구현은 [test_airflow_dagrun.py](test_airflow_dagrun.py)다.

기존 [task wrapper tests](test_airflow_execution.py)는 함수 호출과 예외 계약을 유지한다. 이 모듈은 task나 domain 함수를 mock하지 않고 `airflow db migrate`, `airflow dags reserialize`, `airflow dags test`를 별도 프로세스에서 실행한다. Primary marker는 `integration`이며 기본 pytest 실행에 포함한다.

## Scenarios And Oracles

| Scenario | Input | Persisted Oracle | Test |
| --- | --- | --- | --- |
| Disabled analytics | 1,000행 정상 입력, `run_dbt_build=false` | DAGRun success; raw/gate success, analytics skipped; raw 이벤트만 존재; `dbt/target` 디렉터리 부재 | `test_disabled_analytics_is_skipped_without_asset_update` |
| Raw failure | 빈 source directory | DAGRun failed; raw failed, gate/analytics upstream_failed; Asset 이벤트와 `dbt/target` 없음 | `test_raw_failure_blocks_gate_and_analytics_without_events` |
| Blocking quality gate | income NULL 400/1,000행 | DAGRun failed; gate failed, analytics upstream_failed; raw 이벤트만 존재; `null_spike(income)` 및 AirflowException 로그; `dbt/target` 없음 | `test_quality_gate_blocks_analytics_with_incident_evidence` |
| Ordered promotion | income NULL 161/1,000행, build enabled | 세 task success와 start/end datetime 순서; raw/analytics 이벤트 및 URI 일치; candidate/current 바이트 및 projection ID 일치; 실제 Bronze/staging/mart 결과 | `test_success_promotes_candidate_and_records_analytics_update` |
| dbt failure | 정상 income, `loan_purpose=NA`, 기존 current sentinel pair | raw/gate success, analytics failed; raw 이벤트만 존재; 실제 dbt not_null 실패 결과; current 바이트 불변 | `test_dbt_failure_preserves_current_without_analytics_update` |

모든 시나리오는 CLI 종료 코드와 독립 SQLite 조회를 함께 사용한다. Run은 정확히 하나이고 `triggered_by=TEST`여야 한다. Asset 이벤트의 DAG/task/run identity 및 URI(`hmda/raw/hmda_loans`, `hmda/analytics/loan_analytics`)를 확인하며 XCom 테이블 전체가 비어 있어야 한다(`SELECT key FROM xcom` 공백). 정상 입력의 독립 데이터 oracle은 Bronze/staging 1,000행, staging income non-null 839행, mart application/approval/denial count 1,000/1,000/0이다. Failure 테스트의 sentinel은 이전 artifact 바이트 보존만 검사하며 유효한 이전 dbt run이라고 주장하지 않는다.

정상 실행에서는 필수 staging/mart 모델의 성공을 확인하되 다른 정상 모델의 추가를 허용한다. 추가 모델을 포함한 모든 dbt 결과는 여전히 `success` 또는 `pass`여야 한다. Raw Asset evidence는 필수 필드의 값과 `data_update is True`를 검사하며 부가 metadata 필드는 허용한다. Task 상태, 이벤트 발행 주체, candidate/current 바이트와 실제 데이터 결과 검증은 그대로 유지한다.

## Fixture Policy

`_SOURCE_YEAR`, `_FIXTURE_ROW_COUNT`, `_ACCEPTED_INCOME_NULL_COUNT`, `_BLOCKING_INCOME_NULL_COUNT`는 테스트 입력의 고정된 의도를 소유한다. 파일명, request와 CSV의 연도는 같은 상수를 사용한다. 정상 income non-null 기대값은 fixture 행 수에서 의도한 NULL 행 수를 뺀 값이며 production 계산이나 실행 결과에서 정답을 가져오지 않는다.

정상 입력의 161/1,000은 accepted 2025 income profile에 가까운 통과 사례이고, 400/1,000은 명확한 차단 사례다. 정확한 threshold 경계 테스트는 아니다. [Quality gate policy](../../src/hmda_reliability/reliability/quality_gate.py)의 baseline, threshold 또는 필수 profile column이 변경되면 fixture의 통과·차단 의도를 재검토한다. Production policy에서 fixture 값을 자동 계산하거나 실패를 피하려고 기대값을 자동 갱신하지 않는다. 수치 정책과 경계값 자체는 [기존 quality gate 테스트](../reliability/test_quality_gate.py)가 검증한다.

## Isolation And Lifecycle

- 각 테스트는 repository `.local/` 아래 고유 임시 checkout에 현재 `src/`와 canonical `dbt/` 입력을 복사한다. Git HEAD만 사용하는 worktree와 달리 미커밋 source 변경도 검사한다. 기존 `target`, `logs`, bytecode는 복사하지 않는다.
- CSV는 테스트에서 생성한다. Git 미추적 sample, 메인 실데이터 내용, 기존 Airflow metadata에 의존하지 않는다.
- 실제 import가 임시 checkout에 속하는지 확인한다. 별도 HOME, AIRFLOW_HOME, SQLite 연결, DuckDB, source, TMPDIR, dbt artifact와 subprocess 환경을 사용한다.
- subprocess는 현재 pytest interpreter와 같은 venv의 CLI를 사용한다. 부모 프로세스의 environment와 cwd를 바꾸지 않는다.
- CLI command별 timeout은 60초, test timeout은 240초다. command 종료 또는 timeout 시 별도 process group을 종료한 뒤 임시 checkout을 정리한다. 무조건 skip하거나 기대하지 않은 오류를 성공으로 처리하지 않는다.
- 모듈 전후 메인 DuckDB 및 current manifest/run_results의 존재 여부, 크기, mtime_ns, SHA-256을 read-only로 비교한다. 메인 파일이 없는 새 checkout에서도 부재 보존을 확인한다.
- CLI 실패 시 해당 실행 로그를 assertion에 포함한다. 임시 DB와 전체 로그는 테스트 종료 시 제거하며 영구 증거 저장 서비스를 추가하지 않는다.

## Run

Repository venv와 의존성이 준비된 Linux 환경에서 실행한다.

```bash
uv run pytest tests/orchestration/test_airflow_dagrun.py
```

관련 회귀 검증은 `uv run pytest tests/orchestration`으로 실행한다. 이 테스트는 자동 발견되는 기존 integration suite에 편입되므로 별도 CI job이나 marker를 추가하지 않는다.

## Exclusions

- Scheduler daemon, executor service, 자동 schedule, distributed execution을 입증하지 않는다. `dags test` 실행과 service-managed 실행을 동일시하지 않는다.
- 모든 TaskInstance 중간 상태의 연속 관찰이나 28개 Spec Scenario 전체의 종단 간 재실행을 주장하지 않는다.
- Promotion 중 파일 교체 실패, lock-bound gate recheck, config precedence와 domain policy의 상세 경계는 기존 [dbt runner tests](../data_operations/test_dbt_runner.py), [quality gate tests](../data_operations/test_quality_gate.py), [config tests](test_config.py), [task wrapper tests](test_airflow_execution.py)가 소유한다.
- DAGRun failed는 dbt가 작성한 분석 테이블의 rollback을 뜻하지 않는다. 이 모듈의 실패 보존 oracle은 analytics 이벤트와 current artifact pair다.
