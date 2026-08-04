---
type: openspec-spec-driven-tdd-plan-review
category: review
title: <title>
description: <Proposal, Specs, Design과 Tasks의 검토 범위와 결과를 짧게 설명한다.>
status: "<pending | in_progress | approved | changes_requested | blocked>"
# OPTIONAL PARSABLE TAGS: 생략하면 Proposal tags를 상속한다.
# 유지한다면 Proposal tags와 정확히 일치시킨다.
tags:
  - "domain:domain-name"
  - "subdomain:subdomain-name"
  - "capability:capability-name"
  - "tag-name"
---

<!--
작성 규칙:
- 본문 헤더는 기본적으로 서술 구조다. 예외적으로 frontmatter의 `status`와 `### Required Changes` 체크박스는 gate 파싱 계약이다.
- 구현 전 계획만 검토하며 구현 결과나 코드 품질을 판정하지 않는다.
- tags를 유지한다면 Proposal tags와 정확히 일치시키며, 생략하면 상속으로 해석한다.
- Proposal, Specs, Design과 Tasks 사이의 연결을 Evidence로 확인한다.
- 확인된 문제만 기록하고 같은 문제를 반복하지 않는다.
- 문제가 없는 영역을 형식적으로 나열하지 않는다.
- OPTIONAL 블록과 빈 placeholder를 남기지 않는다.
-->

> [!NOTE]
> <Status, 가장 중요한 근거와 다음 조치를 한 문단으로 요약한다.>

## Overview

| Target | Scope | Status |
| --- | --- | --- |
| Proposal · Specs · Design · Tasks | <검토 범위> | <Pending / In Progress / Approved / Changes Requested / Blocked> |

<!-- OPTIONAL: 검토를 제한하거나 차단한 조건이 있을 때만 추가한다.

> [!CAUTION]
> <누락된 근거, 외부 의존성 또는 검토 제한>
-->

## Traceability

| From | To | Evidence | Result |
| --- | --- | --- | --- |
| Proposal | Specs | <Capability와 Requirement 연결> | <Pass / Fail / Not Verified> |
| Specs | Design | <행동 계약과 책임 경계 연결> | <Pass / Fail / Not Verified> |
| Specs / Design | Tasks | <Scenario, 검증 전략과 작업 연결> | <Pass / Fail / Not Verified> |

<!-- OPTIONAL SECTION: 실질적인 문제가 있을 때만 유지한다. -->

## Findings

### F1. <Finding title>

- **Severity** - <Critical / Major / Minor>
- **Artifact** - <proposal | specs | design | tasks>
- **Location** - <섹션, Requirement, Scenario 또는 Task>
- **Evidence** - <확인된 사실 또는 모순>
- **Impact** - <구현 또는 검증에 미치는 영향>
- **Required Change** - <재검토 전에 필요한 수정>

## Verification

| Check | Evidence | Result |
| --- | --- | --- |
| Intent and scope are explicit | <근거> | <Pass / Fail / Not Verified> |
| Requirements are observable and testable | <근거> | <Pass / Fail / Not Verified> |
| Design satisfies Specs without unnecessary scope | <근거> | <Pass / Fail / Not Verified> |
| TDD tasks cover changed behavior | <근거> | <Pass / Fail / Not Verified> |
| Open questions and dependencies do not block Apply | <근거> | <Pass / Fail / Not Verified> |

## Status

| Decision | Rationale |
| --- | --- |
| <Pending / In Progress / Approved / Changes Requested / Blocked> | <상태를 결정한 핵심 근거> |

<!-- OPTIONAL SECTION: status가 changes_requested일 때만 유지한다. -->

### Required Changes

<!-- PARSING CONTRACT: 미완료 최상위 체크박스가 하나라도 있으면 Apply를 차단한다. -->

- [ ] <재검토 전에 반드시 해결할 변경>
