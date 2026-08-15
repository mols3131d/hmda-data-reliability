---
name: pivot-spec-driven-tdd-rpi
description: >-
  Route Research evidence and Review feedback into OpenSpec's custom
  `spec-driven-tdd` workflow. Use when Research may determine or revise an
  OpenSpec change, or Review findings must be routed back to their owning work.
  Do not use for ordinary schema-owned planning or Apply execution without
  Research or Review input.
compatibility: >-
  Requires OpenSpec with the custom `spec-driven-tdd` schema. No additional
  skill, project document, repository convention, or standalone template is a
  dependency of this skill. Applicable host-project instructions still apply as
  ambient constraints.
metadata:
  version: "0.3.0"
---

# Spec-Driven TDD RPI

OpenSpec의 custom `spec-driven-tdd` workflow에 Research와 Review feedback을 연결한다.

Host project의 적용 가능한 지침은 따르되 특정 문서, 경로 또는 convention을 이 skill의 dependency로 고정하지 않는다. `spec-driven-tdd` contract를 확인할 수 없으면 중단하고 incompatibility를 보고하며, 누락된 contract를 자체 planning model이나 추정 규칙으로 대체하지 않는다.

## Arguments

```yaml
entry: auto
change: auto
research: auto
feedback: auto
```

| Argument | `auto` 동작 |
| --- | --- |
| `entry` | 현재 요청과 확인된 상태에서 `research`, `planning`, `apply`, `review-feedback` 중 진입점을 선택한다. |
| `change` | 명확히 하나로 식별되는 기존 OpenSpec change를 사용한다. Research-only 진입에는 change를 강제하지 않는다. |
| `research` | 현재 판단에 근거가 부족할 때만 필요한 범위로 조사한다. |
| `feedback` | 제공되었거나 현재 작업에서 확인된 Review finding만 처리한다. |

명시된 argument를 우선한다. `auto`는 확인된 상태에서 하나의 안전한 선택으로 수렴할 때만 해석한다. 여러 후보가 실질적으로 가능하면 임의로 선택하지 않고 필요한 식별 정보나 blocker를 보고한다. 존재하지 않는 artifact, evidence 또는 validation 결과를 가정하지 않는다.

## Authority And Scope

| Owner | Responsibility |
| --- | --- |
| OpenSpec + `spec-driven-tdd` | planning artifact 종류·책임·dependency·template, Apply gate, task tracking과 TDD execution contract |
| Host project | 현재 작업에 적용되는 repository, domain, validation과 운영 제약 |
| This skill | Research 필요성 판단과 handoff, Review feedback routing, entry transition과 blocker 전달 |

Active schema contract가 이 skill의 설명보다 우선한다. Host-project 지침은 ambient constraint이지 이 skill의 고정 dependency가 아니다.

이 skill은 schema-owned artifact model이나 Apply contract를 복제하지 않고, Research 또는 Review feedback을 새로운 OpenSpec artifact나 추가 gate로 만들지 않는다.

## Workflow

1. 요청된 entry와 확인 가능한 대상 change를 식별한다. Research-only에는 change가 없어도 된다.
1. Planning 또는 Apply라면 active `spec-driven-tdd` contract와 현재 artifact 상태를 확인하고 schema prerequisite를 따른다.
1. 현재 판단에 필요한 근거가 부족할 때만 Research를 수행한다.
1. Research가 OpenSpec change가 필요한 근거를 제공하면 기존 change를 명확히 식별하거나, 허용된 경우 OpenSpec을 통해 새 change를 준비한 뒤 planning으로 전이한다. 필요한 식별 정보나 권한이 없으면 임의로 만들지 않고 next action 또는 blocker를 반환한다.
1. OpenSpec 작업에 채택된 Research conclusion은 schema responsibility에 따라 owning planning artifact에 필요한 내용만 반영한다.
1. Planning artifact 수정이 downstream artifact에 영향을 주면 schema dependency에 따라 다시 일치시킨다.
1. Apply 진입과 실행은 active schema의 Apply contract에 위임한다.
1. Review feedback은 finding, 근거와 영향을 받는 work surface를 확인한 뒤 아래 routing contract에 따라 처리한다.
1. 요청된 entry가 완료되었거나 blocker가 명확하면 종료한다.

불필요한 Research, artifact 생성, Review 반복 또는 고정 phase pipeline을 추가하지 않는다.

## Research Evidence

Research는 기본적으로 transient evidence다. 이 skill은 별도 Research artifact, 저장 경로 또는 template을 요구하지 않는다.

- 기존 evidence로 충분하면 새 Research를 수행하지 않는다.
- OpenSpec 작업에 채택된 conclusion, 필요한 근거와 unresolved uncertainty만 owning artifact에 반영한다.
- Research 전체를 planning artifact에 복제하거나 변경 필요성이 없는데 change를 만들지 않는다.
- Handoff 후 owning work가 원본 Research, Chat history 또는 숨은 추론에 의존하지 않게 한다.

Owning artifact는 active schema의 responsibility와 dependency를 기준으로 결정한다.

## Review Feedback Routing

Review feedback은 독립적인 canonical authority가 아니다. finding을 검증한 뒤 원인을 소유하는 work로 route한다.

| Finding | Route |
| --- | --- |
| Planning defect | 원인을 소유하는 planning artifact를 수정하고 schema dependency에 따라 재검증한다. |
| Implementation 또는 test defect | 해당 implementation 또는 test work로 route하고 필요한 validation을 다시 요구한다. |
| 새로운 요구사항 또는 현재 change 밖의 독립 범위 | 현재 change를 비대하게 만들지 않고 후속 OpenSpec change로 분리한다. |
| 현재 workflow가 소유하지 않는 concern | artifact나 dependency를 만들지 않고 out-of-scope로 명시한다. |

같은 change와 후속 change는 finding 수가 아니라 기존 change의 의도와 범위 안에서 해결 가능한지로 구분한다.

## Handoff

필요할 때 다음 최소 상태만 전달한다. Handoff는 별도 artifact가 아니라 현재 호출의 출력 형식이다.

```markdown
## RPI Handoff

- Entry:
- Change: <id | not-applicable | unresolved>
- Research: <used | not-required>
- Feedback: <handled | blocked | not-required>
- Next: <action | blocker | none>
```

확인한 상태만 기록한다. Planning에 채택된 Research 또는 Review 결론은 owning artifact에 반영하거나 `Next`에 미완료 handoff를 명시한다. 다른 Review finding은 owning work로 route한 상태와 필요한 next action을 기록한다. schema-owned gate 상태를 별도 상태로 복제하지 않으며 실행하거나 검증하지 않은 결과를 사실처럼 보고하지 않는다.

## Completion

요청된 entry의 contract를 충족하고 다음 action 또는 blocker가 명확하면 완료한다. Planning에 채택된 Research 또는 Review 결론은 transient evidence에만 남기지 않으며, 다른 Review finding은 owning work로 route한다. 새로운 finding이나 근거 없이 Review loop를 반복하지 않는다.
