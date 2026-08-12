---
name: pivot-spec-driven-tdd-rpi
description: >-
  Coordinate Research and Review feedback around OpenSpec's custom
  `spec-driven-tdd` workflow. Use when Research may inform an OpenSpec change,
  planning artifacts need revision, Apply entry must be checked, or Review
  findings must be routed back to their owning work.
compatibility: >-
  Requires OpenSpec with the custom `spec-driven-tdd` schema. No additional
  external skill, project document, repository convention, or standalone
  template is required by this skill.
metadata:
  version: "0.3.0"
---

# Spec-Driven TDD RPI

OpenSpec의 custom `spec-driven-tdd` workflow에 Research와 Review feedback을 연결한다.

이 skill의 외부 dependency는 **OpenSpec과 `spec-driven-tdd` schema뿐**이다. 나머지 orchestration 규칙은 이 skill 안에서 처리한다.

OpenSpec이 `spec-driven-tdd` contract를 제공하지 못하면 진행을 중단하고 incompatibility를 보고한다. 누락된 dependency를 자체 planning model, fallback contract 또는 추정 규칙으로 대체하지 않는다.

## Arguments

```yaml
entry: auto
change: auto
research: auto
feedback: auto
```

| Argument | `auto` 동작 |
| --- | --- |
| `entry` | 현재 요청과 상태에서 `research`, `planning`, `apply`, `review-feedback` 중 진입점을 선택한다. |
| `change` | 기존 OpenSpec change를 사용한다. Research-only 진입에는 change를 강제하지 않는다. |
| `research` | 현재 판단에 근거가 부족할 때만 필요한 범위로 조사한다. |
| `feedback` | 제공되었거나 현재 작업에서 확인된 Review finding만 처리한다. schema 상태를 대체하지 않는다. |

명시된 argument를 우선한다. 존재하지 않는 artifact, evidence 또는 validation 결과를 가정하지 않는다.

## Ownership

### OpenSpec + `spec-driven-tdd`

다음은 active schema contract가 소유한다.

- planning artifact의 종류와 책임
- artifact dependency와 `requires`
- artifact template과 작성 contract
- Apply gate, task tracking과 TDD execution contract

현재 schema contract가 이 skill의 설명보다 항상 우선한다. 이 skill은 위 규칙을 복제하거나 별도 planning model로 대체하지 않는다.

### This Skill

이 skill은 다음 orchestration만 소유한다.

- Research가 필요한지 판단하고 범위를 제한한다.
- 채택된 Research finding을 schema가 소유하는 planning artifact로 handoff한다.
- Review feedback을 원인과 변경 책임에 따라 owning work로 route한다.
- Research와 Review feedback evidence가 durable workflow dependency가 되지 않게 한다.
- 현재 entry의 다음 action 또는 blocker를 명확하게 전달한다.

## Entry Conditions

아래 조건은 entry routing을 위한 최소 조건이다. `spec-driven-tdd`가 소유하는 artifact 또는 Apply gate를 대체하지 않는다.

| Entry | Condition |
| --- | --- |
| `research` | 조사할 질문과 범위가 명확하다. OpenSpec change는 아직 없어도 된다. |
| `planning` | 대상 OpenSpec change가 `spec-driven-tdd`를 사용하며, 작성·수정할 artifact의 schema prerequisite를 충족한다. |
| `apply` | active `spec-driven-tdd` schema가 정의한 Apply contract를 충족한다. |
| `review-feedback` | finding, 근거와 영향을 받는 revision 또는 work surface를 식별할 수 있다. |

Research나 Review feedback evidence의 존재 자체를 planning 또는 Apply의 추가 gate로 만들지 않는다.

## Workflow

1. 요청된 entry와, 존재하는 경우 대상 OpenSpec change를 식별한다.
1. Planning 또는 Apply라면 OpenSpec에서 active `spec-driven-tdd` contract와 현재 artifact 상태를 확인한다.
1. 현재 판단에 필요한 근거가 부족할 때만 Research를 수행한다.
1. Research conclusion이 채택되면 schema의 artifact responsibility를 기준으로 owning planning artifact에 필요한 내용만 반영한다.
1. Planning artifact를 작성하거나 수정할 때는 OpenSpec과 active schema의 dependency와 contract를 그대로 따른다.
1. Planning 수정이 다른 artifact에 영향을 주면 schema dependency에 따라 다시 확인한다.
1. Apply 진입과 실행은 active schema의 Apply contract에 위임한다.
1. Review feedback이 있으면 아래 routing contract에 따라 처리하고 필요한 OpenSpec 상태를 다시 확인한다.
1. 요청된 entry가 완료되었거나 blocker가 명확하면 종료한다.

