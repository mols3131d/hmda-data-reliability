---
name: pivot-openspec-rpi
description: |
   Coordinate Project Pivot's human-centered Research → OpenSpec → Implement → Review workflow for non-trivial development and operational changes. Use when a task has uncertainty, spans multiple files, changes behavior or architecture, depends on external APIs, or needs evidence-backed validation. Use with existing OpenSpec changes or to create a new change without forking OpenSpec. Do not use for trivial edits, simple formatting, or requests that do not require implementation.
---

# Pivot OpenSpec RPI

OpenSpec을 변경의 Source of Truth로 사용한다. P는 repository에 설치된 OpenSpec workflow를
그대로 실행하며, RPI는 이를 대체하거나 custom schema·entry gate·lifecycle을 추가하지 않는다.
각 phase는 독립적으로 시작할 수 있지만, 실행과 종료에는 해당 phase의 artifact 계약이 필요하다.
명세 전에는 선택적으로 근거 중심 Research를, 구현 후에는 독립적인 Review를 결합한다.

`pivot`은 project 가제 namespace다. project 이름이 바뀌면 directory와 front matter의 `name`을 함께 변경한다.

## Operating Model

| Phase | 책임 | Durable artifact |
| --- | --- | --- |
| Research | 근거 충분성, 현재 상태, 위험, 미해결 질문 | `openspec/research/{research-id}/research.md` |
| OpenSpec | 문제, 요구사항, 설계, task, change 상태 | 기존 OpenSpec artifact |
| Implement | OpenSpec task가 요구한 코드와 검증 | 코드, 테스트, 갱신된 `tasks.md` |
| Review | spec·구현·근거의 독립적 대조 | `openspec/reviews/{change-id}/{sequence}-{review-title}[-{extension}].md` |

OpenSpec 밖에 별도의 plan을 만들지 않는다.

## Entry Routing

1. [Principles](references/principles.md)와 [Workflow](references/workflow.md)를 읽는다.
1. 요청에서 시작 phase를 정한다. 명시되지 않으면 현재 artifact와 요청의 직접 목표로 Research, OpenSpec, Implement, Review 중 하나를 선택한다.
1. 선택한 phase의 [입력 계약](references/workflow.md#stage-contract)을 기존 artifact로 확인한다.
   - 계약을 충족하면 선택한 phase를 바로 실행한다.
   - 계약에 필요한 artifact가 없거나 신뢰할 수 없으면, 해당 artifact owner phase로 route한다.
   - 이미 존재하는 artifact를 다시 만들거나 앞 phase를 형식적으로 재실행하지 않는다.
1. Research에서 시작할 때만 repository에서 재사용하지 않는 안정적인 `{research-id}`를 정한다.
   - 날짜를 넣지 않은 kebab-case ID를 사용한다.
   - Research가 여러 날 이어져도 ID와 경로를 바꾸지 않는다.
   - 세부 절차와 artifact bundle 규칙은 [Research](references/research.md)를 따른다.
1. OpenSpec에서 시작할 때는 설치된 OpenSpec workflow의 entry contract와 절차를 그대로 따른다.
   - stage contract와 handoff는 [Workflow](references/workflow.md)를 따른다.
1. Implement에서 시작할 때는 승인된 OpenSpec task를 확인한 뒤 구현한다.
   - 입력·완료 조건과 handoff는 [Workflow](references/workflow.md)를 따른다.
1. Review에서 시작할 때는 active OpenSpec change, 구현 diff, 실제 검증 결과, 관련 Research를 확인한다.
   - 입력, attempt 규칙, finding과 verdict는 [Review](references/review.md)를 따른다.
1. Review status에 따라 route한다.
   - verdict에 따른 다음 owner와 lifecycle은 [Workflow](references/workflow.md)를 따른다.

## Autonomy

일상적인 확인을 요청하지 않고 loop를 계속한다.

다음 Human gate에서만 멈춘다.

| Gate | 예시 |
| --- | --- |
| Intent conflict | 사용자 요청과 활성 OpenSpec이 충돌 |
| Material choice | 선택에 따라 제품 동작, 호환성, 비용, 위험이 달라짐 |
| Unsafe side effect | 파괴적·비가역적·권한 필요·외부 공개 작업 |
| Missing access | 필수 저장소, 환경, secret, service에 접근 불가 |

Review status가 `approved`가 아니면 archive하지 않는다.

## Context Discipline

- phase 사이에는 chat history보다 durable artifact를 우선한다.
- 이전 agent의 숨은 추론이 아니라 artifact와 대상 change를 전달한다.
- main context는 조율과 사람의 결정에 집중한다.
- 현재 phase에 필요한 reference만 읽는다.

## Resource Map

| 필요 | 읽을 파일 |
| --- | --- |
| 판단 원칙 | [Principles](references/principles.md) |
| 전체 lifecycle과 routing | [Workflow](references/workflow.md) |
| Research 절차 | [Research](references/research.md) |
| Review 절차 | [Review](references/review.md) |
| Windows·WSL·Copilot·Codex 적용 | [Adoption](references/adoption.md) |

## Final Report

최종 결과는 짧은 표로 보고한다.

| Field | Content |
| --- | --- |
| Research | RPI Research identifier와 status |
| Change | OpenSpec change identifier |
| Implementation | 완료 task와 주요 amendment |
| Validation | 실제 실행한 check와 결과 |
| Review | `pending`, `in_progress`, `approved`, `changes_requested`, `blocked` |
| Remaining | 알려진 위험, blocker, follow-up change |
