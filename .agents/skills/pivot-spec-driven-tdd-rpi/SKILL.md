---
name: pivot-spec-driven-tdd-rpi
description: Coordinate research-backed work with the OpenSpec custom schema `spec-driven-tdd`. Use when starting Research, creating or revising planning artifacts, or entering Apply from an existing change. Treat Research as temporary input: after accepted findings are transferred into their owning planning artifacts, later work depends on those artifacts rather than the Research file. Do not impose a fixed phase sequence, redefine schema contracts, or place Research inside OpenSpec.
---

# Spec-Driven TDD RPI

OpenSpec 밖의 임시 Research를 `spec-driven-tdd` planning에 연결한다.

Research는 planning의 입력일 수 있지만 durable dependency는 아니다. 채택된 결론이 책임을 소유하는 planning artifact로 이전되면 이후 workflow는 Research 없이 계속되어야 한다.

## Core Contract

- `spec-driven-tdd`가 `proposal`, `specs`, `design`, `tasks`, `plan-review`와 Apply contract를 소유한다.
- Research는 `research/`의 local rules를 따르는 독립적이고 임시적인 evidence artifact다.
- Entry는 phase 실행 이력이 아니라 현재 entry에 필요한 artifact로 결정한다.
- Research handoff는 이후 판단에 필요한 모든 채택된 결론이 책임에 맞는 planning artifact로 이전되었을 때 완료된다.
- Handoff가 완료되면 Research의 삭제, 이동 또는 부재를 이후 entry의 blocker로 취급하지 않는다.

## Artifact Flow

```text
Research ──accepted findings──> planning artifacts ──schema gate──> Apply
   └────────────────────── temporary; handoff 후 삭제 가능
```

Planning artifact는 Research 전체를 복제하지 않는다. 요구사항, 설계, task, 위험 또는 검증 전략에 영향을 주는 채택된 결론만 해당 책임을 소유하는 artifact로 이전한다.

## Entry Gates

| Entry | Gate |
| --- | --- |
| Research | 조사할 목표와 범위가 명확하다. |
| Planning artifact | schema가 선언한 `requires`와 현재 판단에 충분한 evidence가 준비되어 있다. Research가 존재하면 사용하되, 필요하지 않으면 새로 만들지 않는다. |
| Apply | schema가 선언한 `apply.requires`가 준비되어 있고 planning artifact가 현재 변경과 일관된다. Research artifact의 존재는 요구하지 않는다. |

필요한 evidence가 부족하면 Research로 route한다. 채택된 결론이 planning artifact로 이전된 뒤에는 해당 artifact가 다음 entry의 입력을 소유한다.

## Core Workflow

1. 요청된 entry와 target change를 식별한다.
1. `openspec/schemas/spec-driven-tdd/`에서 해당 entry의 contract만 읽는다.
1. schema가 요구하는 artifact의 존재, 관련성과 일관성을 확인한다.
1. 판단 근거가 부족할 때만 Research를 작성하거나 갱신한다.
1. 채택된 Research 결론을 책임에 맞는 planning artifact로 이전한다.
1. Research를 정리하기 전에 이후 판단에 필요한 채택된 결론이 Research에만 남아 있지 않은지 확인한다.
1. gate가 충족되면 요청된 entry를 수행한다.

상위 planning artifact가 실질적으로 바뀌면 영향을 받는 하위 artifact만 다시 검증한다. Research가 이미 삭제되었더라도 planning artifact가 충분하면 재생성하지 않는다.

## Research Handoff

Research handoff 완료 시 다음이 성립해야 한다.

- 이후 판단에 필요한 채택된 결론을 owning planning artifact에서 확인할 수 있다.
- Research path나 chat history가 유일한 근거로 남지 않는다.
- Planning의 정합성과 Apply 진입 가능 여부를 Research 없이 평가할 수 있다.
- Research를 삭제해도 schema dependency와 Apply gate가 유지된다.

Research의 저장, 삭제와 archive는 `research/`의 local rules를 따른다. Archive는 인간이 명시적으로 승인한 경우에만 수행한다.

Planning이 이후 실질적으로 변경되어 근거가 다시 부족해지면 현재 질문에 필요한 Research로 route한다. 원본 Research의 부재 자체는 재조사 사유가 아니다.

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

확인한 artifact와 상태만 기록한다. 삭제된 Research는 다시 요구하지 않으며, 실행하거나 검증하지 않은 상태를 사실처럼 보고하지 않는다.

## Completion

요청된 entry의 schema gate를 충족하고 다음 route 또는 blocker가 명확하면 완료한다. Research handoff를 수행했다면 이후 workflow가 원본 Research 없이도 진행 가능한 상태여야 한다.