불필요한 Research, artifact 생성, Review 반복 또는 고정 phase pipeline을 추가하지 않는다.

## Research Handoff

Research는 기본적으로 transient evidence다. 별도 Research artifact, 저장 경로 또는 template을 이 skill이 요구하지 않는다.

- 기존 evidence로 충분하면 새 Research를 수행하지 않는다.
- Research 전체를 planning artifact에 복제하지 않는다.
- 채택된 conclusion, decision에 필요한 근거와 unresolved uncertainty만 owning artifact에 반영한다.
- Research가 변경 필요성을 만들지 못하면 OpenSpec change를 억지로 생성하지 않는다.
- Research evidence를 보존해야 한다면 저장 방식은 이 skill의 dependency나 gate가 아니다.

Owning artifact는 active schema의 artifact description, instruction과 dependency를 기준으로 결정한다.

## Review Feedback Routing

Review feedback은 독립적인 canonical authority가 아니다. finding을 검증한 뒤 다음과 같이 route한다.

| Finding | Route |
| --- | --- |
| Planning defect | 원인을 소유하는 `spec-driven-tdd` planning artifact를 수정하고 schema dependency에 따라 재검증한다. |
| Implementation 또는 test defect | 해당 implementation 또는 test surface를 수정하고 관련 validation을 다시 수행한다. |
| 새로운 요구사항 또는 현재 change 밖의 독립 범위 | 현재 change를 비대하게 만들지 않고 후속 OpenSpec change로 분리한다. |
| 현재 workflow가 소유하지 않는 concern | 억지로 artifact나 dependency를 만들지 않고 out-of-scope로 명시한다. |

같은 change와 후속 change는 finding 수가 아니라 기존 change의 의도와 범위 안에서 해결 가능한지로 구분한다.

## Transient Evidence

Research와 Review feedback evidence는 owning work로 handoff되기 전의 transient working evidence다.

- evidence 자체를 `spec-driven-tdd` artifact로 취급하지 않는다.
- handoff 후 Research나 Review feedback 원본이 없어도 OpenSpec workflow가 계속될 수 있어야 한다.
- schema artifact나 implementation에 필요한 결론이 transient evidence에만 남아 있지 않게 한다.
- Chat history나 숨은 추론을 durable dependency로 만들지 않는다.

## Handoff

필요할 때 다음 최소 상태만 전달한다. Handoff는 별도 artifact 생성 요구가 아니라 현재 호출의 출력 형식이다.

```markdown
## RPI Handoff

- Entry:
- Change: <id | not-applicable>
- Research: <used | transferred | not-required>
- Feedback: <resolved | findings | not-required>
- Next: <action | blocker | none>
```

확인한 상태만 기록한다. schema-owned gate 상태를 별도 상태로 복제하지 않는다. 실행하거나 검증하지 않은 결과를 사실처럼 보고하지 않는다.

## Completion

요청된 entry의 contract를 충족하고 다음 action 또는 blocker가 명확하면 완료한다.

Research나 Review feedback을 사용했다면 채택된 결론이 transient evidence에만 남아 있지 않아야 한다.

## Boundaries

- OpenSpec과 custom `spec-driven-tdd` schema 외의 dependency를 추가하지 않는다.
- 특정 repository path, project document, branch, VCS host, external template 또는 다른 skill을 요구하지 않는다.
- dependency가 없거나 해석되지 않을 때 schema contract를 자체 구현하거나 추정하지 않는다.
- `spec-driven-tdd`의 artifact model, dependency 또는 Apply contract를 재정의하지 않는다.
- Research나 Review feedback을 OpenSpec schema artifact로 추가하지 않는다.
- 별도의 Plan artifact나 competing workflow를 만들지 않는다.
- Research 또는 Review feedback 존재를 schema가 정의하지 않은 gate로 만들지 않는다.
- 새로운 finding이나 근거 없이 Review loop를 반복하지 않는다.
