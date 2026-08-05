---
name: pivot-spec-driven-tdd-rpi
description: Extend the OpenSpec custom schema `spec-driven-tdd` with independent Research artifacts. Use to coordinate research-backed planning and Apply work from any valid entry point by verifying the artifacts required for that entry. Do not impose a fixed phase sequence, redefine the schema, or place Research inside OpenSpec.
metadata:
  - version: 0.1.0
---

# Spec-Driven TDD RPI

`spec-driven-tdd`에 OpenSpec 밖의 Research를 evidence layer로 연결한다.

RPI의 entry는 고정하지 않는다. 요청된 entry에 필요한 artifact는 반드시 존재해야 하며, Plan과 Implement의 contract는 `spec-driven-tdd`가 소유한다.

## Artifact Model

```text
Research artifact ──evidence──> spec-driven-tdd change
```

Research는 `research/`에 저장되는 독립 artifact다. OpenSpec change나 schema artifact가 아니며, 요구사항·설계·task의 canonical source가 되지 않는다. 채택된 결론은 해당 OpenSpec artifact로 이전한다.

Change는 관련 Research artifact를 명시적으로 연결한다. 하나의 Research가 여러 change를 지원하거나 하나의 change가 여러 Research를 참조할 수 있다.

## Artifact Gates

| Entry | Gate |
| --- | --- |
| Research | 조사할 목표와 범위가 명확하다. |
| OpenSpec artifact | 관련 Research artifact와 schema가 선언한 `requires`가 준비되어 있다. |
| Apply | 관련 Research artifact와 schema가 선언한 `apply.requires`가 준비되어 있다. |

이전 phase의 실행 이력은 gate가 아니다. 필요한 artifact가 현재 목적에 충분하고 서로 실질적으로 충돌하지 않으면 해당 entry에서 시작한다.

## Routing

1. 요청된 entry, 관련 Research artifact와 target change를 식별한다.
1. `openspec/schemas/spec-driven-tdd/`에서 해당 entry의 contract을 읽는다.
1. 필요한 artifact의 존재, 관련성, 일관성을 확인한다.
1. 누락되거나 충돌하는 artifact가 있으면 해당 artifact의 owner로 route한다.
1. gate가 충족되면 요청된 entry를 수행한다.

상위 artifact가 실질적으로 바뀌면 영향을 받는 하위 artifact만 다시 검증한다. Research 변경도 변경의 목적, 범위, 전제, 위험 또는 검증 전략을 바꿀 때만 OpenSpec artifact 갱신으로 이어진다.

## Research

Research artifact는 현재 변경을 계획하거나 재검토하기에 충분한 질문, 근거, 결론, 불확실성과 영향을 남긴다.

Research가 부족하면 추측으로 OpenSpec artifact를 작성하지 않는다. 충분한 Research가 있으면 추가 조사를 반복하지 않고 기존 artifact를 사용한다.

저장 경로와 lifecycle은 `research/`의 local rules를 따른다. 채택된 결론은 owning artifact로 이전하며, archive는 인간이 명시적으로 승인한 경우에만 수행한다.

## Boundaries

- `spec-driven-tdd`의 dependency, template, parser와 Apply contract을 다시 정의하지 않는다.
- Research를 OpenSpec change directory에 넣거나 schema artifact로 만들지 않는다.
- 별도의 Plan artifact나 고정된 phase pipeline을 추가하지 않는다.
- Chat history나 숨은 추론을 durable artifact로 취급하지 않는다.
- Research 결과만으로 요구사항, 설계 또는 구현 결정을 확정하지 않는다.

## Handoff

```markdown
## RPI Handoff

- Entry:
- Research:
- Change:
- Gate: ready | blocked
- Next:
```

Artifact path와 확인된 상태만 기록한다. 실행하지 않았거나 검증하지 않은 상태는 사실처럼 보고하지 않는다.

## Completion

요청된 entry의 artifact gate를 충족했고, Research와 change의 관계가 보이며, 다음 route 또는 blocker가 명확하면 완료한다.
