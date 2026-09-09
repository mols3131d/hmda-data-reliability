---
type: research
title: "Actual Airflow DAGRun Proof Planning Research (PR #229)"
description: "OpenSpec planning 전에 현재 orchestration verification gap, runtime isolation feasibility와 actual DAGRun proof 접근 선택에 필요한 근거를 조사한다."
tags:
  - orchestration
  - airflow
  - runtime-proof
  - mvp
  - pr-229
---

# Actual Airflow DAGRun Proof Planning Research (PR #229)

> [!NOTE]
> 본 조사는 GitHub Pull Request [#229](https://github.com/mols3131d/hmda-data-reliability/pull/229) 작업의 일환으로 진행되었습니다.
> 현재 repository는 Airflow DAG structure와 task wrapper behavior는 검증하지만 scheduler가 실제로 만든 DAGRun, TaskInstance lifecycle, Asset event와 DuckDB/dbt side effect의 정합성까지는 증명하지 않는다. Actual runtime proof를 시작하기 전 가장 중요한 planning risk는 **runtime artifact isolation**이며, 현재 evidence만 보면 disposable worktree 또는 temporary checkout이 production contract를 넓히지 않고 이를 해결할 가능성이 가장 높다. 다만 기존 Airflow CLI/runtime만으로 reproducible proof와 evidence retrieval이 충분한지는 local execution으로 확인해야 한다.

## Question

OpenSpec planning을 시작하기 전에 actual Airflow DAGRun proof에 관해 무엇을 이미 알고 있으며, 어떤 runtime gap과 isolation risk를 local agent가 먼저 확인해야 하는가?

## Scope

- `hmda_data_plane`의 현재 automated verification boundary.
- Actual Airflow runtime에서만 확인 가능한 gap.
- Airflow metadata, DuckDB, source fixture, dbt artifact와 working tree isolation feasibility.
- Existing runtime surface와 최소 helper 사이의 planning trade-off.
- 조사 결과가 OpenSpec artifact scope에 주는 의미.

### Out of Scope

- 새 requirement나 observable scenario 정의.
- Technical design 결정.
- File-level implementation task 또는 test case 목록.
- Runtime proof의 acceptance matrix 작성.
- Production behavior 변경을 선제적으로 가정하는 것.

## Findings

### Current tests stop before scheduler-created DAGRun behavior

`tests/orchestration/test_airflow_dag.py`는 DAG structure와 parameter contract를 검사하고, `tests/orchestration/test_airflow_execution.py`는 task의 `.function()`을 직접 호출하면서 `get_current_context()`와 domain call을 monkeypatch한다. 따라서 task wrapper가 올바른 public boundary를 호출하고 failure/skip evidence semantics를 보존하는 것은 확인하지만, Airflow scheduler가 실제 DAGRun과 TaskInstance를 생성하고 dependency state를 전이하는 경로는 거치지 않는다.

이 차이는 actual runtime proof가 기존 test를 반복하는 작업이 아니라는 근거다. Local agent는 먼저 현재 test가 이미 소유하는 behavior와 runtime-only observation을 분리해야 한다.

#### Verification Evidence

- [`tests/orchestration/test_airflow_execution.py`](../../../tests/orchestration/test_airflow_execution.py)
  - `airflow_dag.load_raw_hmda_loans.function()` 등 task function 직접 실행.
  - `_runtime_context()`가 `get_current_context()`를 monkeypatch해 outlet evidence를 local object로 대체.
- [`tests/orchestration/test_airflow_dag.py`](../../../tests/orchestration/test_airflow_dag.py)
  - DAG graph, parameter와 framework declaration 수준 검증.

### Canonical behavior is already defined, so the work starts as proof rather than feature definition

현재 `openspec/specs/orchestration-pipeline/spec.md`는 raw → gate → analytics ordering, quality gate failure containment, failed/skipped analytics evidence, runtime override boundary, schedule/retry policy와 control-plane exclusion을 이미 정의한다. 따라서 이 branch의 출발점은 새 orchestration behavior를 정하는 것이 아니라 **이미 정해진 behavior가 actual Airflow runtime에서도 성립하는지 확인하는 것**이다.

Runtime reconnaissance에서 현재 contract와 실제 behavior가 일치하면 OpenSpec은 behavior delta 없이 proof/tooling/documentation 성격의 change로 계획할 수 있다. 반대로 actual DAGRun에서 contract violation이 확인되면 그 시점부터 behavior delta가 별도 planning 대상이 된다. Inbox research가 어느 쪽의 requirement를 미리 작성해서는 안 된다.

#### Canonical Behavior Evidence

- [`openspec/specs/orchestration-pipeline/spec.md`](../../../openspec/specs/orchestration-pipeline/spec.md)
  - ordered stage execution, quality gate failure, execution/data-update evidence, runtime policy와 disabled analytics semantics를 이미 소유.
- [`openspec/schemas/spec-driven-tdd/README.md`](../../../openspec/schemas/spec-driven-tdd/README.md)
  - Proposal → Specs → Design → Tasks ownership을 분리하고, spec-level behavior가 바뀌지 않는 change는 `skip_specs`를 사용할 수 있음을 정의.

### Database-only sandboxing is insufficient for a clean analytics proof

기존 sandbox guide는 별도 `AIRFLOW_HOME`과 sandbox DuckDB 사용을 안내하지만 analytics run이 생성하는 dbt artifact는 repository-relative `dbt/target` surface를 사용한다. DAG의 runtime override는 `database_path`, `source_root`, `source_year`, `source_file`, `run_dbt_build` 다섯 필드뿐이며 artifact root를 별도로 주입하는 surface는 없다.

따라서 main working tree에서 `database_path`만 분리해 clean analytics run을 수행하면 DuckDB는 안전해도 기존 dbt current artifact와 run artifact를 변경할 수 있다. Actual DAGRun proof의 첫 기술적 unknown은 “어떤 시나리오를 돌릴 것인가”보다 **기존 작업 state와 artifact surface를 완전히 분리할 수 있는가**다.

#### Sandbox Isolation Evidence

- [`src/hmda_reliability/orchestration/dags/hmda_data_plane.py`](../../../src/hmda_reliability/orchestration/dags/hmda_data_plane.py)
  - `_RUNTIME_OVERRIDE_FIELDS`는 다섯 runtime parameter만 허용.
- [`inbox/2026-09-04/07-12-guide-orchestration-sandbox-dag-testing.md`](../../2026-09-04/07-12-guide-orchestration-sandbox-dag-testing.md)
  - sandbox DB와 `AIRFLOW_HOME` 중심의 기존 수동 실행 절차.
- Notion `Actual Airflow DAGRun Proof Plan`
  - dbt current/run artifact와 worktree까지 분리해야 한다는 planning source.

### Disposable worktree or temporary checkout is the strongest current isolation candidate

현재 runtime API에 test-only artifact path를 추가하지 않으면서 repository-relative dbt path까지 격리하려면 target revision의 disposable Git worktree 또는 temporary checkout에서 Airflow를 실행하는 방식이 가장 직접적이다. 이 방식은 Airflow metadata, fixture, DuckDB와 `dbt/target`을 하나의 proof root 아래로 모을 수 있고 production runtime contract를 변경하지 않는다.

이 결론은 아직 implementation decision이 아니다. Local execution에서 Airflow DAG discovery, package import, dbt working directory와 environment가 disposable checkout에서도 정상 작동하는지 확인해야 한다. 성공하면 OpenSpec Design이 별도 runtime capability를 만들 이유가 줄어들고, 실패하면 실패 원인이 tooling gap인지 production runtime limitation인지 분리해야 한다.

### Existing Airflow surfaces should be tested before introducing a helper

이 proof의 가치 중 하나는 실제 Airflow runtime이 현재 repository contract를 보존하는지 확인하는 데 있다. 따라서 먼저 `airflow` CLI/runtime 자체로 DAG load, DAGRun execution과 runtime evidence 조회가 가능한지 확인하는 편이 가장 정보량이 높다.

별도 harness는 다음과 같은 실제 gap이 관찰될 때만 planning candidate가 되는 편이 낫다.

- 동일한 setup을 반복할 때 환경 준비가 수동 state에 과도하게 의존한다.
- DAGRun terminal state 또는 Asset evidence를 안정적으로 회수하기 어렵다.
- Isolation invariant를 사람이 매번 확인해야 해서 proof reproducibility가 낮다.

반대로 단순히 command 수를 줄이기 위한 wrapper는 actual-runtime truth를 증명하는 데 필수적이지 않으며 OpenSpec scope를 불필요하게 키울 수 있다.

### Runtime evidence categories are known, but their exact retrieval path is still a local unknown

Planning source와 current contract를 합치면 actual proof에서 관심을 가져야 할 evidence category는 이미 분명하다: DAGRun/TaskInstance state, Airflow Asset update evidence, sandbox DuckDB state, dbt artifact state와 target revision provenance다.

하지만 Inbox에서 exact query, helper API, evidence schema를 정하면 OpenSpec Design 또는 Tasks를 선행하게 된다. Local agent가 먼저 Airflow 3.3.0의 실제 CLI/API와 metadata DB에서 어떤 evidence를 안정적으로 얻을 수 있는지 조사하고, 그 결과를 OpenSpec planning에 넘기는 편이 적절하다.

## Options

| Criterion | Existing Airflow CLI + disposable worktree | Minimal proof helper | Production runtime path extension |
| --- | --- | --- | --- |
| Production contract 영향 | 없음 | 보통 없음 | 있음 |
| Actual runtime truth 보존 | 가장 직접적 | helper가 orchestration을 대체하지 않으면 유지 가능 | runtime contract 자체가 달라질 수 있음 |
| Isolation 가능성 | 높음, local verification 필요 | helper가 worktree/setup을 관리하면 높일 수 있음 | artifact path 자체를 직접 제어 가능 |
| 사전 planning 적합성 | **우선 조사** | CLI만으로 부족할 때 후보 | test convenience만으로는 선택하지 않음 |

현재 선택은 첫 번째 option을 **local reconnaissance의 출발점**으로 삼는 것이다. 이것은 최종 Design 결정이 아니라, production capability를 늘리기 전에 existing surface의 실제 한계를 확인하자는 조사 순서다.

## Implications

- OpenSpec artifact를 만들기 전에 local agent는 actual runtime invocation과 isolation feasibility에 관한 unresolved fact를 먼저 확인하는 편이 낫다.
- Actual runtime이 canonical contract와 일치하고 별도 helper만 필요하다면 spec-level behavior를 새로 정의할 근거는 현재 없다.
- Runtime contract violation이 나오면 해당 observation이 OpenSpec Specs/Design 판단의 입력이 되고, Inbox에서 임시 requirement나 patch를 만들지 않는다.
- 기존 `inbox` artifact는 OpenSpec이 시작된 뒤 normative planning source로 유지하지 않는다. OpenSpec artifact가 why/scope, behavior, technical delta와 implementation outcomes를 소유한다.

## Open Questions

- Airflow 3.3.0의 현재 repository environment에서 scheduler-created DAGRun을 가장 단순하게 생성하고 terminal state까지 관찰할 수 있는 repository-native 실행 경로는 무엇인가?
- TaskInstance state와 Asset event를 CLI/API/metadata DB 중 어떤 surface에서 가장 안정적으로 회수할 수 있는가?
- Disposable worktree에서 dbt subprocess의 cwd와 `dbt/target`이 예상대로 해당 worktree에 고정되는가?
- 최소 clean/dirty fixture가 current data-operation/reliability contract를 그대로 사용할 수 있는가, 아니면 fixture preparation 자체에 별도 helper가 필요한가?
- Existing Airflow surface만으로 setup과 evidence capture가 충분히 reproducible한가, 아니면 OpenSpec Design에서 최소 helper를 정당화할 operational gap이 실제로 관찰되는가?
