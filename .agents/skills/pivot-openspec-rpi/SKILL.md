---
name: pivot-openspec-rpi
description: |
   Coordinate Project Pivot's human-centered Research → OpenSpec → Implement → Review workflow for non-trivial development and operational changes. Use when a task has uncertainty, spans multiple files, changes behavior or architecture, depends on external APIs, or needs evidence-backed validation. Use with existing OpenSpec changes or to create a new change without forking OpenSpec. Do not use for trivial edits, simple formatting, or requests that do not require implementation.
---

# Pivot OpenSpec RPI

OpenSpec을 Single Source of Truth로 관리하는 Research → OpenSpec → Implement → Review 워크플로우 지침입니다.

- **원칙**: OpenSpec 커스텀 스키마를 생성하지 않으며, Research와 Review는 독립적인 Decorator 아티팩트로 연결합니다.
- **독립성**: 각 Phase는 독립 시작 가능하나, 시작 및 마감을 위한 입력/출력 아티팩트 계약(Contract)을 준수해야 합니다.

## Operating Model

| Phase | 주요 책임 | Canonical Artifact 경로 |
| --- | --- | --- |
| **Research** | 문제 정의, 현황 조사, 위험 분석, 근거 수집 | `openspec/research/{research-id}/*` 번들 (임시)<br/>`openspec/research/archive/{research-id}/*` 번들 (보관 시) |
| **OpenSpec** | 문제, 요구사항, 설계, task, change 상태 관리 | 기존 OpenSpec 커스텀 변경 아티팩트 (`proposal.md`, `design.md`, `specs/`, `tasks.md`) |
| **Implement** | 승인된 OpenSpec task 기반 코드 구현 및 테스트 검증 | 소스 코드, 유닛/통합 테스트, 갱신된 `tasks.md` |
| **Review** | spec·구현·근거의 독립적 대조 및 판정 | `openspec/reviews/{change-id}/{sequence}-{review-title}[-{extension}].md` |

OpenSpec 밖에 별도의 plan을 만들지 않는다.

## Entry Routing Algorithm

1. **상태 파악**: [Principles](references/principles.md) 및 [Workflow](references/workflow.md)를 참조하여 현재 요청의 목표 Phase를 선정한다.
1. **입력 계약(Input Contract) 검증**:
   - 목표 Phase 실행에 필요한 아티팩트가 존재하고 유효한지 확인한다.
   - 아티팩트 미비 또는 신뢰 불가 시, 해당 아티팩트 소유(Owner) Phase로 우회(Route)한다.
   - 이미 검증된 아티팩트가 존재할 경우 이전 Phase를 재실행하지 않는다.
1. **Phase별 진입 규칙**:
   - **Research**: 안정적인 `{research-id}` (kebab-case, 날짜 미포함) 생성 후 [Research](references/research.md) 지침에 따라 임시 번들 작성.
   - **OpenSpec**: 설치된 OpenSpec 커맨드 및 절차 준수 ([Workflow](references/workflow.md)).
   - **Implement**: 승인된 태스크(`tasks.md`) 확인 후 구현 진행.
   - **Review**: Active OpenSpec, 구현 diff, 실제 검증 결과를 확보하고 [Review](references/review.md) 지침에 따라 독립 검토 수행.

## Durable Phase Reports & Chat Handoff

- **보고서 원칙**: 모든 세부 분석, 근거, 결과는 채팅이 아닌 해당 Phase의 **Canonical Artifact**에 기록한다.
- **채팅 출력 제한**: 최종 채팅 답변은 아래 Handoff 테이블 규격(경로, 상태, 다음 Routing)으로 1~3줄 이내 요약 전송한다.

| Field | Content |
| --- | --- |
| **Research** | Research 아티팩트 경로 및 상태 (`draft`, `in_progress`, `completed`, `blocked`) |
| **Change** | OpenSpec Change ID 및 상태 |
| **Implementation** | 구현/수정된 태스크 아티팩트 경로 및 실행한 검증 명령 |
| **Validation** | 테스트 실행 결과 요약 및 리포트 경로 |
| **Review** | Review 아티팩트 경로 및 판정 (`approved`, `changes_requested`, `blocked`) |
| **Next Phase** | 다음 진행할 소유(Owner) Phase 또는 차단(Blocker) 사유 |

## Autonomy & Human Gates

Agent는 다음 **Human Gate** 조건 발동 시에만 진행을 멈추고 사용자에게 승인을 요청한다.

| Gate | 조건 및 발동 기준 |
| --- | --- |
| **Intent Conflict** | 사용자 요청과 기존 OpenSpec 명세가 충돌할 때 |
| **Material Choice** | 제품 동작, 아키텍처, 호환성, 비용에 영향을 주는 대안 선택 시 |
| **Research Archive** | 임시 Research 번들을 영구 보관(`openspec/research/archive/` 이동 및 Git 커밋)하고자 할 때 |
| **Unsafe Side Effect** | 비가역적 데이터 삭제, 외부 권한 필요, 파괴적 명령 실행 시 |
| **Missing Access** | 필수 환경, 파일, 시크릿, 외부 서비스 접근 불가 시 |

## Context Discipline

- phase 사이에는 chat history보다 durable artifact를 우선한다.
- 이전 agent의 숨은 추론이 아니라 artifact와 대상 change를 전달한다.
- main context는 조율과 사람의 결정에 집중한다.
- 현재 phase에 필요한 reference만 읽는다.

## Resource Map

| 주제 | 참조 문서 |
| --- | --- |
| 핵심 판단 원칙 | [Principles](references/principles.md) |
| 전체 Lifecycle 및 Handoff 규칙 | [Workflow](references/workflow.md) |
| Research 상세 수행 절차 | [Research](references/research.md) |
| Review 상세 수행 절차 | [Review](references/review.md) |
| 개발 환경 적용 (Windows/WSL/VSCode) | [Adoption](references/adoption.md) |
