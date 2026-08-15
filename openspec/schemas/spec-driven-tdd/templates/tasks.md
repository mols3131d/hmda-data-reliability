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
- parser는 줄 시작이 정확히 `- [ ]` 또는 `- [x]`인 모든 최상위 체크박스를 progress로 집계한다.
- 최상위 체크박스는 독립적으로 검증 가능한 구현 결과에만 사용한다.
- RED, GREEN, REFACTOR는 TDD 실행 단계이며 별도 progress task로 나누지 않는다.
- Review, self-review, 승인 대기 같은 process/gate state는 Tasks에 기록하지 않는다.
- 구현에 필요한 선행 조건은 필요할 때만 일반 text나 list로 기록한다.
- 각 task에는 객관적인 `Done when`을 둔다.
- 빈 섹션이나 placeholder를 남기지 않는다.

필요할 때만 task 아래에 다음 metadata를 추가한다.
- `Covers`: Requirement 또는 Scenario 추적이 제목만으로 명확하지 않을 때
- `Test first`: 행동 변경에서 먼저 실패로 고정할 관찰값이 명확화에 도움될 때
-->

## Tasks

- [ ] <독립적으로 검증 가능한 구현 결과>
  - **Done when:** <객관적으로 확인 가능한 완료 조건>

- [ ] <다음 구현 결과>
  - **Done when:** <객관적으로 확인 가능한 완료 조건>
