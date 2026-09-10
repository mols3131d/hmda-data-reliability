---
type: report
title: "Actual Airflow DAGRun Proof Result"
description: "Airflow 3.3.0 격리 실행의 품질 차단, 정상 promotion, Asset 이벤트와 무오염 증거 및 scheduler proof 한계."
tags: [orchestration, airflow, runtime-proof, isolation, pr-229]
---

# Actual Airflow DAGRun Proof Result

## Summary

2026-09-09 UTC, head `503fb945f5dbcb6ed9fb018f1a13fcb5eb23679b`의 수정하지 않은 `hmda_data_plane`를 Airflow **3.3.0**에서 두 번 실행했다. 결함 gate 차단과 정상 dbt build/promotion은 통과했다. 메인 DuckDB와 manifest는 SHA-256, 크기, nanosecond mtime이 모두 불변이며 disposable worktree를 제거했다.

> [!WARNING]
> 두 실행 모두 metadata DB에서 `run_type=manual`, `triggered_by=TEST`, `triggering_user_name=dag_test`, `creating_job_id=null`, `scheduled_by_job_id=null`이다. 따라서 `dags test`를 scheduler service가 생성·처리한 실행으로 표현하지 않는다. 다만 canonical spec과 2026-09-09 확정된 MVP 범위는 scheduler-service 실행이나 자동·주기 생성을 요구하지 않으므로 이 한계는 PR 완료 blocker가 아니다. 두 시나리오만으로 spec 전체를 종단 간 실측했다고도 주장하지 않는다.

## Execution

| Scenario | Run ID | DAGRun | CLI Exit |
| --- | --- | --- | --- |
| A: Dirty | `manual__2026-09-09T11:19:13.439045+00:00` | failed | 1 (expected) |
| B: Clean | `manual__2026-09-09T11:19:28.953401+00:00` | success | 0 |

Worktree는 `.local/worktrees/pr229-final-proof`에 detached HEAD로 생성했다. 메인 venv를 재사용하되 `PYTHONPATH=<worktree>/src`와 worktree cwd를 사용했고 실제 package import가 worktree 아래임을 assertion으로 확인했다. 각 시나리오의 `AIRFLOW_HOME`, SQLite 연결, DuckDB와 source directory는 별도 `.local/dirty` 및 `.local/clean` 아래다. `TMPDIR`도 worktree 내부로 지정했다. 메인 실데이터는 fixture로 읽거나 적재하지 않았다. 보호 파일 SHA-256 계산만 read-only로 수행했다.

시나리오 A는 허용된 `data/samples/hmda/year_2025.csv`를 복사했다. [선행 정찰](02-report-orchestration-actual-airflow-dagrun-reconnaissance.md) 기록의 “20행”과 달리 **실제 적재량은 19행**이다. 시나리오 B는 같은 CSV의 header와 첫 data row를 template으로 1,000행을 작성하고 `activity_year=2025`, `loan_amount=200000+index`, `income=NA` 161행 및 `income=80` 839행으로 설정했다. Synthetic income null rate는 **16.1%**다.

시나리오마다 다음 순서로 동기 실행했다. `database_path`와 `source_root`는 해당 worktree의 절대 경로이며 `source_year=2025`, `run_dbt_build=true`다.

```bash
python -m airflow version
python -m airflow db migrate
python -m airflow dags reserialize
python -m airflow dags test hmda_data_plane -c '<scenario JSON>'
python -m airflow tasks states-for-dag-run hmda_data_plane '<RUN_ID>' -o json
```

## Task Evidence

CLI JSON의 task별 state/start/end 필드를 발췌했다. 모든 시간은 UTC다. 이는 terminal state와 실행 순서 증거이며 모든 중간 상태 전이를 sampling한 기록은 아니다.

