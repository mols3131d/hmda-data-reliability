---
type: review
title: PR #228 CI Admission Review
description: PR #228의 OpenSpec admission과 dependency/runtime CI 보강을 변경 영향 범위, 실행 근거와 repository CI contract 관점에서 검토한 결과다.
tags:
  - "domain:software-engineering"
  - ci
  - openspec
  - pr-228
---

# PR #228 CI Admission Review

> [!IMPORTANT]
> **Revise** — OpenSpec structural admission과 dependency lock/build 검증은 유효한 개선이지만, canonical Spec 변경의 executable validation과 dependency 변경의 runtime-boundary smoke가 아직 닫히지 않았다. `openspec validate --all --strict`는 현재 규모에서 실행 비용은 작지만 일반 OpenSpec 변경에 항상 적용하기에는 영향 범위가 넓으므로 affected validation을 기본으로 하고 global 또는 불확실한 변경에서만 bulk validation을 쓰는 편이 repository CI 원칙에 더 맞다.

- **Target** — [PR #228](https://github.com/mols3131d/hmda-data-reliability/pull/228)
- **Revision** — `2b130e432423f7baf8b5ea80c8407ae52b9f0821`
- **Scope** — OpenSpec change classification과 validation gate, dependency/runtime admission, classifier regression tests, Lefthook 연계, PR metadata와 현재 CI evidence

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 **Major** | Canonical `openspec/specs/**` 변경이 OpenSpec 구조 검증까지만 연결되고 관련 executable validation을 선택하지 않는다. | Spec capability 변경을 최소 관련 project test에 fail-safe하게 매핑한다. |
| F2 | 🟠 **Major** | Dependency/runtime 변경은 lock, sync, wheel build, unit/type까지만 검증하며 실제 dbt/DuckDB/Airflow boundary smoke를 실행하지 않는다. | Dependency 변경에 작고 결정론적인 component/integration smoke set을 추가한다. |
| F3 | 🟡 **Minor** | 모든 `openspec/**` 변경에 `validate --all --strict`를 적용해 작은 변경도 모든 active change와 spec 상태에 결합된다. | 일반 change/spec은 affected item을 검증하고 config/schema 또는 영향 범위가 불명확할 때 bulk validation으로 넓힌다. |
| F4 | 🟡 **Minor** | PR 본문이 현재 head와 CI 상태보다 뒤처져 구현된 항목을 `(예정)`, CI를 `Not Verified`로 표시한다. | Ready 전 현재 head와 validation evidence에 맞게 PR 본문을 갱신한다. |

## Details

### F1 · Canonical Spec Changes Stop at Structural Validation

🟠 **Major**

#### Locations

- [`.github/workflows/classify_changes.sh`](../../.github/workflows/classify_changes.sh)
  - `openspec/*` classification
  - Markdown early `continue`
- [`tests/test_ci_classifier.py`](../../tests/test_ci_classifier.py)
  - `test_openspec_paths_trigger_openspec_validation`
- [`.github/workflows/ci-lite.yml`](../../.github/workflows/ci-lite.yml)
  - `Validate OpenSpec`
  - `Run selected tests`

#### Evidence

Classifier는 `openspec/specs/orchestration-pipeline/spec.md` 같은 canonical Spec 변경을 `openspec=true`로 분류하지만 Markdown 경로 처리 뒤 `continue`하므로 capability test routing에 도달하지 않는다. 새 regression test도 이 경로에서 `tests == "false"`를 명시적으로 기대한다. 따라서 CI는 OpenSpec artifact의 구조적 유효성은 확인하지만 변경된 capability contract와 현재 implementation/test가 같은 의미를 유지하는지는 검증하지 않는다.

#### Impact

구조적으로 유효한 Spec 변경이 기존 구현과 executable expectation을 뒤처지게 만들어도 OpenSpec admission만으로는 이를 검출할 수 없다. 이는 canonical contract 변경에 필요한 검증 근거가 path routing 때문에 빠질 수 있는 상태다.

#### Action

`openspec/specs/<capability>/...` 변경을 해당 capability의 최소 관련 project test에 연결한다. 정확한 영향을 안전하게 결정하기 어려운 경우에는 selector가 조용히 생략하지 말고 검증 범위를 넓혀야 한다.

### F2 · Dependency Changes Lack Runtime-Boundary Smoke

🟠 **Major**

#### Locations

- [`.github/workflows/classify_changes.sh`](../../.github/workflows/classify_changes.sh)
  - `.python-version|pyproject.toml|uv.lock`
  - `full_unit=true`, `full_type=true`
- [`.github/workflows/ci-lite.yml`](../../.github/workflows/ci-lite.yml)
  - `Verify dependency lock`
  - `Sync dependencies`
  - `Verify package build`
  - `Run selected tests`
- [`tests/dbt/test_analytics_foundation.py`](../../tests/dbt/test_analytics_foundation.py)
  - `test_dbt_build_creates_artifacts_lineage_and_idempotent_mart`
- [`tests/orchestration/test_airflow_dag.py`](../../tests/orchestration/test_airflow_dag.py)
  - Airflow DAG contract tests

#### Evidence

Dependency 관련 파일은 full unit/type 경로를 선택하고 `uv lock --check`, `uv sync --locked`, wheel build를 추가로 통과한다. 그러나 `FULL_UNIT=true`의 pytest 명령은 `unit` marker만 실행한다. 실제 DuckDB와 `dbt build`를 연결하는 검증 및 Airflow DAG import/contract 검증은 integration marker이므로 dependency-only 변경에서 제외된다.

#### Impact

Airflow, dbt, DuckDB 또는 다른 runtime dependency 변경이 설치·타입·unit·package build를 모두 통과하면서 실제 project boundary에서는 깨지는 회귀를 놓칠 수 있다.

#### Action

Dependency 변경에 전체 integration suite가 아니라 작은 smoke set을 연결한다. 예를 들어 현재 repository가 이미 보유한 dbt/DuckDB integration과 Airflow import/DAG contract처럼 dependency compatibility를 직접 증명하는 테스트만 선택하는 방식이 적합하다.

### F3 · `--all` Is Cheap but Broader Than the Affected Scope

🟡 **Minor**

#### Locations

- [`.github/workflows/ci-lite.yml`](../../.github/workflows/ci-lite.yml)
  - `npx --yes @fission-ai/openspec@1.12.0 validate --all --strict`
- [`inbox/2026-09-09/10-20-research-ci-openspec-admission.md`](10-20-research-ci-openspec-admission.md)
  - full validation latency measurement and selection rationale
- [`docs/development/ci.md`](../../docs/development/ci.md)
  - Change Impact
  - Admission Boundary

#### Evidence

OpenSpec CLI에서 `--all`은 모든 active change와 spec을 검증한다. 현재 repository에서는 약 20개 active item의 전체 검증이 약 1초 수준으로 측정되어 compute latency 자체는 작다. 따라서 이 finding의 핵심은 성능이 아니라 scope coupling이다. 일반 `openspec/changes/<name>/**` 한 건도 unrelated active spec/change 상태와 결합되어 실패할 수 있고, repository CI 원칙은 같은 신뢰를 얻을 수 있다면 affected scope를 exhaustive scope보다 우선하도록 한다.

#### Impact

현재 규모에서는 시간 비용이 거의 없지만 active change와 spec 수가 늘거나 병렬 작업이 증가하면 unrelated OpenSpec 상태가 작은 PR의 admission을 막는 운영 마찰이 생길 수 있다. 또한 failure attribution이 변경 대상보다 넓어진다.

#### Action

bulk validation을 제거할 필요는 없다. 다음과 같이 fail-safe fallback으로 유지하는 편이 적절하다.

1. `openspec/changes/<name>/**` → 해당 change를 `openspec validate <name> --type change --strict`로 검증한다.
1. `openspec/specs/<name>/**` → 해당 spec과 그 spec을 직접 수정하는 active change를 검증한다.
1. `openspec/config.yaml`, `openspec/schemas/**`, selector가 영향을 결정하지 못한 경우 → `--all --strict` 또는 필요한 bulk scope로 넓힌다.
1. `openspec/changes/archive/**` → 현재처럼 archived validation을 별도 취급한다.

현재 item 수와 latency만 보면 `--all`도 허용 가능한 단순한 초기 baseline이다. 다만 F1의 capability routing을 이번 PR에서 보강한다면 OpenSpec 구조 검증도 같은 impact selector에 맞추는 편이 장기 운영 비용과 실패 attribution 측면에서 더 일관된다.

### F4 · PR Body Is Stale

🟡 **Minor**

#### Locations

- [PR #228](https://github.com/mols3131d/hmda-data-reliability/pull/228)
  - `Changes`
  - `Validation`
- [`inbox/2026-09-09/11-05-plan-ci-admission-reinforcement-pr-228/tasks.md`](11-05-plan-ci-admission-reinforcement-pr-228/tasks.md)
  - completed implementation and verification checklist

#### Evidence

현재 head에는 classifier, regression tests, CI workflow, Lefthook 변경이 모두 포함되어 있고 CI Lite run 826도 성공했지만 PR 본문은 이 변경을 `(예정)`으로 표시하고 CI Lite를 `Not Verified`로 남겨두고 있다.

#### Impact

Reviewer가 구현 완료 범위와 실제 검증 상태를 잘못 해석할 수 있고, 남은 work와 완료된 work의 경계가 흐려진다.

#### Action

Ready 전 PR body의 `Changes`와 `Validation`을 현재 head와 CI run 기준으로 갱신한다. 새 `Validate OpenSpec` step은 이번 PR 자체에 `openspec/**` 변경이 없어 run 826에서 skipped였다는 점은 그대로 구분해 기록한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | PR scope and changed-file inspection | PR #228 head `2b130e4`의 9개 변경 파일과 patch를 검토했다. |
| ✅ Pass | Current prospective-merge CI status | CI Lite run 826이 head `2b130e4`에서 성공했다. |
| ✅ Pass | Classifier regression evidence | CI의 `Run selected tests`가 성공했고 PR 작업 기록은 `tests/test_ci_classifier.py` 44 passed를 기록한다. |
| ⚪ Not Verified | OpenSpec step execution on an OpenSpec-changing prospective merge | PR #228 자체는 `openspec/**`를 변경하지 않아 run 826의 `Validate OpenSpec` step은 skipped였다. |
| ⚪ Not Verified | Local repository validation after this review artifact write | 이 review 작성은 remote repository mutation으로 수행했으며 local checkout에서 `validate_inbox_artifacts.py`를 직접 실행하지 않았다. |

## Risks and Limits

- 이 review는 PR #228의 CI admission 변경에 한정하며 Actual Airflow DAGRun proof, current-revision MVP E2E, live LLM proof 자체는 검토 범위에 포함하지 않는다.
- 이 환경에는 repository가 권장하는 `review-lead` subagent orchestration이 없어 dual-perspective independent review는 수행하지 않았다.
- OpenSpec CLI의 현재 공식 문서는 `validate <item-name>`, `--all`, `--changes`, `--specs`, `--archived`를 별도 scope로 제공한다. 실제 PR 구현은 `@fission-ai/openspec@1.12.0`에 고정되어 있으므로 selector를 변경할 때는 해당 pinned version의 CLI behavior를 다시 확인해야 한다.
