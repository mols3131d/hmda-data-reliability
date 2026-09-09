---
type: plan
title: "Actual Airflow DAGRun Proof"
description: "실제 Apache Airflow runtime에서 hmda_data_plane의 실행 순서, failure containment, data/artifact/Asset evidence와 isolation을 검증하기 위한 구현 및 검증 계획."
tags:
  - orchestration
  - airflow
  - runtime-proof
  - mvp
---

# Actual Airflow DAGRun Proof

이 작업은 Airflow 기능을 확대하는 PR이 아니다. 현재 `hmda_data_plane`이 실제 Apache Airflow runtime에서도 `raw load → quality gate → analytics build` 계약을 보존하는지, 특히 blocking dirty input에서 analytics 승격을 실제로 차단하는지를 증명한다.

현재 repository는 DAG 구조와 task function 수준의 계약을 이미 검증하지만 실제 scheduler가 만든 DAGRun, TaskInstance state, Asset event와 DuckDB/dbt side effect가 함께 일치한다는 proof는 아직 없다. 따라서 이번 변경의 완료 조건은 새 기능 수가 아니라 **실제 runtime evidence가 canonical orchestration contract와 일치하는가**다.

## Basis

- **Branch base:** `main@f098190b75df5ae359ab6fc2bb4646cbcddde8bd`
- **Canonical contract:** `openspec/specs/orchestration-pipeline/spec.md`
- **Architecture guide:** `docs/domains/orchestration.md`
- **MVP boundary:** `docs/mvp.md`
- **Planning source:** `Actual Airflow DAGRun Proof Plan` Notion page
- **Prior working note:** `inbox/2026-09-04/07-12-guide-orchestration-sandbox-dag-testing.md`

기존 working note의 DB 경로 격리만으로는 충분하지 않다. Airflow trigger surface는 `database_path`, `source_root`, `source_year`, `source_file`, `run_dbt_build`만 override하며 dbt candidate/current artifact는 repository-relative `dbt/target` surface를 사용한다. Clean analytics run이 기존 current projection을 바꾸지 않게 하려면 proof root 전체를 격리해야 한다.

## Goal

실제 Airflow runtime에서 다음을 하나의 target revision 기준으로 증명한다.

1. `hmda_data_plane`이 정상 parse되고 실제 DAGRun을 생성한다.
1. Clean input은 raw → gate → analytics 순서로 실제 TaskInstance `success`를 만들고 DuckDB, dbt artifact와 Asset evidence가 일치한다.
1. Blocking dirty input은 quality gate를 실제 `failed`로 만들고 analytics task body, dbt subprocess, artifact promotion과 analytics update evidence를 모두 차단한다.
1. `run_dbt_build=false`는 raw/gate 성공을 보존하면서 analytics만 `skipped`로 남기고 analytics update evidence를 만들지 않는다.
1. DAGRun에 reliability control plane, approval, recovery, evaluation 또는 AI task가 포함되지 않고 schedule/automatic retry가 활성화되지 않는다.

## Isolation Gate

Proof 실행 전 아래 surface를 모두 기존 개발 상태와 분리한다.

- **Airflow runtime:** 전용 `AIRFLOW_HOME`, metadata DB, logs, generated auth/config.
- **DuckDB:** proof 전용 `database_path`; 기본 `data/hmda_reliability.duckdb` 사용 금지.
- **Input fixture:** `.local` 또는 임시 root 아래의 작고 deterministic한 clean/dirty source.
- **dbt artifacts:** `dbt/target/runs/*`, current `manifest.json`, `run_results.json`이 기존 작업 상태와 분리되어야 한다.
- **Working tree:** canonical dbt project layout은 유지하되 repository-relative artifact surface까지 분리할 수 있는 disposable worktree 또는 temporary checkout을 사용한다.

이 isolation을 안전하게 만들 수 없다면 production contract에 test-only artifact path injection을 추가해 우회하지 않는다. 해당 상태는 **BLOCKED**로 기록하고 isolation blocker를 먼저 해결한다.

## Proof Scenarios

### S0 — Runtime Bootstrap

- 격리된 `AIRFLOW_HOME`과 DAG folder를 target revision에 고정한다.
- examples를 비활성화한다.
- 실제 Airflow CLI/runtime에서 `hmda_data_plane` parse와 listing을 확인한다.
- active full data-plane DAG가 하나인지, schedule 없음, retries `0`, `max_active_runs=1`인지 확인한다.

**Evidence:** target SHA, runtime version/config locator, DAG listing/inspection 결과.

### S1 — Clean Actual DAGRun

Expected state:

```text
load_raw_hmda_loans       success
evaluate_quality_gate     success
build_dbt_loan_analytics  success
```

추가로 다음 side effect와 evidence를 확인한다.

