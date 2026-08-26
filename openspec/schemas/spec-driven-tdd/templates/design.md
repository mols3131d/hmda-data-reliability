---
type: openspec-spec-driven-tdd-design
category: design
title: <title>
description: <핵심 technical delta 또는 추가 설계 판단이 없음을 한 문장으로 설명한다.>
---

<!--
작성 규칙:
- Proposal과 Specs는 Design의 입력이지 다시 요약할 내용이 아니다.
- 각 candidate를 다음 순서로 분류한다.
  1. Why, scope, impact인가? → Proposal.
  2. 외부에서 관찰하거나 Requirement/Scenario로 검증할 수 있는 behavior, failure, acceptance, contract인가? → Specs.
  3. 구현 결과나 완료 조건인가? → Tasks.
  4. 제거하면 구현 선택, 변경되는 technical boundary, constraint 또는 migration mechanism이 실질적으로 미정이 되는가? → Design.
- 기술 용어를 사용하거나 implementation과 관련 있다는 이유만으로 Design에 넣지 않는다.
- upstream context가 꼭 필요하면 owning artifact나 Requirement를 짧게 참조하고 새로운 technical delta만 설명한다.
- 하나의 technical delta는 Design 안에서도 한 번만 기록한다. 같은 판단을 요약문, Decision, 표나 Mermaid로 반복하지 않는다.
- 추가 technical delta가 없으면 `기존 architecture를 따른다.` 한 문장으로 끝낸다.
-->

## Technical Delta

<단순한 선택은 한 문장으로 기록한다. 여러 비자명한 선택이 있으면 아래 Decision 형식을 사용하고 별도 요약문을 반복하지 않는다.>

<!-- OPTIONAL: 여러 구현 선택지 중 하나를 고정해야 할 때 필요한 항목만 추가한다.

### D1. <Decision>

- **Decision:** <선택한 접근법>
- **Rationale:** <이 선택이 필요한 기술적 이유>
- **Trade-off:** <중요한 비용이 있을 때만 기록>
-->

<!-- OPTIONAL: 새로 만들거나 변경하는 technical responsibility boundary 자체가 결정일 때 사용한다. 같은 boundary를 Decision으로 다시 설명하지 않는다.

### Boundary Changes

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| `<boundary>` | <새로 정하거나 변경하는 기술적 책임> | <인접 구현 책임> |
-->

<!-- OPTIONAL: migration의 strategy, ordering constraint 또는 compatibility mechanism 자체가 결정일 때 사용한다. 실제 작업 순서와 완료 조건은 Tasks에 맡긴다.

### Migration Strategy

- <전환 전략 또는 compatibility mechanism>
-->
