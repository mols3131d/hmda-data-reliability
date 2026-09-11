---
type: review
title: PR #228 Merge Readiness Review
description: PR #228의 OpenSpec admission routing과 현재 main 기준 merge readiness를 검토한 결과다.
tags:
  - "domain:software-engineering"
  - ci
  - openspec
  - pr-228
---

# PR #228 Merge Readiness Review

> [!IMPORTANT]
> **Revise** — 기존 review improvement는 대부분 유효하지만, `orchestration-pipeline` canonical Spec의 executable routing에 실제 coverage gap이 남아 있고 현재 `main` 기준 prospective-merge CI evidence도 없다. 두 항목을 닫기 전에는 merge하지 않는 편이 맞다.

- **Target** — [PR #228](https://github.com/mols3131d/hmda-data-reliability/pull/228)
- **Revision** — head `c64b8ac07acb24ed3a0eed1e18a1b488db467c07`; reviewed against current `main=dcc114ae75980a000624de992fee156d72c273bf`
- **Scope** — canonical OpenSpec capability → executable test routing, affected/bulk validation behavior, dependency/runtime admission, current prospective-merge evidence

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 **Major** | `orchestration-pipeline` Spec 변경이 `tests/orchestration`만 선택해 Spec이 직접 요구하는 Reliability/Data Operations 동작을 검증하지 못한다. | `orchestration-pipeline` routing에 실제 contract owner의 관련 test surface를 포함하고 classifier regression을 갱신한다. |
| F2 | 🟠 **Major** | 성공한 CI는 과거 `main=1bb7a82`와의 prospective merge를 검증했으며 현재 `main=dcc114a`와 합쳐질 상태는 검증하지 않았다. | F1 수정 후 최신 `main`을 반영하고 새 prospective-merge CI 성공을 확인한다. |

## Details

### F1 · `orchestration-pipeline` Executable Routing Is Too Narrow

#### Locations

- [`.github/workflows/classify_changes.sh`](../../.github/workflows/classify_changes.sh)
  - `add_openspec_spec_target()`
  - `orchestration-pipeline)` mapping
- [`openspec/specs/orchestration-pipeline/spec.md`](../../openspec/specs/orchestration-pipeline/spec.md)
  - `Data quality gate execution`
  - `Domain delegation`
- [`tests/orchestration/test_airflow_execution.py`](../../tests/orchestration/test_airflow_execution.py)
  - orchestration adapter와 task behavior 검증
- [`tests/data_operations/test_dbt_runner.py`](../../tests/data_operations/test_dbt_runner.py)
  - canonical dbt configuration과 lock-bound quality-gated build 검증
- [`tests/reliability/test_quality_gate.py`](../../tests/reliability/test_quality_gate.py)
  - blocking incident scope와 quality policy 검증
- [`tests/test_ci_classifier.py`](../../tests/test_ci_classifier.py)
  - canonical Spec routing regression

#### Evidence

현재 classifier는 `openspec/specs/orchestration-pipeline/**` 변경에 `tests/orchestration`만 선택한다.

그러나 canonical `orchestration-pipeline` Spec은 단순한 Airflow DAG wiring만 소유하지 않는다. 같은 Spec 안에서 다음 동작도 명시적으로 요구한다.

- Reliability public boundary가 blocking policy를 판정해야 한다.
- `null_spike`와 `empty_partition`만 detector incident 중 pipeline을 차단해야 한다.
- Data Operations가 canonical dbt configuration을 강제해야 한다.
- analytics build 직전 mutation lock 안에서 전체 Bronze quality gate를 다시 검증해야 한다.

이 동작의 직접 executable evidence는 `tests/orchestration` 밖에 있다. `tests/reliability/test_quality_gate.py`는 blocking/non-blocking incident policy를 검증하고, `tests/data_operations/test_dbt_runner.py`는 canonical configuration과 lock-bound 재검증을 검증한다.

반면 orchestration execution test는 lower-domain API를 monkeypatch하는 경로가 있어, Reliability 또는 Data Operations의 실제 contract가 달라져도 adapter-level assertions만으로는 그 불일치를 검출할 수 없다.

예를 들어 canonical Spec에서 `volume_drop`을 blocking incident로 바꾸는 변경은 구조적으로 유효한 OpenSpec 변경일 수 있지만, 현재 routing은 `tests/orchestration`만 실행한다. 실제 구현이 여전히 `volume_drop`을 non-blocking으로 유지하는지는 `tests/reliability/test_quality_gate.py`가 검증하므로 현재 selector는 canonical contract와 implementation 사이의 false green을 허용할 수 있다.

#### Impact

이 PR의 핵심 목적 중 하나는 canonical Spec 변경을 affected executable validation에 연결해 contract drift를 merge 전에 잡는 것이다. `orchestration-pipeline`처럼 여러 domain의 public boundary를 직접 요구하는 Spec에서 owner test가 빠지면, selector 자체가 merge-critical evidence를 조용히 누락한다.

이는 전체 test를 항상 실행해야 한다는 의미는 아니다. 현재 repository CI 원칙대로 affected scope를 유지하되, **Spec이 실제로 소유하는 executable contract surface를 충분히 포함해야 한다.**

#### Action

최소 수정으로 `orchestration-pipeline` mapping을 다음 surface까지 확장한다.

- `tests/orchestration`
- `tests/data_operations`
- `tests/reliability`

그리고 `tests/test_ci_classifier.py`의 canonical Spec routing expectation을 갱신해 이 세 target이 유지되는 것을 회귀 테스트로 고정한다.

더 좁은 개별 test file 집합으로 같은 contract를 안정적으로 증명할 수 있다면 그 방식도 가능하다. 중요한 조건은 orchestration adapter뿐 아니라 Spec이 직접 요구하는 Data Operations와 Reliability behavior가 admission evidence에 포함되는 것이다.

### F2 · Current `main` Prospective-Merge Evidence Is Stale

#### Locations

- [PR #228](https://github.com/mols3131d/hmda-data-reliability/pull/228)
  - head `c64b8ac07acb24ed3a0eed1e18a1b488db467c07`
- [`docs/development/ci.md`](../../docs/development/ci.md)
  - `Admission Boundary`
- [CI Lite run `34344653108`](https://github.com/mols3131d/hmda-data-reliability/actions/runs/34344653108)
  - successful prospective-merge run against `main=1bb7a82dfd6548066dcac51a3b69aa34406b49cb`
- [Current `main` `dcc114a`](https://github.com/mols3131d/hmda-data-reliability/commit/dcc114ae75980a000624de992fee156d72c273bf)

#### Evidence

PR head는 여전히 `c64b8ac`이고 GitHub는 현재 PR을 mergeable로 계산한다. 하지만 head와 current `main` 비교는 `ahead 10 / behind 2`의 diverged 상태다.

현재 head의 성공한 CI Lite run `34344653108`은 merge commit `89b8b117198f5c6402e87a05ed3c9f0ed52f89fe`를 검사했으며, 그 merge commit의 base parent는 `1bb7a82dfd6548066dcac51a3b69aa34406b49cb`였다. 이후 `main`에는 PR #231과 #232가 들어와 현재 `dcc114ae75980a000624de992fee156d72c273bf`까지 진행했다.

Repository CI contract는 PR을 단독 head가 아니라 **현재 `main`과 합쳐질 상태**를 기준으로 검증하도록 요구한다. 따라서 과거 prospective-merge run의 성공을 현재 merge candidate의 evidence로 그대로 승격할 수 없다.

#### Impact

현재 `main`과 PR #228 사이에 충돌이 없다는 `mergeable=true`만으로 runtime/test compatibility가 증명되지는 않는다. 특히 이 PR은 CI selector와 admission workflow 자체를 변경하므로, 최신 base와 결합된 workflow가 실제로 성공하는 증거가 merge 판단에 직접 필요하다.

#### Action

F1 수정과 함께 최신 `main`을 topic branch에 반영한 뒤 CI Lite가 새 prospective merge에서 성공하는지 확인한다.

이 단계는 별도의 기능 변경을 요구하는 것이 아니라 현재 merge candidate에 대한 evidence refresh다. 새 CI가 성공하고 F1 regression이 포함되면 추가적인 broad redesign 없이 재리뷰할 수 있다.

## Resolved or Dropped Candidates

기존 review에서 지적된 `--all --strict`의 과도한 coupling은 현재 구현에서 해소된 것으로 본다. 일반 active Change와 known canonical Spec은 affected item validation을 사용하고, configuration/schema 또는 selector가 불확실한 경우에만 bulk `--all --strict`로 넓어진다. 현재 구조는 fail-safe fallback을 유지하면서 정상 경로의 scope coupling을 줄이므로 이 항목을 다시 finding으로 채택하지 않는다.

Dependency/runtime admission도 기존 finding을 닫는 방향으로 구현돼 있다. `.python-version`, `pyproject.toml`, `uv.lock` 변경은 lock/build/unit/type에 더해 dbt/DuckDB 및 Airflow boundary smoke를 선택한다. 이번 review에서는 이 경로에 새로운 material defect를 확인하지 못했다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | PR state and revision | PR #228은 open, ready, mergeable이며 head는 `c64b8ac`로 확인했다. |
| ✅ Pass | Classifier implementation review | known canonical Spec mapping, direct active Change pairing, bulk/archive fallback과 dependency runtime smoke routing을 직접 검토했다. |
| ✅ Pass | F1 contract-to-test ownership trace | `orchestration-pipeline` Spec의 Reliability/Data Operations 요구와 실제 `tests/reliability`, `tests/data_operations`, `tests/orchestration` 검증 위치를 대조했다. |
| ✅ Pass | Existing head CI evidence | CI Lite run `34344653108`은 성공했고 classifier regression `49 passed`, lock/build, Python validation과 Lefthook validation이 성공했다. |
| ❌ Fail | Current-base prospective merge evidence | 성공 run은 `main=1bb7a82` 기준이며 현재 `main=dcc114a`와 결합된 CI evidence는 없다. |
| ⚪ Not Verified | Independent dual-perspective orchestration | 현재 runtime에는 repository의 `review-lead` subagent orchestration이 없어 동일 컨텍스트 review methodology로 검토했다. |

## Risks and Limits

- PR #228 자체가 `openspec/**`를 변경하지 않아 기존 remote CI에서 새 `Validate OpenSpec` step은 실행되지 않고 skipped됐다. OpenSpec CLI 동작은 작업 기록의 local `20 passed, 0 failed` evidence를 참고했으며 이번 review에서 재실행하지 않았다.
- 이번 review는 PR #228이 도입하는 CI admission behavior와 merge readiness에 한정한다. Actual Airflow DAGRun proof, MVP E2E 또는 LLMOps live proof의 구현 상태는 판단 범위가 아니다.
- F1 수정 후 selector target이 바뀌므로 focused classifier regression과 최신 prospective-merge CI를 다시 확인해야 한다.
