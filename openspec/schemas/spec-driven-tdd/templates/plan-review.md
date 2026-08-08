---
type: openspec-spec-driven-tdd-plan-review
category: review
title: <title>
description: <계획 검토 범위와 현재 결과를 짧게 설명한다.>
status: "<pending | in_progress | approved | changes_requested | blocked>"
review_loop: 0
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
- review_loop는 0부터 8까지의 정수다.
- checklist 항목과 Required Changes는 같은 checklist ID를 사용한다.
- 통과 항목의 상세 설명과 빈 Required Changes section은 남기지 않는다.
-->

# Plan Review

## Checklist

- [ ] **C1 — Intent and Scope:** Proposal의 목적, 범위와 Capability 선언이 명확하고 일치한다.
- [ ] **C2 — Behavior Contracts:** Specs가 변경 행동과 중요한 실패·경계를 검증 가능하게 정의한다.
- [ ] **C3 — Technical Approach:** Design이 Specs를 충족하고 주요 책임 경계, 위험과 미해결 결정을 다룬다.
- [ ] **C4 — TDD Execution:** Tasks가 변경 행동을 빠짐없이 다루며 검증 가능한 TDD 순서와 완료 조건을 가진다.
- [ ] **C5 — Consistency and Readiness:** Artifact가 일관되고 추적 가능하며 Apply를 막는 문제가 없다.

<!-- OPTIONAL: 미통과 항목이 있을 때만 유지한다. -->

### Required Changes

<!-- PARSING CONTRACT: 미완료 최상위 checkbox가 하나라도 있으면 Apply를 차단한다. -->

- [ ] **<C1-C5> — <미통과 기준>**
  - **Target:** <artifact>
  - **Location:** <section, Requirement, Scenario 또는 Task>
  - **Evidence:** <확인된 누락 또는 모순>
  - **Impact:** <구현 또는 검증에 미치는 영향>
  - **Required Change:** <통과에 필요한 변경>
