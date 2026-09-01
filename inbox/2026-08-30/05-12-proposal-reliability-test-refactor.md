---
type: proposal
title: Refactor Reliability Tests Around Semantic Failure Stages
description: 호출 순서와 예외 타입에 결합된 reliability 테스트를 의미 기반 fault injection과 명확한 failure oracle 중심으로 정리하는 제안서.
status: draft
tags:
  - reliability
  - testing
  - refactor
  - test-oracle
---

# Refactor Reliability Tests Around Semantic Failure Stages

> [!NOTE]
> `tests/reliability`의 긴 파일을 줄이는 것 자체가 목표는 아니다. 우선 `test_null_spike_evaluation.py`와 `test_approval_backfill_validation.py`에서 호출 횟수로 실행 단계를 식별하고, `ValueError` 타입만으로 path validation을 확인하는 부분을 의미 기반 oracle로 바꾼다. 파일 분할은 이 작업 뒤에도 읽기 흐름이 개선되지 않을 때만 ownership 기준으로 재평가한다.

## Decision Summary

| Decision | Rationale | Not Decided Here |
| --- | --- | --- |
| preflight path rejection은 direct exception contract로 검증한다 | evaluator는 workspace 생성 전 path 존재와 alias를 직접 검사한다 | production error type 또는 message 변경 |
| target overwrite fault는 request 의미로 선택한다 | staged candidate load와 target replacement는 `expected_identity` 유무로 구분된다 | 모든 counter의 일괄 제거 |
| replay처럼 동일 입력이 반복되는 경우에는 order를 명시적으로 검증한다 | 일부 invocation은 인자만으로 first recovery와 replay를 구분할 수 없다 | replay contract를 새 public API로 노출 |
| 파일 분할은 마지막에 판단한다 | 현재 문제의 중심은 line count가 아니라 oracle 정확도다 | helper의 전역 통합 |

## Problem

현재 reliability 테스트는 여러 recovery와 replay 시나리오를 폭넓게 보증하지만, 일부 하네스가 production 내부 호출 순서에 의존한다.

- `snapshot_count == 2`, `lifecycle_count == 3`, `load_count == 2` 같은 ordinal counter가 특정 실행 단계를 선택한다.
- alias 또는 기존 database 거부 테스트가 `ValueError`의 message와 발생 경계를 확인하지 않는다.
- 일부 failure 테스트는 구조화된 failure result의 일부 field만 확인하므로 원래 실패 원인과 runtime evidence가 충분히 보존됐는지 테스트마다 일관되지 않다.

이 문제는 파일 길이보다 더 중요하다. 내부 call graph가 바뀌면 실제 contract 변화 없이 테스트가 깨질 수 있고, 잘못된 호출에서 fault가 발생해도 테스트가 통과할 가능성이 있다. 반대로 replay처럼 시간 순서 자체가 contract인 경우에는 counter를 없애는 것이 아니라, 어떤 순서가 왜 필요한지 test oracle에 남겨야 한다.

## Scope

### In Scope

- `tests/reliability/test_null_spike_evaluation.py`
- `tests/reliability/test_approval_backfill_validation.py`
- 직접 영향을 받는 reliability fixture 또는 test-only helper
- 해당 테스트의 focused validation과 관련 package suite

### Out Of Scope

- production source 변경
- reliability contract 또는 approval policy 변경
- 테스트 assertion 완화
- 단순 line-count 감소를 위한 무조건적인 파일 분할
- `conftest.py`로 scenario-specific helper를 기계적으로 승격

## Goals

1. fault injection이 호출 순서가 아니라 실행 단계의 의미를 기준으로 동작하게 한다.
1. path validation 테스트가 기대한 exception boundary와 message를 직접 검증하게 한다.
1. failure result가 보존해야 하는 runtime evidence를 scenario별로 명확히 드러낸다.
1. 테스트가 production algorithm을 재구현하지 않으면서도 false green 위험을 줄인다.
1. 기존 observable behavior와 테스트 level을 유지한다.

## Non-goals

