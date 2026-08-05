---
name: pivot-spec-driven-tdd-rpi
description: >-
  Coordinate research-backed planning and Apply work with the OpenSpec custom
  schema `spec-driven-tdd`. Use when Research may inform a change, when creating
  or revising planning artifacts, or when entering Apply from an existing change.
  Research is temporary: after decision-relevant findings are transferred to
  their owning planning artifacts, later entries must not require the Research
  file. Do not redefine schema contracts or place Research inside OpenSpec.
compatibility: >-
  Requires an Agent Skills-compatible coding agent with repository file access
  and an OpenSpec project that provides the custom `spec-driven-tdd` schema.
metadata:
  version: "0.1.0"
---

# Spec-Driven TDD RPI

OpenSpec 밖의 임시 Research를 `spec-driven-tdd` planning에 연결한다.

Research는 planning의 입력일 수 있지만 durable dependency는 아니다. Handoff가 완료되면 이후 workflow는 planning artifact만으로 계속되어야 한다.

## Core Contract

- `spec-driven-tdd`가 planning artifact, dependency와 Apply contract를 소유한다.
- Research는 `research/`의 local rules를 따르는 독립적이고 임시적인 evidence artifact다.
- Entry는 phase 실행 이력이 아니라 현재 entry에 필요한 artifact로 결정한다.
- Research handoff는 후속 판단에 필요한 accepted finding이 더 이상 Research에만 남지 않을 때 완료된다.
- 나중에 재검증해야 하는 finding은 결론과 함께 source location을 owning artifact에 남긴다.

## Finding Ownership

Research 전체를 복제하지 않는다. 채택된 finding만 책임에 맞게 이전한다.

| Finding | Owning artifact |
| --- | --- |
| 변경 목적, 범위, Capability와 영향 | `proposal` |
| 관찰 가능한 행동과 계약 | `specs` |
| 접근, 책임 경계, trade-off, 위험과 검증 전략 | `design` |
| 구현 단위, 순서와 완료 근거 | `tasks` |
| 계획의 정합성과 실행 가능성 판정 | `plan-review`가 독립적으로 작성 |

## Entry Gates

| Entry | Gate |
| --- | --- |
| Research | 조사할 목표와 범위가 명확하다. |
| Planning artifact | schema가 선언한 `requires`와 해당 artifact를 작성할 충분한 근거가 준비되어 있다. Research가 필요하지 않으면 새로 만들지 않는다. |
| Apply | schema가 선언한 `apply.requires`가 준비되어 있다. Research artifact는 요구하지 않는다. |

Artifact 간 모순이나 근거 부족이 확인되면 영향을 소유하는 artifact로 route하고 schema dependency에 따라 다시 검증한다.

## Core Workflow

1. 요청된 entry와 target change를 식별한다.
1. `openspec/schemas/spec-driven-tdd/`에서 해당 entry의 contract만 읽는다.
1. schema가 요구하는 artifact와 현재 근거를 확인한다.
1. 근거가 부족할 때만 기존 Research를 사용하거나 필요한 범위로 조사한다.
1. accepted finding을 책임에 맞는 planning artifact로 이전한다.
1. Research를 정리하기 전에 후속 판단에 필요한 finding이나 source location이 Research에만 남아 있지 않은지 확인한다.
1. schema gate가 충족되면 요청된 entry를 수행한다.

상위 planning artifact가 실질적으로 바뀌면 영향을 받는 하위 artifact만 다시 검증한다. 원본 Research의 부재 자체는 재조사 사유가 아니다.

## Research Lifecycle

Research의 저장, 삭제와 archive는 `research/`의 local rules를 따른다.

- Handoff가 완료되면 Research를 삭제해도 이후 planning과 Apply를 계속할 수 있다.
- Archive는 인간이 명시적으로 승인한 경우에만 수행한다.
- Planning이 바뀌어 근거가 다시 부족해지면 현재 질문에 필요한 Research로 route한다.

## Boundaries

- `spec-driven-tdd`의 dependency, template, parser 또는 Apply contract를 다시 정의하지 않는다.
- Research를 OpenSpec change directory에 넣거나 schema artifact로 만들지 않는다.
- 별도의 Plan artifact나 고정된 phase pipeline을 추가하지 않는다.
- Research의 존재를 handoff 이후 entry의 추가 gate로 만들지 않는다.
- Chat history나 숨은 추론을 durable artifact로 취급하지 않는다.
- Research 결과만으로 요구사항, 설계 또는 구현 결정을 확정하지 않는다.

## Handoff

```markdown
## RPI Handoff

- Entry:
- Change:
- Planning:
- Research: <path | transferred | not-required>
- Gate: ready | blocked
- Next:
```

확인한 artifact와 상태만 기록한다. 실행하거나 검증하지 않은 상태를 사실처럼 보고하지 않는다.

## Completion

요청된 entry의 schema gate를 충족하고 다음 route 또는 blocker가 명확하면 완료한다. Research handoff를 수행했다면 이후 workflow가 원본 Research 없이도 진행 가능한 상태여야 한다.
