---
name: pivot-spec-driven-tdd-rpi
description: >-
  Coordinate evidence, spec-driven planning, TDD execution, and review as a
  self-contained workflow. Use when a change needs Research before planning,
  planning artifacts need revision, implementation should enter through a plan
  gate, or Review findings must be routed back to the work that owns them.
metadata:
  version: "0.3.0"
---

# Spec-Driven TDD RPI

Research, planning, implementation, and Review를 하나의 자족적인 spec-driven TDD workflow로 연결한다.

이 skill은 자신의 핵심 동작을 설명하기 위해 외부 schema, guideline, template, 다른 skill 또는 특정 repository 구조를 요구하지 않는다.

## Arguments

```yaml
entry: auto
target: auto
artifacts: auto
research: auto
review: auto
```

| Argument | `auto` 동작 |
| --- | --- |
| `entry` | 요청과 현재 상태에서 `research`, `planning`, `apply`, `review-feedback` 중 필요한 진입점을 선택한다. |
| `target` | 변경 대상이나 현재 작업 범위를 식별한다. Research-only 작업에는 change target을 강제하지 않는다. |
| `artifacts` | 기존 planning artifact가 있으면 semantic role로 매핑하고, 없으면 현재 작업에 필요한 role만 사용한다. |
| `research` | 현재 판단에 근거가 부족할 때만 필요한 범위로 조사한다. |
| `review` | 제공된 Review finding이나 현재 작업에서 확인된 finding만 사용한다. |

명시된 argument를 우선한다. 없는 artifact, evidence 또는 validation 결과를 가정하지 않는다.

## Capsule Contract

- 이 skill의 workflow, gate, artifact responsibility와 finding routing은 이 파일이 소유한다.
- 특정 repository path, branch, 문서 이름 또는 외부 workflow 존재를 전제로 하지 않는다.
- 기존 artifact가 있으면 이름이 아니라 아래 semantic role에 매핑한다.
- Research와 Review evidence는 기본적으로 transient input이다. 별도 artifact 생성을 workflow의 필수 조건으로 만들지 않는다.
- 채택된 결정과 요구사항은 transient evidence가 아니라 해당 planning 또는 implementation surface에 남아야 한다.
- Entry는 과거 phase 실행 이력이 아니라 현재 필요한 작업과 준비 상태로 결정한다.

## Planning Model

Planning은 다섯 semantic role로 구성한다. 실제 파일명과 저장 위치는 중요하지 않다.

| Role | Responsibility | Ready when |
| --- | --- | --- |
| `intent` | 변경 목적, 범위, 영향 | 행동 계약을 정의할 만큼 목적과 경계가 명확하다. |
| `behavior` | 관찰 가능하고 검증 가능한 요구사항 | 정상 동작, 중요한 실패 조건과 경계가 검증 가능하게 표현된다. |
| `design` | 구현 접근, 책임 경계, 중요한 trade-off와 검증 전략 | 구현 작업을 안정적으로 도출할 수 있다. |
| `tasks` | 순서가 있는 검증 가능한 구현 작업 | 모든 계획 범위가 구현 단위와 완료 근거로 연결된다. |
| `plan-review` | 구현 전 계획 정합성과 실행 가능성 판정 | 모든 required finding이 해소되고 Apply 가능 여부가 명확하다. |

기존 문서가 여러 role을 함께 소유해도 된다. role마다 별도 파일을 만들 필요는 없다.

## Entry Gates

| Entry | Gate |
| --- | --- |
| `research` | 조사할 질문과 범위가 명확하다. |
| `planning` | 현재 작성하거나 수정할 role에 필요한 상위 결정과 근거가 충분하다. |
| `apply` | `intent`, `behavior`, `design`, `tasks`가 서로 일치하고 `plan-review`가 approved이며 unresolved required finding이 없다. |
| `review-feedback` | finding, 근거와 영향을 받는 책임 surface를 식별할 수 있다. |

Gate가 충족되지 않으면 부족한 근거나 owning role로 route한다. artifact를 형식적으로 생성해 gate를 통과시키지 않는다.

## Workflow

1. 요청된 entry, target과 현재 artifact를 식별한다.
1. 기존 artifact를 semantic role에 매핑하고 필요한 role의 준비 상태만 확인한다.
1. 현재 판단에 근거가 부족할 때만 Research를 수행한다.
1. 채택된 Research finding을 책임이 있는 planning role에 반영한다.
1. Planning artifact를 변경했다면 영향을 받는 하위 role을 다시 확인한다.
1. Apply 전에는 전체 planning model을 Plan Review gate로 검증한다.
1. 구현은 `tasks`와 `behavior`를 기준으로 가능한 범위에서 test-first feedback loop로 수행한다.
1. 구현 중 계획 오류가 확인되면 owning planning role로 되돌리고 Plan Review를 다시 수행한다.
1. Review finding은 원인과 변경 책임에 따라 owning surface로 route하고 필요한 validation을 다시 수행한다.
1. 요청된 entry의 gate가 충족되고 다음 action 또는 blocker가 명확하면 종료한다.

