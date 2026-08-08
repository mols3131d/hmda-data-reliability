---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: <title>
description: <구현 범위와 완료 목표를 짧게 설명한다.>
# DERIVED: tasks.md 본문의 파싱 대상 체크박스에서 계산한다.
tasks_completed: 0
tasks_total: 0
# OPTIONAL PARSABLE TAGS: 생략하면 Proposal tags를 상속한다.
# 유지한다면 Proposal tags와 정확히 일치시킨다.
tags:
  - "domain:domain-name"
  - "subdomain:subdomain-name"
  - "capability:capability-name"
  - "tag-name"
---

<!--
형식 규칙:
- `tasks_completed`와 `tasks_total`은 생성된 Change artifact의 체크박스에서 계산하는 파생값이며 체크박스가 원본이다.
- schema template의 초기값은 0이며 생성 또는 갱신 직후 재계산한다.
- tags를 유지한다면 Proposal tags와 정확히 일치시키며, 생략하면 상속으로 해석한다.
- 파싱 대상 작업은 줄 시작이 정확히 `- [ ]` 또는 `- [x]`인 최상위 체크박스다.
- 빈 섹션, 목록과 placeholder를 남기지 않는다.
-->

> [!NOTE]
> <구현 범위, 핵심 순서와 전체 완료 기준을 한 문단으로 요약한다.>

<!-- OPTIONAL SECTION: 구현 전에 충족해야 할 외부 조건이 있을 때만 유지한다. -->

## Prerequisites

- [ ] <선행 조건을 확인한다.>
  - **Done when:** <충족 여부를 확인할 근거>

## Tasks

<!--
PARSING CONTRACT:
- 작업 체크박스는 들여쓰기 없이 줄 시작에서 `- [ ]` 또는 `- [x]`를 사용한다.
- 체크 상태는 소문자 `x`로 기록한다.
- `Covers`, `Done when` 같은 메타데이터는 체크박스로 작성하지 않는다.
- fenced code block과 HTML comment 안의 예시는 집계하지 않는다.
-->

### 1. <Workstream>

- [ ] 1.1 **RED** — <기대 행동을 고정하는 실패 테스트를 작성한다.>
  - **Covers:** `<requirement or scenario>`
  - **Done when:** <의도한 이유로 실패한다.>

- [ ] 1.2 **GREEN** — <테스트를 통과하는 최소 구현을 작성한다.>
  - **Done when:** <관련 행동과 테스트가 통과한다.>

- [ ] 1.3 **REFACTOR** — <중복과 불필요한 복잡성을 제거한다.>
  - **Done when:** <행동을 유지하면서 구조가 단순해진다.>

### 2. <Workstream>

- [ ] 2.1 <독립적으로 실행하고 검증할 작업>
  - **Done when:** <객관적인 완료 조건>

<!-- OPTIONAL SECTION: 데이터, 스키마, 배포 또는 호환성 전환이 있을 때만 유지한다. -->

## Migration

- [ ] <전환 또는 롤백 작업>
  - **Done when:** <완료를 확인할 근거>

## Self-Review

- [ ] 모든 관련 Requirement와 Scenario가 구현 및 테스트에 반영되었는지 확인한다.
- [ ] Design의 Decision과 Boundary를 지키면서 중복과 불필요한 복잡성을 제거한다.
- [ ] 관련 테스트, 실패 경로와 정적 검사가 통과하는지 확인한다.
- [ ] 필요한 문서, 설정과 운영 절차를 갱신한다.
- [ ] 알려진 제약과 후속 작업을 명시한다.