- sandbox DuckDB에 expected Bronze rows가 존재한다.
- dbt staging/mart가 같은 sandbox DB를 사용한다.
- candidate artifact가 생성되고 검증된 current projection으로 promotion된다.
- raw Asset event의 DB/source/row-count evidence가 실제 state와 일치한다.
- analytics Asset event의 return code/artifact/projection evidence가 실제 생성물과 일치한다.

### S2 — Blocking Dirty Actual DAGRun

대표 blocking case는 `null_spike(income)`를 사용한다.

Expected state:

```text
load_raw_hmda_loans       success
evaluate_quality_gate     failed
build_dbt_loan_analytics  upstream_failed 또는 미실행
```

Task state만 확인하지 않는다. 다음을 별도 증명한다.

- gate failure에 blocking incident discriminator가 남는다.
- analytics task body와 dbt subprocess가 시작되지 않는다.
- 새 analytics Asset update evidence가 없다.
- dirty run 때문에 current dbt artifact projection이 바뀌지 않는다.
- raw load 성공 evidence는 보존된다.

### S3 — Disabled Analytics Semantics

`run_dbt_build=false`로 실제 DAGRun을 생성한다.

Expected state:

```text
load_raw_hmda_loans       success
evaluate_quality_gate     success
build_dbt_loan_analytics  skipped
```

Analytics candidate/promotion 및 성공 Asset update evidence가 없어야 한다.

## Implementation Strategy

1. **Repository-native 실행 가능성부터 확인한다.** 기존 CLI와 runtime surface만으로 S0–S3를 재현할 수 있으면 별도 harness를 추가하지 않는다.
1. **반복성과 evidence capture에 필요한 최소 helper만 추가한다.** Harness가 필요하면 proof root 생성, fixture 준비, runtime invocation 또는 evidence extraction처럼 반복 실행을 안정화하는 책임으로 제한한다.
1. **Harness 자체의 invariant만 deterministic test로 고정한다.** 기존 DAG 구조/task wrapper 테스트를 중복하지 않는다.
1. **Runtime contract 차이를 발견한 경우에만 구현을 수정한다.** Actual DAGRun이 canonical spec과 어긋날 때 원인에 해당하는 가장 작은 production change를 만들고 동일 시나리오를 재실행한다.
1. **최종 proof report에 target SHA와 evidence locator를 남긴다.** 일회성 screenshot, metadata DB, sandbox DuckDB, generated auth 파일과 전체 dbt run artifact는 commit하지 않는다.

## Deliverables

필요한 것만 포함한다.

- 재현 가능한 actual-DAGRun proof harness — 기존 workflow만으로 반복 가능한 proof가 어렵다면 추가.
- Focused tests — harness 또는 isolation invariant를 유지할 가치가 있을 때만 추가.
- Runtime/validation documentation update — 현재 canonical guide와 실제 절차가 다를 때만 수정.
- Proof report — target Git SHA, 환경, scenario별 `PROVEN`/`FAILED`/`BLOCKED`, evidence locator를 기록.

## Acceptance

Actual Airflow DAGRun proof는 아래를 모두 만족해야 `PROVEN`으로 닫는다.

- [ ] target Git revision과 clean initial state가 고정되어 있다.
- [ ] Airflow metadata, DuckDB, source fixture와 dbt artifact surface가 기존 개발 상태와 격리되어 있다.
- [ ] 실제 Airflow runtime이 `hmda_data_plane`을 load하고 DAGRun을 생성한다.
- [ ] clean run에서 raw → gate → analytics가 실제 TaskInstance `success`로 완료된다.
- [ ] clean run의 DuckDB/dbt/Asset evidence가 TaskInstance state와 일치한다.
- [ ] dirty run에서 gate가 blocking incident로 `failed`가 된다.
- [ ] dirty run에서 analytics가 실행되지 않고 analytics update/promotion evidence가 생기지 않는다.
- [ ] `run_dbt_build=false`에서 analytics가 `skipped`이고 성공 update evidence가 없다.
- [ ] control-plane/recovery/AI task가 DAGRun에 포함되지 않는다.
- [ ] schedule과 automatic retry가 활성화되지 않는다.
- [ ] proof 결과가 target SHA와 재현 절차에 연결되어 있다.

## Outcome Rules

- **PROVEN:** isolation과 핵심 runtime scenario가 모두 계약과 일치한다.
- **FAILED:** actual runtime에서 contract violation이 확인된다. 원인에 해당하는 최소 변경 후 같은 proof를 재실행한다.
- **BLOCKED:** 안전한 isolation 또는 재현 가능한 actual DAGRun을 만들 수 없다. test-only 우회로 통과 처리하지 않는다.

이 proof가 `PROVEN`으로 닫히기 전에는 actual Airflow data plane이 runtime 수준에서 검증됐다고 간주하지 않는다.
