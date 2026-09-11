---
type: research
title: PR #228 F1/F2 Remediation Research
description: 최신 PR revision과 main을 기준으로 OpenSpec executable routing gap을 최소 범위로 닫고 prospective-merge evidence를 갱신하기 위한 조사 결과다.
tags:
  - ci
  - openspec
  - pr-228
  - review-remediation
---

# PR #228 F1/F2 Remediation Research

> [!NOTE]
> F1은 유효하다. `orchestration-pipeline`의 직접 executable contract는 orchestration adapter에만 있지 않고 Data Operations와 Reliability에도 있다. 세 domain 전체 directory보다 reviewer가 지정한 exact file set을 admission target으로 추가하는 편이 같은 contract evidence를 더 작은 범위로 보존한다. F2는 최신 `main`을 local candidate에 반영했지만, push 후 새 prospective-merge CI가 아직 필요하다.

## Question

PR #228의 최신 review에서 남은 F1 executable routing gap과 F2 stale prospective-merge evidence를, repository CI contract를 훼손하지 않는 최소 변경으로 닫을 수 있는가?

## Scope

- PR #228 remote head `4bca22830f2ad0693c5d3b9d2079a0b8e612683c`
- latest `origin/main` `6ef4e642f1cbe477ff1a1967f514649d2aae4772`
- historical review artifact의 F1/F2와 현재 source/test surface 대조
- `.github/workflows/classify_changes.sh`와 `tests/scripts/test_ci_classifier.py`의 canonical Spec routing
- F1에 직접 대응하는 executable test collection 범위

### Out of Scope

- orchestration, Data Operations 또는 Reliability business behavior 변경
- OpenSpec CLI 내부 변경
- PR approval, Ready 전환 또는 merge
- unrelated test suite 최적화

## Findings

### F1 remains a current routing gap

`orchestration-pipeline` Spec은 ordered Airflow execution뿐 아니라 domain delegation, canonical dbt source/configuration, lock-bound quality-gated build, structural validation과 blocking incident policy까지 요구한다. 현재 classifier의 `orchestration-pipeline)` mapping은 `tests/orchestration`만 추가한다.

#### Evidence

- [`openspec/specs/orchestration-pipeline/spec.md`](../../openspec/specs/orchestration-pipeline/spec.md)
  - `Domain delegation`은 Data Operations와 Reliability public boundary 위임을 요구한다.
  - `Data quality gate execution`은 canonical source/partition, lock 재검증, bundled dbt configuration과 blocking scope를 요구한다.
- [`tests/orchestration/`](../../tests/orchestration/)
  - DAG ordering, task state, adapter delegation과 Airflow error boundary를 검증한다.
- [`tests/data_operations/test_quality_gate.py`](../../tests/data_operations/test_quality_gate.py)
  - 전체 Bronze population, canonical source/partition, absent/null partition과 Airflow 비의존 composition을 검증한다.
- [`tests/data_operations/test_dbt_runner.py`](../../tests/data_operations/test_dbt_runner.py)
  - lock-bound gate 재검증, process ordering과 canonical dbt project/profile configuration을 검증한다.
- [`tests/reliability/test_quality_gate.py`](../../tests/reliability/test_quality_gate.py)
  - `null_spike`·`empty_partition` blocking과 `volume_drop`·`schema_drift`·`freshness_delay` non-blocking policy, profile coverage를 검증한다.
- [`inbox/2026-09-10/11-32-review-software-engineering-ci-pr-228-merge-readiness.md`](../2026-09-10/11-32-review-software-engineering-ci-pr-228-merge-readiness.md)
  - F1의 동일한 contract-to-test ownership gap을 Major finding으로 기록한다.

### Exact-file routing is sufficient and materially narrower

Read-only collection 결과는 다음과 같다.

| Candidate | Collected tests | Assessment |
| --- | ---: | --- |
| `tests/orchestration tests/data_operations tests/reliability` | 262 | F1보다 넓으며 reliability recovery/e2e와 전체 data operation surface까지 포함한다. |
| `tests/orchestration tests/data_operations/test_quality_gate.py tests/data_operations/test_dbt_runner.py tests/reliability/test_quality_gate.py` | 74 | F1 review가 지목한 orchestration, canonical/lock-bound Data Operations와 blocking Reliability contract를 모두 포함한다. |

`add_focused_test`는 directory뿐 아니라 existing test file path도 target과 type target으로 보존하고, 네 target은 CI의 `>=3` 병렬 실행 경로를 사용한다. 따라서 exact-file set은 selector의 affected-scope 원칙과 F1의 owner coverage 조건을 동시에 만족한다.

### F2 requires refreshed remote evidence

PR review가 기록한 성공 CI는 과거 `main=1bb7a82` 기준이었다. 현재 `main`은 `6ef4e64`이며 PR remote head는 `4bca228`이다. local branch에는 `4bca228`를 fast-forward한 뒤 `origin/main`을 merge해 candidate `76b5862`를 만들었다. 이 candidate를 push하고, GitHub가 생성한 새 prospective-merge CI run의 head/base evidence를 확인해야 F2를 닫을 수 있다.

## Decision

F1은 `orchestration-pipeline)` mapping에 다음 exact targets를 추가하는 방식으로 수정한다.

- `tests/orchestration`
- `tests/data_operations/test_quality_gate.py`
- `tests/data_operations/test_dbt_runner.py`
- `tests/reliability/test_quality_gate.py`

`tests/scripts/test_ci_classifier.py`의 canonical Spec regression expected set도 같은 네 target으로 갱신한다. F2는 최신 `main` merge commit을 포함한 PR update와 새 CI evidence로 검증한다.

## Open Questions

- push 후 생성될 prospective-merge CI가 최신 `main=6ef4e64`와 candidate를 실제로 검증하는지 확인해야 한다.
- 새 CI에서 selector, OpenSpec validation, dependency/runtime smoke 또는 focused tests가 실패하면 그 실패 지점부터 다음 loop를 시작한다.
