---
name: pivot-spec-driven-tdd-rpi
description: >-
  Coordinate temporary Research, OpenSpec `spec-driven-tdd` planning and Apply
  work. Use when Research informs a change, when creating or revising planning
  artifacts, when entering Apply, or when Review findings must be routed to
  their owning planning or implementation artifacts. Research and Review
  evidence are temporary and must not become durable workflow dependencies.
compatibility: >-
  Depends on OpenSpec and its custom `spec-driven-tdd` schema.
metadata:
  version: "0.2.1"
---

# Spec-Driven TDD RPI

OpenSpec 밖의 임시 Research와 Review evidence를 `spec-driven-tdd` planning과 Apply에 연결한다.

Research와 Review는 입력일 수 있지만 durable dependency는 아니다. Handoff가 완료되면 이후 workflow는 owning artifact만으로 계속되어야 한다.

## Core Contract

- `spec-driven-tdd`가 planning artifact, dependency와 Apply contract를 소유한다.
- Research와 inbox Review artifact는 `inbox/AGENTS.md`의 공통 규칙과 해당 type guideline을 따른다.
- OpenSpec Plan Review와 inbox Review를 구분한다.
- Entry는 phase 실행 이력이 아니라 현재 entry에 필요한 artifact와 contract로 결정한다.
- Finding handoff는 채택된 결론, 조치와 필요한 근거가 임시 artifact에만 남지 않을 때 완료된다.
- Research 또는 inbox Review artifact의 존재와 verdict를 Apply나 archive dependency로 만들지 않는다.

## Finding Ownership

Research 전체를 복제하지 않는다. 채택된 finding만 현재 schema가 정의한 artifact responsibility에 따라 이전한다. 아래 표는 routing 요약이며 세부 contract는 현재 schema가 우선한다.

| Finding | Owning artifact |
| --- | --- |
| 변경 목적, 범위, Capability와 영향 | `proposal` |
| 관찰 가능한 행동과 계약 | `specs` |
| 접근, 책임 경계, trade-off, 위험과 검증 전략 | `design` |
| 구현 단위, 순서와 완료 근거 | `tasks` |
| 계획의 정합성과 실행 가능성 판정 | `plan-review`가 독립적으로 작성 |

Review finding은 원인과 변경 책임에 따라 route한다.

| Finding | Route |
| --- | --- |
| Planning defect | 해당 planning artifact 수정 후 Plan Review 재수행 |
| Implementation 또는 test defect | source 또는 tests 수정 후 관련 validation 재수행 |
| 새로운 요구사항 또는 확장된 범위 | 후속 OpenSpec Change |
| 문서, workflow 또는 process defect | 해당 canonical artifact |

문제의 수가 아니라 기존 Change의 의도와 범위 안인지로 같은 Change와 후속 Change를 구분한다.

## Entry Gates

| Entry | Gate |
| --- | --- |
| Research | 조사할 목표와 범위가 명확하다. |
| Planning artifact | schema가 선언한 `requires`와 해당 artifact를 작성할 충분한 근거가 준비되어 있다. Research가 필요하지 않으면 새로 만들지 않는다. |
| Apply | schema가 정의한 Apply contract 전체를 충족한다. Research와 inbox Review artifact는 추가로 요구하지 않는다. |
| Review feedback | 대상 revision, finding과 근거가 식별되어 owning artifact로 route할 수 있다. |

Artifact 간 모순이나 근거 부족이 확인되면 영향을 소유하는 artifact로 route하고 schema dependency에 따라 다시 검증한다.

## Core Workflow

1. 요청된 entry를 식별하고, Change가 이미 존재하거나 해당 entry에 필요한 경우에만 target change를 식별한다.
1. OpenSpec entry라면 `openspec/schemas/spec-driven-tdd/`에서 해당 contract만 읽는다.
1. OpenSpec entry라면 schema가 요구하는 artifact와 현재 근거를 확인한다.
1. Research가 필요한 경우에만 기존 Research를 사용하거나 필요한 범위로 조사한다.
1. accepted finding을 책임에 맞는 planning artifact로 이전한다.
1. Review feedback이 있으면 원인과 범위에 따라 owning artifact 또는 후속 Change로 route한다.
1. 변경된 artifact의 dependency와 필요한 validation을 다시 확인한다.
1. 임시 evidence를 정리하기 전에 이후 판단에 필요한 정보가 그 파일에만 남아 있지 않은지 확인한다.
1. 적용되는 gate가 충족되면 요청된 entry를 수행한다.

상위 planning artifact가 실질적으로 바뀌면 영향을 받는 하위 artifact를 다시 검증한다. Research나 inbox Review artifact의 부재 자체는 재조사 또는 재검토 사유가 아니다.

## Temporary Artifact Lifecycle

Research와 inbox Review artifact의 저장, 삭제와 archive는 `inbox/AGENTS.md`와 해당 type guideline을 따른다.

- Handoff가 완료되면 임시 artifact를 삭제해도 이후 planning, Apply와 archive를 계속할 수 있어야 한다.
- Archive와 promotion은 inbox lifecycle과 branch 규칙을 따른다.
- Planning 또는 구현이 바뀌어 근거가 다시 부족해지면 현재 질문에 필요한 Research나 Review로 route한다.
- Review의 validation과 남은 risk는 필요한 경우 PR, Issue 또는 canonical artifact로 이전한다.

## Boundaries

- `spec-driven-tdd`의 dependency, template, parser 또는 Apply contract를 다시 정의하지 않는다.
- Research나 inbox Review를 OpenSpec change directory 또는 schema artifact로 만들지 않는다.
- inbox Review를 Plan Review와 합치거나 대체하지 않는다.
- 별도의 Plan artifact나 고정된 phase pipeline을 추가하지 않는다.
- Review path, sequence와 retention 규칙을 이 skill에서 다시 정의하지 않는다.
- Research나 inbox Review의 존재를 handoff 이후 entry의 추가 gate로 만들지 않는다.
- Review verdict를 자동 archive 승인으로 해석하지 않는다.
- Chat history나 숨은 추론을 durable artifact로 취급하지 않는다.
- 임시 artifact만으로 요구사항, 설계 또는 구현 결정을 확정하지 않는다.

## Handoff

```markdown
## RPI Handoff

- Entry:
- Change: <id | not-applicable>
- Planning: <artifact | not-applicable>
- Research: <path | transferred | not-required>
- Review: <path | transferred | not-required>
- Gate: ready | blocked
- Next:
```

확인한 artifact와 상태만 기록한다. 실행하거나 검증하지 않은 상태를 사실처럼 보고하지 않는다.

## Completion

요청된 entry에 적용되는 gate를 충족하고 다음 route 또는 blocker가 명확하면 완료한다. Research나 Review handoff를 수행했다면 이후 workflow가 원본 임시 artifact 없이도 진행 가능한 상태여야 한다.
