---
type: plan
title: "Core Documentation Consistency Plan"
description: "Use when coordinating PR #226 scope, document ownership, inspection order, and completion criteria."
tags:
  - consistency
  - documentation
  - maintenance
---

# Core Documentation Consistency Plan

## Goal

PR #226은 핵심 문서가 같은 프로젝트를 서로 다른 책임 수준에서 일관되게 설명하도록 정리한다. 장기 방향, 현재 MVP, architecture, 개발 환경의 canonical ownership은 유지하고, 실제 의미 충돌·용어 불일치·불필요한 중복·읽기 비용이 확인된 부분만 최소 범위로 수정한다.

새로운 제품 요구사항이나 capability contract를 만드는 작업이 아니다. 현재 capability의 normative contract는 계속 `openspec/specs/**`, 실제 구현 상태는 source와 configuration이 소유한다.

## Boundaries

[`docs/AGENTS.md`](../../docs/AGENTS.md)의 ownership과 trust boundary를 기준으로 각 문서가 맡은 책임 안에서만 수정한다. 일반 문서 품질은 [`docs/documentation/`](../../docs/documentation/README.md), Markdown 표현은 [`.rulesync/rules/markdown.md`](../../.rulesync/rules/markdown.md)를 따른다.

- `VISION.md`의 장기 방향을 현재 MVP 세부사항에 맞춰 축소하지 않는다.
- `mvp.md`에 구현 상태나 validation 결과를 새로 소유시키지 않는다.
- `ARCHITECTURE.md`에 exact capability requirement를 복제하지 않는다.
- `README.md`와 `DEVELOPMENT.md`는 진입점과 개발 context에 필요한 수준만 유지한다.
- 문서 정리를 이유로 source, test, OpenSpec, workflow 또는 unrelated Inbox artifact를 변경하지 않는다.

## Execution Model

전체 문서를 한 번에 수정하지 않는다. 실제 실행 순서, folder별 done gate, cross-folder queue와 최종 logical validation은 [`02-plan-folder-and-logical-validation-todo.md`](02-plan-folder-and-logical-validation-todo.md)를 따른다.

- 한 번에 하나의 folder unit만 writable scope로 둔다.
- 현재 folder를 완료하고 검증한 뒤에만 다음 unit으로 이동한다.
- 다른 folder의 독립 문제는 즉시 수정하지 않고 queue에 남긴다.
- folder 작업이 모두 끝나면 data flow, recovery authority, AI delegation, development workflow처럼 의미 단위로 다시 검증한다.

## Target Set

| Target | Inspection focus |
| --- | --- |
| [`README.md`](../../README.md) | 첫 진입점의 현재 MVP 설명, 용어와 중복 수준 |
| [`docs/VISION.md`](../../docs/VISION.md) | durable direction과 delegation 원칙의 밀도·중복 |
| [`docs/mvp.md`](../../docs/mvp.md) | active goal, acceptance와 architecture terminology의 정합성 |
| [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) | execution boundary, recovery abstraction과 domain terminology |
| [`DEVELOPMENT.md`](../../DEVELOPMENT.md) | active tool/layer naming과 architecture 표현의 정합성 |

위 핵심 문서를 중심축으로 유지하되 실제 정합성 검증은 checklist의 folder unit에 따라 `docs/**` human documentation을 단계적으로 확인한다. `docs/domains/**`, `docs/development/**` 등은 해당 unit 차례에만 writable scope가 되며, OpenSpec, source와 test는 supporting evidence로만 사용한다.

## Work Sequence

1. 각 반복 개념의 canonical owner와 abstraction level을 고정한다.
1. 현재 folder unit 안에서 같은 개념을 표현하는 용어와 boundary를 비교한다.
1. 실제 contradiction, 누락된 mapping, 의도적인 abstraction 차이, 단순 prose 문제를 구분한다.
1. 독자의 판단을 바꾸는 문제만 가장 작은 coherent edit로 수정한다.
1. 해당 folder의 done gate를 통과하고 cross-folder candidate를 queue에 기록한다.
1. 모든 folder unit 완료 후 logical validation checklist로 cross-document consistency를 다시 검증한다.
1. 수정 후 관련 owner와 다시 대조하고 changed Markdown에 repository-owned validation을 적용한다.
1. PR description에는 최종 변화와 실제 validation 결과만 반영하고 상세 작업 과정은 Inbox artifact에 남긴다.

## Acceptance

- 같은 개념이 핵심 문서에서 서로 다른 authority나 safety boundary로 읽히지 않는다.
- 서로 다른 layer naming을 유지해야 한다면 대응 관계를 독자가 별도 추론 없이 이해할 수 있다.
- recovery와 AI delegation 설명은 문서별 abstraction을 지키며 concrete contract를 잘못 일반화하지 않는다.
- canonical owner가 분명한 반복 설명은 필요한 맥락만 남기고 재정의하지 않는다.
- 의미를 바꾸지 않는 prose 다듬기는 중요한 조건·예외·관계를 보존한다.
- 각 folder unit의 완료가 독립적으로 검증되고, 마지막 logical validation에서 cross-folder contradiction이 남지 않는다.
- 변경된 문서의 Markdown, link, metadata와 repository-specific validation 결과가 확인된다.

## Out of Scope

- 구현, test 또는 runtime behavior 변경
- OpenSpec requirement 추가·수정
- 새로운 architecture 또는 delegation policy 결정
- 완료 여부, roadmap 또는 dashboard 갱신
- 이번 정합성 작업과 직접 연결되지 않은 문서 전면 rewrite