```json
{
  "dirty": [
    {"task_id":"load_raw_hmda_loans","state":"success","start_date":"2026-09-09T11:19:14.073126+00:00","end_date":"2026-09-09T11:19:17.013841+00:00"},
    {"task_id":"evaluate_quality_gate","state":"failed","start_date":"2026-09-09T11:19:17.078593+00:00","end_date":"2026-09-09T11:19:17.134628+00:00"},
    {"task_id":"build_dbt_loan_analytics","state":"upstream_failed","start_date":"2026-09-09T11:19:17.167499+00:00","end_date":"2026-09-09T11:19:17.167499+00:00"}
  ],
  "clean": [
    {"task_id":"load_raw_hmda_loans","state":"success","start_date":"2026-09-09T11:19:29.665287+00:00","end_date":"2026-09-09T11:19:32.631072+00:00"},
    {"task_id":"evaluate_quality_gate","state":"success","start_date":"2026-09-09T11:19:32.691288+00:00","end_date":"2026-09-09T11:19:32.740752+00:00"},
    {"task_id":"build_dbt_loan_analytics","state":"success","start_date":"2026-09-09T11:19:32.779396+00:00","end_date":"2026-09-09T11:19:36.808860+00:00"}
  ]
}
```

Dirty log에는 다음 causal chain이 남았다. 실패 판정은 CLI exit만이 아니라 SQLite TaskInstance 상태와 analytics 이벤트 부재까지 대조했다.

```text
hmda_reliability.reliability.quality_gate.QualityGateError:
품질 게이트 실패: source_year=2025 asset=source.hmda_reliability.raw.hmda_loans detected=[null_spike(income)]
airflow.sdk.exceptions.AirflowException:
품질 게이트 실패: source_year=2025 asset=source.hmda_reliability.raw.hmda_loans detected=[null_spike(income)]
```

## Asset And Projection Evidence

각 격리 SQLite DB를 `mode=ro`로 열어 `SELECT * FROM dag_run`, `SELECT * FROM task_instance`, `SELECT * FROM asset_event`를 실행했다. 아래는 `asset_event` 결과의 핵심 필드다. source DAG는 모두 `hmda_data_plane`이고 source run은 위 해당 시나리오 ID와 일치한다.

| Scenario | Event ID | Source Task | Timestamp (UTC) | Extra |
| --- | --- | --- | --- | --- |
| Dirty | 1 | load_raw_hmda_loans | 11:19:17.034548 | raw_load, data_update=true, source_file_count=1, source_year=2025, hmda_loans_row_count=19 |
| Clean | 1 | load_raw_hmda_loans | 11:19:32.651644 | raw_load, data_update=true, source_file_count=1, source_year=2025, hmda_loans_row_count=1000 |
| Clean | 2 | build_dbt_loan_analytics | 11:19:36.819146 | analytics_build, data_update=true, return_code=0 |

Raw event의 `database_path`와 `source_root`는 각각 `<worktree>/.local/<scenario>/sandbox.duckdb`, `<worktree>/.local/<scenario>/source`다. Dirty에는 analytics event가 **0개**, clean에는 **1개**다.

Clean analytics event의 나머지 extra:

```json
{
  "manifest_path": "/home/mols3131d/workspaces/hmda-data-reliability/.local/worktrees/pr229-final-proof/dbt/target/runs/current/run-5kkahnlr/manifest.json",
  "run_results_path": "/home/mols3131d/workspaces/hmda-data-reliability/.local/worktrees/pr229-final-proof/dbt/target/runs/current/run-5kkahnlr/run_results.json",
  "projection_id": "sha256:ac529ed0fe8f165856fd1f124c318350d25054aba708db249d3e8989fa49dffe"
}
```

Worktree의 candidate와 top-level current manifest/run_results를 정리 전에 로컬 evidence directory로 회수했다. dbt run_results에는 **모델 2개 success, 테스트 18개 pass**가 기록됐다. 모델은 `stg_hmda_loans`, `mart_hmda_loan_outcomes`다. 회수한 candidate/current manifest와 run_results 각각의 바이트 일치 assertion을 통과했다. Public `artifact_projection_id()`로 current pair를 재계산한 값도 위 Asset event의 projection ID와 일치했다.