- 모든 helper를 하나의 공통 factory로 통합하지 않는다.
- 긴 테스트 파일을 길이만으로 나누지 않는다.
- 모든 테스트에 동일한 assertion helper를 강제하지 않는다.
- 새로운 mocking framework나 observability dependency를 도입하지 않는다.

## Evidence

### Finding 1. Ordinal fault injection

`test_null_spike_evaluation.py`의 recovery/replay 관련 테스트와 `test_approval_backfill_validation.py`의 race 테스트는 호출 횟수로 fault 발생 위치를 추론한다. 호출 인자, 대상 database, partition identity 또는 recovery state가 실제로 단계를 구별할 때에만 더 안정적인 식별자가 된다. recovery와 replay가 동일 hook input을 반복하면 outer approved execution 순서와 inner call journal을 함께 사용해야 한다.

### Finding 2. Weak exception oracle

alias 및 existing database 거부 테스트는 `ValueError`를 catch한 뒤 side effect 부재를 확인하지만, validation failure의 message나 context를 직접 확인하지 않는 경로가 있다. 이 경우 이후 단계의 다른 `ValueError`가 원래 실패로 오인될 수 있다.

### Finding 3. Inconsistent failure evidence

failure stage와 mutation state는 여러 테스트에서 확인되지만, failure reason 또는 evidence context의 확인 범위가 시나리오마다 다르다. 모든 정보를 공통 helper에 숨기기보다, 각 테스트가 보증하는 핵심 evidence를 직접 명시해야 한다.

## Verified Execution Boundaries

현재 production code를 읽어 확인한 경계다. 제안된 테스트 리팩터링은 이 경계를 바꾸지 않고, 각 경계의 observable result를 더 정확히 확인한다.

| Boundary | Current Behavior | Test Consequence |
| --- | --- | --- |
| evaluation database preflight | `_ensure_disposable_database_paths()`가 workspace 생성 전에 existing path와 symlink를 거부한다 | existing path와 dangling symlink는 `새 path여야 합니다` 오류와 side-effect 부재를 함께 검증한다 |
| evaluation database alias preflight | existing path와 symlink를 먼저 거부한 뒤, request database path가 evaluator의 internal clean 또는 candidate path와 같으면 거부한다 | externally controllable target-clean 및 target-candidate alias는 `서로 달라야 합니다` 오류와 side-effect 부재를 함께 검증한다. dangling symlink는 existing-path family로 유지한다 |
| approved candidate staging | `_stage_approved_candidate_source()`는 temporary Parquet를 만든 뒤 candidate identity를 확인한다 | candidate staging과 target replacement를 같은 `load_hmda_loans_partition()` 호출로 오인하지 않는다 |
| target overwrite | `_replace_approved_partition()`은 staged source와 non-null `expected_identity`를 사용한다 | stale race fault는 target replacement invocation에만 주입한다 |
| replay | same approval로 recovery executor를 다시 호출해 verification을 재개하며 두 executor invocation은 동일 request input을 가질 수 있다 | hook input에 없는 phase label을 만들지 않고, outer approved execution의 순서와 inner call journal으로 replay를 식별한다 |

## Failure Contract Matrix

| Contract Family | Observable Outcome | Required Oracle |
| --- | --- | --- |
| preflight rejection | direct `ValueError`, workspace와 external boundary 미진입 | exact message fragment, no database/load/callback call, source and artifact preservation |
| pre-target recovery rejection | structured result 또는 typed recovery gate failure, target mutation 없음 | `failure_stage="before_target_mutation"`, `target_mutated=False`, required reconciliation action |
| post-target recoverable failure | structured evidence가 completed mutation을 보존 | `failure_stage="after_partition_mutation"`, mutation evidence, reconciliation action, relevant error evidence |
| replay failure | first recovery evidence는 유지하고 replay outcome만 분리 | recovery/replay presence, replay mutation state 또는 failure case, reconciliation action |

이 표는 테스트마다 모든 field를 assertion하라는 규칙이 아니다. 각 scenario는 자기 contract를 식별하는 최소 evidence만 확인한다.

## Design Direction

```text
scenario input
    -> semantic fault selector
    -> target execution stage
    -> typed failure/result
    -> stage and evidence assertions
```

### Selector Policy

