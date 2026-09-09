---
type: plan
title: "Core Documentation Consistency and Readability Plan"
description: "Use when coordinating PR #226 scope, ownership, four-stage execution order, and completion criteria."
tags:
  - consistency
  - documentation
  - maintenance
  - readability
---

# Core Documentation Consistency and Readability Plan

## Goal

PR #226은 핵심 문서가 같은 프로젝트를 서로 다른 책임 수준에서 일관되게 설명하도록 정리한 뒤, 그 의미를 보존하면서 가독성을 개선한다. 장기 방향, 현재 MVP, architecture, 개발 환경의 canonical ownership은 유지하고 실제 의미 충돌·용어 불일치·불필요한 중복·읽기 비용이 확인된 부분만 최소 범위로 수정한다.

새로운 제품 요구사항이나 capability contract를 만드는 작업이 아니다. 현재 capability의 normative contract는 계속 `openspec/specs/**`, 실제 구현 상태는 source와 configuration이 소유한다.

## Boundaries

[`docs/AGENTS.md`](../../docs/AGENTS.md)의 ownership과 trust boundary를 기준으로 각 문서가 맡은 책임 안에서만 수정한다. 일반 문서 품질은 [`docs/documentation/`](../../docs/documentation/README.md), Markdown 표현은 [`.rulesync/rules/markdown.md`](../../.rulesync/rules/markdown.md)를 따른다.

- `VISION.md`의 장기 방향을 현재 MVP 세부사항에 맞춰 축소하지 않는다.
- `mvp.md`에 구현 상태나 validation 결과를 새로 소유시키지 않는다.
- `ARCHITECTURE.md`에 exact capability requirement를 복제하지 않는다.
- `README.md`와 `DEVELOPMENT.md`는 진입점과 개발 context에 필요한 수준만 유지한다.
- 문서 정리를 이유로 source, test, OpenSpec, workflow 또는 unrelated Inbox artifact를 변경하지 않는다.
- 정합성 수정과 readability-only edit를 같은 단계에서 섞지 않는다.
- 가독성보다 semantic fidelity와 canonical ownership을 우선한다.

## Execution Model

실제 실행 순서와 folder별 checklist는 [`02-plan-folder-and-logical-validation-todo.md`](02-plan-folder-and-logical-validation-todo.md)를 따른다. 작업은 다음 네 단계를 순서대로 완료한다.

1. **Consistency Review** — folder 단위로 정합성 문제와 protected non-finding을 확인한다. 원칙적으로 canonical 문서를 수정하지 않는다.
1. **Consistency Improvement** — Stage 1에서 확정된 finding만 folder 단위로 수정하고 logical unit별로 다시 검증한다. 완료 시점의 의미를 semantic baseline으로 고정한다.
1. **Readability Polish** — semantic baseline을 변경하지 않고 정보 구조, navigation, 문장과 Markdown 표현만 다듬는다.
1. **Integrity Review** — Stage 2 semantic baseline과 Stage 3 결과를 비교해 의미·계약·권한·조건이 파괴되지 않았는지 검증한다.

각 단계 안에서도 한 번에 하나의 folder unit만 다룬다. 현재 folder gate를 닫기 전에는 다음 folder로 이동하지 않고, 다른 folder의 독립 문제는 `Cross-Folder Queue`에 기록한다.

## Target Set

| Target | Inspection focus |
| --- | --- |
| [`README.md`](../../README.md) | 첫 진입점의 현재 MVP 설명, 용어와 중복 수준 |
| [`docs/VISION.md`](../../docs/VISION.md) | durable direction과 delegation 원칙의 밀도·중복 |
| [`docs/mvp.md`](../../docs/mvp.md) | active goal, acceptance와 architecture terminology의 정합성 |
| [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) | execution boundary, recovery abstraction과 domain terminology |
| [`DEVELOPMENT.md`](../../DEVELOPMENT.md) | active tool/layer naming과 architecture 표현의 정합성 |

`docs/**`의 다른 human-authored 문서는 folder unit별 검토에서 관련성이 확인되면 동일한 네 단계에 포함한다. `docs/domains/**`, `openspec/specs/**`, source와 test는 문서 표현이 실제 owner와 맞는지 확인하는 supporting evidence로 읽을 수 있지만, 별도 scope가 확인되기 전에는 구현·contract 수정 대상으로 확장하지 않는다.

## Acceptance

- 같은 개념이 핵심 문서에서 서로 다른 authority나 safety boundary로 읽히지 않는다.
- 서로 다른 layer naming을 유지해야 한다면 대응 관계를 독자가 별도 추론 없이 이해할 수 있다.
- recovery와 AI delegation 설명은 문서별 abstraction을 지키며 concrete contract를 잘못 일반화하지 않는다.
- canonical owner가 분명한 반복 설명은 필요한 맥락만 남기고 재정의하지 않는다.
- 정합성 개선은 Stage 1에서 확인된 문제에 근거하고 logical validation을 통과한다.
- 가독성 개선은 Stage 2 semantic baseline의 사실, 관계, 조건, 예외와 authority를 보존한다.
- Stage 4에서 readability edit로 인한 semantic regression이 없음을 다시 검증한다.
- 변경된 문서의 Markdown, link, metadata와 repository-specific validation 결과가 확인된다.

## Out of Scope

- 구현, test 또는 runtime behavior 변경
- OpenSpec requirement 추가·수정
- 새로운 architecture 또는 delegation policy 결정
- 완료 여부, roadmap 또는 dashboard 갱신
- 이번 정합성·가독성 작업과 직접 연결되지 않은 문서 전면 rewrite