## Isolation Evidence

아래 값은 실행 전후 동일하다.

| Protected File | Bytes | Mtime Ns | SHA-256 |
| --- | --- | --- | --- |
| data/hmda_reliability.duckdb | 930099200 | 1788404673367919779 | 07e95e769ba973ecbbd47f3bd47fd520b145e2a7e3ffe81d5585e597b9c4b71b |
| dbt/target/manifest.json | 664324 | 1788848463763517457 | 085e47dcc58ca4717a2debccc813a0fb939da502ecaa6d321814fc2044a887f6 |

```json
{"unchanged": true, "worktree_removed": true}
```

첫 시도는 Git 미추적 샘플이 worktree에 없어 DAG 실행 전 실패했다. `finally`에서 worktree 정리와 지문 검사를 수행했고, 허용된 메인 샘플을 읽도록 수정한 뒤 위 두 실행을 완료했다. 최종 `git worktree remove <path> --force` 후, 보고서 편집 전 `git status --porcelain` 출력은 비어 있었다. 보고서와 tasks 수정은 의도된 문서 변경이며 commit 요청 없이 이를 clean으로 만들기 위해 commit하거나 삭제하지 않는다.

전체 로그, CLI JSON, SQLite 결과, conf, provenance, before/after JSON과 회수한 dbt target은 Git 미추적 `.local/pr229-proof-evidence/`에 있다. `projection-verification.json`은 회수한 artifact만 읽어 별도 실행한 candidate/current 비교와 public projection ID 재계산의 통과 결과다. 임시 실행기는 `.local/pr229-proof.py`이며 영구 tooling으로 도입하지 않는다. 제거된 worktree의 경로는 실행 당시 identity이며 현재 열 수 있는 경로가 아니다.

## Verification Reconciliation

2026-09-10 canonical spec의 10개 Requirement와 28개 Scenario를 기존 자동화 검증 및 위 두 실행에 대조했다. 직접 관련된 orchestration, quality gate, reliability policy와 dbt promotion 테스트 모듈 6개를 현재 revision에서 실행했으며 **74개 테스트가 모두 통과했다**.

```bash
uv run pytest \
  tests/orchestration/test_airflow_dag.py \
  tests/orchestration/test_airflow_execution.py \
  tests/orchestration/test_config.py \
  tests/data_operations/test_quality_gate.py \
  tests/reliability/test_quality_gate.py \
  tests/data_operations/test_dbt_runner.py
```

결합 근거는 다음 범위를 제공한다.

- 실제 Airflow 3.3.0 실행은 ordered success, blocking gate failure, TaskInstance terminal state, Asset event, dbt promotion과 격리를 검증한다.
- 자동화 테스트는 raw·analytics failure, disabled analytics skip, runtime config precedence, full-Bronze gate, canonical source/config, lock-bound recheck, failure propagation, promotion atomicity, domain delegation과 task data boundary를 검증한다.
- Canonical spec은 모든 Scenario를 scheduler daemon 기반 종단 간 실행으로 검증하라고 요구하지 않는다. 가장 낮은 유효 경계의 자동화 테스트와 핵심 실제 실행을 결합한 결과, 옵션 A 범위에서 추가로 해소해야 할 필수 verification gap은 확인되지 않았다.

## Scope And Limits

- Production code, canonical spec과 영구 harness를 변경하지 않은 일회성 verification/report다. OpenSpec Change와 `skip_specs: true` 설정은 만들지 않는다.
- Scheduler service 실행, 모든 TaskInstance 중간 상태의 연속 sampling과 모든 실패 경로의 별도 Airflow 실측은 수행하지 않았다. 이는 명시된 증거 범위의 제한이며 현재 spec 또는 MVP acceptance blocker가 아니다.
- 향후 scheduler-service 운영 경로나 반복 가능한 runtime harness가 요구되면 현재 PR의 누락 수정이 아니라 별도 요구사항과 변경으로 평가한다.