불필요한 Research, 계획 재작성, Review 반복은 수행하지 않는다.

## Finding Routing

### Research to Planning

Research 전체를 복제하지 않는다. 채택된 finding만 책임에 따라 이전한다.

| Finding | Route |
| --- | --- |
| 목적, 범위, 영향 | `intent` |
| 관찰 가능한 행동과 계약 | `behavior` |
| 접근, 책임 경계, trade-off, 위험, 검증 전략 | `design` |
| 구현 단위, 순서, 완료 근거 | `tasks` |

Research가 변경 필요성을 만들지 못하면 planning artifact를 억지로 생성하지 않는다.

### Review to Owner

| Finding | Route |
| --- | --- |
| 목적 또는 범위 결함 | `intent` |
| 요구사항 또는 행동 계약 결함 | `behavior` |
| 접근, 경계 또는 검증 전략 결함 | `design` |
| 구현 순서 또는 완료 기준 결함 | `tasks` |
| 구현 또는 test defect | 해당 implementation 또는 test surface |
| 새로운 요구사항 또는 독립적으로 검토할 범위 | 현재 변경과 분리된 후속 change |

Finding 수가 아니라 현재 변경의 목적과 범위 안에서 해결 가능한지로 같은 change와 후속 change를 구분한다.

## Plan Review

Plan Review는 구현 결과가 아니라 구현 전 계획을 검토한다.

다음을 모두 확인한다.

- `intent`와 `behavior`가 서로 일치한다.
- `design`이 behavior를 충족하며 불필요한 범위 확장을 만들지 않는다.
- `tasks`가 design과 behavior를 추적 가능하게 구현 단위로 분해한다.
- 중요한 가정, 실패 경로와 validation이 빠지지 않았다.
- unresolved required finding이 없다.

판정은 다음 중 하나다.

- `approved`: Apply 가능하다.
- `changes_requested`: 현재 계획 범위 안에서 수정이 필요하다.
- `blocked`: 필요한 근거, 결정 또는 외부 조건이 없어 진행할 수 없다.

계획이 실질적으로 수정되면 Plan Review를 다시 수행한다. 새로운 finding 없이 같은 검토를 반복하지 않는다.

## TDD Execution

Apply는 계획을 구현하는 단계다.

1. 현재 task의 observable behavior와 완료 조건을 확인한다.
1. 가능한 경우 실패하는 test 또는 검증 가능한 oracle을 먼저 준비한다.
1. 해당 behavior를 충족하는 최소 구현을 수행한다.
1. 관련 validation을 실행하고 결과를 확인한다.
1. 다음 task로 진행하기 전에 regression이나 계획 불일치를 확인한다.

Test-first가 적용되지 않는 작업은 그 이유와 대체 validation을 명확히 한다. 실행하지 않은 validation을 완료했다고 보고하지 않는다.

## Review Feedback

Review는 planning과 implementation을 대신 소유하지 않는다. finding을 검증한 뒤 owning surface로 돌려보낸다.

- 근거 없는 가능성, style 선호 또는 이미 해소된 finding을 required finding으로 만들지 않는다.
- planning 수정은 영향을 받는 Plan Review를 다시 연다.
- implementation 수정은 관련 behavior와 validation을 다시 확인한다.
- 범위 밖 finding은 현재 change를 비대하게 만들지 않고 후속 change로 분리한다.

## Handoff

필요할 때 다음 최소 상태만 전달한다.

```markdown
## RPI Handoff

- Entry:
- Target: <target | not-applicable>
- Planning: <ready | needs-revision | not-applicable>
- Research: <used | not-required>
- Review: <resolved | findings | not-required>
- Gate: <ready | blocked>
- Next:
```

확인한 상태만 기록한다. 숨은 추론, 전체 Research 과정 또는 불필요한 workflow history를 durable output으로 만들지 않는다.

## Completion

요청된 entry의 gate를 충족하고 다음 action 또는 blocker가 명확하면 완료한다.

Research나 Review를 사용했다면 채택된 결정이 transient evidence에만 남아 있지 않아야 한다.

## Boundaries

- 특정 project, repository layout, schema path, artifact filename 또는 VCS workflow를 필수로 가정하지 않는다.
- 외부 문서, guideline, template 또는 다른 skill을 이 skill의 동작 조건으로 만들지 않는다.
- 별도 Research 또는 Review 문서를 자동으로 만들지 않는다.
- artifact 수를 늘리는 것을 workflow 진행으로 착각하지 않는다.
- Research가 요구사항, 설계 또는 구현 결정을 단독으로 확정하게 하지 않는다.
- Review를 별도의 canonical authority로 만들지 않는다.
- 계획이 충분히 명확한데 형식적 phase 반복을 강제하지 않는다.
- 새로운 finding이나 근거 없이 review loop를 반복하지 않는다.
