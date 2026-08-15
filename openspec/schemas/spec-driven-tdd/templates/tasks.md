---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: <title>
description: <구현 범위와 완료 목표를 짧게 설명한다.>
# DERIVED: tasks.md 본문의 파싱 대상 체크박스에서 계산한다.
tasks_completed: 0
tasks_total: 0
---

<!--
형식 규칙:
- `tasks_completed`와 `tasks_total`은 최상위 체크박스에서 계산하는 파생값이며 체크박스가 source of truth다.
- 파싱 대상 task는 줄 시작이 정확히 `- [ ]` 또는 `- [x]`인 최상위 체크박스다.
- 하나의 체크박스는 하나의 독립적으로 검증 가능한 구현 결과를 나타낸다.
- RED, GREEN, REFACTOR는 TDD 실행 단계이며 별도 progress task로 나누지 않는다.
- Review, self-review, approval과 process state를 progress task로 만들지 않는다.
- 선행 조건이 필요하면 일반 목록으로 기록하고 task counter에 포함하지 않는다.
- 빈 섹션이나 placeholder를 남기지 않는다.
-->

## Tasks

### 1. <Workstream>

- [ ] 1.1 <독립적으로 검증 가능한 구현 결과>
  - **Covers:** `<requirement or scenario>`
  - **Test first:** <행동 변경이면 먼저 실패로 고정할 관찰값>
  - **Done when:** <객관적으로 확인 가능한 완료 조건>

- [ ] 1.2 <다음 구현 결과>
  - **Done when:** <객관적으로 확인 가능한 완료 조건>
