---
title: Data Operations Change Gates and Delivery Plan
description: 반복 심층 리뷰를 줄이기 위한 변경 분류, validation gate와 contract-first 전달 순서를 제안한다.
tags:
  - data-operations
  - change-gate
  - delivery-plan
  - review-policy
---

# Change Gates And Delivery

## Principle

심층 리뷰는 모든 변경에 반복 적용하는 기본 절차가 아니라, **새로운 판단이 필요한 변경을 탐지했을 때 사용하는 비용 높은 검증**이어야 한다.

Test가 통과했다는 사실만으로 안전을 단정하지 않는다. 대신 변경이 기존 contract 안에 머무는지, contract 자체를 바꾸는지를 먼저 분류한다.

## Change Classes

### Class A — Contract-preserving implementation

예:

- helper 추출
- exception message 정리
- 내부 중복 제거
- 같은 result를 만드는 query/refactor

Gate:

- affected focused test
- `tests/data_operations`
- lint/format when applicable
- light diff review

심층 domain review는 필요하지 않다.

### Class B — Known boundary risk

예:

- 새 dependency exception 처리
- artifact path handling 수정
- result field 추가지만 기존 의미 유지
- metadata mapping 변경

Gate:

- 해당 contract matrix scenario
- domain suite
- 직접 caller 또는 orchestration targeted suite
- finding 중심 targeted review

전체 architecture를 다시 검토하지 않는다.

### Class C — Contract or architecture change

예:

- public request/result 의미 변경
- stage 추가·삭제
- Dagster asset graph 또는 ownership 변경
- lifecycle에 write/recovery/evaluation 연결
- file-count 의미나 skip policy 변경

Gate:

- OpenSpec 또는 canonical contract 결정
- red/characterization test와 independent oracle
- affected domain + integration suite
- deep review

## Trigger Table

| Changed area | Default class | Escalate when |
| --- | --- | --- |
| private helper | A | persisted state, ordering, exception type이 달라짐 |
| result serialization | B | field meaning 또는 compatibility가 달라짐 |
| request field | C | 단순 validation constraint 보강만이면 B 가능 |
| dbt command construction | B | output contract나 execution ownership 변경 시 C |
| error mapping | B | caller-visible taxonomy 정책 변경 시 C |
| Dagster metadata | B | materialization 의미나 asset graph 변경 시 C |
| lifecycle sequence | C | pure internal extraction이면 A |
| docs only | A | canonical behavior를 새로 정의하면 C |

## Delivery Sequence

### Decision 1 — dbt artifact source of truth

추천:

- `dbt_target_path` 하나를 source of truth로 둔다.
- manifest와 run-results path는 target path에서 파생한다.
- command에 `--target-path`를 전달한다.

Alternative:

- 개별 artifact path configuration을 제거하고 dbt project default target만 지원한다.

독립적인 두 path를 유지하면서 dbt output과 사후 검증만 연결하는 방식은 불필요한 invalid state를 허용하므로 피한다.

### Decision 2 — Standard pipeline skip semantics

추천:

- standard `pipeline_job`은 raw와 dbt를 항상 실행한다.
- raw-only 실행은 Dagster asset selection 또는 named raw-only job으로 표현한다.
- 실행하지 않은 dbt asset에는 materialization event를 기록하지 않는다.
- `run_dbt_build`를 `DataOperationRequest`에서 제거한다.

### Decision 3 — Error boundary policy

추천:

- public entry point는 예상 가능한 domain/application failure를 `DataOperationError`로 변환한다.
- `raise ... from exc`로 cause를 유지한다.
- 필요한 safe context는 `DataOperationError`의 structured field 또는 message에 제한적으로 보존한다.
- `TypeError`, assertion, programming error는 broad wrapping하지 않는다.

### Decision 4 — Result semantics

추천:

- evidence/result collection은 tuple로 deep immutable하게 만든다.
- file count는 이름에 의미를 드러낸다.
- 운영상 필요한 값이 discovered와 contributing 둘 다라면 두 field로 분리한다.

## Proposed Work Units

### Change A — dbt execution contract

Scope:

- artifact source-of-truth decision
- fake executable harness
- custom target regression test
- runner fix
- existing timeout/stale test 보존

독립적으로 검토하고 되돌릴 수 있다.

### Change B — application error boundary

Scope:

- wrapping 대상 exception taxonomy 결정
- raw/lifecycle translation matrix tests
- context와 cause preservation
- broad wrapping negative test

### Change C — orchestration truthfulness

Scope:

- standard pipeline skip policy 결정
- raw-only execution path
- no false materialization integration test
- orchestration-only config 분리

### Change D — result and metadata semantics

Scope:

- file count 의미
- deep immutable collections
- result와 Dagster metadata regression tests

각 change는 별도 branch와 Draft PR이 적합하다. 하나의 branch에서 모두 고치면 contract decision과 mechanical fix가 섞여 리뷰 비용이 다시 커진다.

## Review Retirement

현재 `reviews/data-operations-domain-review.md`의 finding이 다음 위치로 이전되면 review artifact는 목적을 다한다.

| Finding | Durable destination |
| --- | --- |
| artifact path | OpenSpec/domain contract + component test |
| error boundary | domain contract + exception matrix tests |
| skip materialization | orchestration spec + integration test |
| file count | result contract + component/integration test |
| immutability | result model contract + unit test |

모든 finding을 test만으로 이전할 수는 없다. 의미 결정은 canonical spec/document가 소유하고, test는 그 결정을 executable하게 보호한다.

## Completion Gate

첫 foundation cycle 완료 조건:

- 네 가지 decision이 명시적으로 해결되었다.
- P1 risk에 red 또는 characterization test가 있다.
- fix는 focused tests를 통과한다.
- `tests/data_operations`와 affected orchestration suite가 통과한다.
- validation을 실행하지 않은 환경에서는 통과를 주장하지 않는다.
- 남은 deep review 대상이 새 contract와 architecture decision으로 제한된다.

## Expected Review Policy Afterward

```text
contract unchanged + focused tests pass
→ light review

known boundary changed + contract tests pass
→ targeted review

contract/spec/architecture changed
→ deep review
```

이 정책은 review quality를 낮추지 않는다. 반복 가능한 판단을 automation으로 내리고, 인간의 추론을 모호성과 새로운 위험에 집중시킨다.