| Selector Type | Use When | Required Proof |
| --- | --- | --- |
| semantic selector | request, source path, `expected_identity`, database path 또는 observed target state로 stage를 구분할 수 있을 때 | fault를 받은 invocation의 relevant attributes와 targeted call count |
| explicit sequence selector | first recovery와 replay처럼 동일 argument가 반복되고 sequence가 contract일 때 | outer execution journal, active execution에 귀속된 inner call journal, expected sequence length, fault가 발생한 ordinal의 domain meaning |
| no selector | direct preflight validation처럼 external boundary에 도달하면 안 될 때 | `pytest.raises(..., match=...)`와 side-effect sentinel |

권장 원칙:

- target overwrite fault는 `expected_identity`와 staged candidate source 같은 의미 있는 입력을 우선 사용한다.
- sequence가 불가피한 replay test는 counter를 숨기지 않고 replay가 second approved execution이어야 하는 이유를 outer execution journal에 남긴다. inner hook은 활성 execution에 귀속하고, hook input에서 얻을 수 없는 phase label을 합성하지 않는다.
- post-recovery lifecycle fault는 target request만으로 구분하지 않고, observed target identity가 recovered state임을 journal에 남긴 뒤에만 주입한다.
- path rejection은 `pytest.raises(..., match=...)`와 side-effect 부재 검증을 결합한다. evaluator가 internal clean/candidate path를 고정 생성하면 request input으로 제어 가능한 target alias만 direct alias branch로 검증하고, internal path pair는 public test surface로 가장하지 않는다.
- failure evidence assertion은 scenario의 핵심 contract를 테스트 본문에 남긴다.

## Acceptance Criteria

- path preflight tests가 direct `ValueError`의 family-specific message와 boundary 미진입을 확인한다.
- stale target replacement test가 candidate staging이 아닌 target overwrite invocation에만 fault를 주입했음을 보인다.
- replay tests가 counter를 쓴다면 replay sequence의 의미와 fault 위치를 outer approved execution 및 inner call journal으로 확인한다.
- post-recovery lifecycle fault가 defect lifecycle이 아닌 recovered target identity에만 발생했음을 보인다.
- post-mutation failure tests가 mutation evidence와 reconciliation action을 보존한다.
- 기존 test의 observable contract, marker와 side-effect 보호가 유지된다.
- focused test와 관련 reliability suite가 통과한다.
- 파일 분할은 ownership, fixture, execution flow가 실제로 분리되는 경우에만 채택되며, 근거가 없으면 현재 파일 경계를 유지한다.

## Decision

이 제안은 `test_null_spike_evaluation.py`와 `test_approval_backfill_validation.py`의 테스트 oracle을 먼저 개선하는 방향을 채택한다. preflight path rejection은 exception contract로, target overwrite race는 semantic selector로, replay처럼 semantic input만으로 구분되지 않는 시나리오는 explicit sequence selector로 다룬다. 파일 분할과 공통 helper 통합은 후속 판단으로 남긴다.

## Constraints And Open Questions

- 이 작업은 test-only refactor다. 안정적인 stage identifier를 production code가 노출하지 않는 경우, public contract 변경으로 확대하지 않고 test-local call journal을 우선 사용한다. 단, hook input에 없는 phase label을 test-local state로 가장해 새 semantic selector라고 부르지 않는다.
- `test_null_spike_evaluation.py`의 모든 counter가 결함은 아니다. 각 counter가 fault injection인지, 결과 관찰인지, replay sequence 계약인지 먼저 분류한다.
- `conftest.py` 승격은 여러 파일이 같은 fixture contract와 lifecycle을 공유한다는 증거가 생길 때만 검토한다.

## Next Step

계획서의 Phase 0에서 current selector를 inventory한 뒤, 다음 pilot을 우선 전환한다.

1. `test_null_spike_vertical_slice_rejects_existing_evaluation_database`
1. `test_null_spike_vertical_slice_rejects_aliased_evaluation_database_paths`
1. `test_recovery_classifies_compare_and_replace_race_as_stale_approval`

그 다음에 replay profile failure와 post-recovery lifecycle failure를 semantic selector 또는 explicit sequence selector 중 어느 방식으로 유지할지 판단한다.
