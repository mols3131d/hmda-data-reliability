---
type: openspec-rpi
category: tasks
title: <title>
description: <구현 범위와 완료 목표를 짧게 설명한다.>
# DERIVED: 본문의 모든 체크박스에서 계산한다.
tasks_completed: 0
tasks_total: 0
# OPTIONAL: 태그가 있을 때만 필드 전체를 유지한다.
tags:
  - "<domain>"
  - "<subdomain>"
  - "<capability>"
  - "<field>"
  - "<tag>"
---

<!--
작성 규칙:
- 모든 실행 작업은 완료 여부를 검증할 수 있는 체크박스로 작성한다.
- 의존성 순서로 배치하고 하나의 작업에는 하나의 결과만 둔다.
- 행동 변경은 가능한 한 RED → GREEN → REFACTOR로 구성한다.
- Specs와 Design의 설명을 반복하지 않는다.
- 빈 섹션, 목록과 placeholder를 남기지 않는다.
-->

> [!NOTE]
> <구현 범위, 핵심 순서와 전체 완료 기준을 한 문단으로 요약한다.>

<!-- OPTIONAL SECTION: 구현 전에 충족해야 할 외부 조건이 있을 때만 유지한다. -->

## Prerequisites

- [ ] <선행 조건을 확인한다.>
  - **Done when:** <충족 여부를 확인할 근거>

## Tasks

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
