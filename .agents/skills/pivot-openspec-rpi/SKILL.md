---
name: pivot-openspec-rpi
description: |
   Coordinate Project Pivot's human-centered Research → OpenSpec → Implement → Review workflow for non-trivial development and operational changes. Use when a task has uncertainty, spans multiple files, changes behavior or architecture, depends on external APIs, or needs evidence-backed validation. Use with existing OpenSpec changes or to create a new change without forking OpenSpec. Do not use for trivial edits, simple formatting, or requests that do not require implementation.
---

# Pivot OpenSpec RPI

OpenSpec을 변경의 Source of Truth로 사용한다. 명세 전에는 근거 중심 Research를, 구현 후에는 독립적인 Review를 결합한다.

`pivot`은 project 가제 namespace다. project 이름이 바뀌면 directory와 front matter의 `name`을 함께 변경한다.

## Operating Model

| Phase | 책임 | Durable artifact |
| --- | --- | --- |
| Research | 근거 충분성, 현재 상태, 위험, 미해결 질문 | `openspec/research/{research-id}/research.md` |
| OpenSpec | 문제, 요구사항, 설계, task, change 상태 | 기존 OpenSpec artifact |
| Implement | OpenSpec task가 요구한 코드와 검증 | 코드, 테스트, 갱신된 `tasks.md` |
| Review | spec·구현·근거의 독립적 대조 | `openspec/reviews/{change-id}/{sequence}-{review-title}[-{extension}].md` |

OpenSpec 밖에 별도의 plan을 만들지 않는다.

## Run

1. [Principles](references/principles.md)와 [Workflow](references/workflow.md)를 읽는다.
1. repository에서 재사용하지 않는 안정적인 `{research-id}`를 정한다.
   - 날짜를 넣지 않은 kebab-case ID를 사용한다.
   - Research가 여러 날 이어져도 ID와 경로를 바꾸지 않는다.
1. [Research](references/research.md)를 실행한다.
   - 추가 조사 전에 기존 근거의 충분성을 판단한다.
   - [Research template](templates/research.md)로 `openspec/research/{research-id}/research.md`를 작성한다.
   - Research status가 `Ready`일 때만 다음 단계로 진행한다.
1. 기존 OpenSpec lifecycle을 실행한다.
   - 활성 OpenSpec change가 있으면 연결하고, 없으면 설치된 workflow로 새 change를 만든다.
   - Research front matter의 `relatedArtifacts`에 연결된 change ID를 기록한다.
   - proposal, specs, design, tasks는 OpenSpec이 소유한다.
   - 구현 중 발견으로 합의된 동작이 달라지면 코드보다 OpenSpec을 먼저 수정한다.
1. 승인된 task를 구현한다.
   - 변경을 작고 task 단위로 추적 가능하게 유지한다.
   - focused check를 일찍 실행하고 Review 전 필수 검증을 완료한다.
1. [Review](references/review.md)를 실행한다.
   - 지원되는 환경에서는 fresh 또는 forked context를 사용한다.
   - [Review template](templates/review.md)로 `openspec/reviews/{change-id}/{sequence}-{review-title}.md`를 작성한다.
   - `sequence`는 `001`부터 증가하는 세 자리 Review attempt 번호다. 같은 attempt의 보조 artifact만 `-{extension}` suffix를 붙인다.
   - 구현자의 설명은 코드·테스트·실행 결과가 뒷받침할 때만 근거로 인정한다.
1. verdict에 따라 자동으로 route한다.
   - `Pass` → OpenSpec으로 archive한다.
   - `Revise` → Review가 지정한 Research, OpenSpec, Implement로 돌아간다.
   - `Blocked` → blocker와 재개에 필요한 최소 행동을 보고한다.

## Autonomy

일상적인 확인을 요청하지 않고 loop를 계속한다.

다음 Human gate에서만 멈춘다.

| Gate | 예시 |
| --- | --- |
| Intent conflict | 사용자 요청과 활성 OpenSpec이 충돌 |
| Material choice | 선택에 따라 제품 동작, 호환성, 비용, 위험이 달라짐 |
| Unsafe side effect | 파괴적·비가역적·권한 필요·외부 공개 작업 |
| Missing access | 필수 저장소, 환경, secret, service에 접근 불가 |

Review가 `Pass`가 아니면 archive하지 않는다.

## Context Discipline

- phase 사이에는 chat history보다 durable artifact를 우선한다.
- 지원되는 환경에서는 [Subagents](references/subagents.md) 계약에 따라 Research와 Review를 isolated 또는 forked context에서 실행한다.
- 이전 agent의 숨은 추론이 아니라 artifact와 대상 change를 전달한다.
- main context는 조율과 사람의 결정에 집중한다.
- 현재 phase에 필요한 reference만 읽는다.

## Resource Map

| 필요 | 읽을 파일 |
| --- | --- |
| 방향과 범위 | [Vision](references/vision.md) |
| 판단 원칙 | [Principles](references/principles.md) |
| 전체 lifecycle과 routing | [Workflow](references/workflow.md) |
| Research 절차 | [Research](references/research.md) |
| Review 절차 | [Review](references/review.md) |
| Subagent·fresh context·fallback | [Subagents](references/subagents.md) |
| Windows·WSL·Copilot·Codex 적용 | [Adoption](references/adoption.md) |
| 개발 순서 | [Roadmap](references/roadmap.md) |

## Final Report

최종 결과는 짧은 표로 보고한다.

| Field | Content |
| --- | --- |
| Research | RPI Research identifier와 status |
| Change | OpenSpec change identifier |
| Implementation | 완료 task와 주요 amendment |
| Validation | 실제 실행한 check와 결과 |
| Review | `Pass`, `Revise`, `Blocked` |
| Remaining | 알려진 위험, blocker, follow-up change |
