---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: <title>
description: <description>
# OPTIONAL PARSABLE TAGS: Change-level 분류의 source of truth다.
# 허용 형식: tag | domain:tag | subdomain:tag | capability:tag
tags:
  - "domain:domain-name"
  - "subdomain:subdomain-name"
  - "capability:capability-name"
  - "tag-name"
---

<!--
작성 규칙:
- `## Capabilities`, `### New Capabilities`, `### Modified Capabilities`와 Capability 이름 헤더는 파싱 계약으로 유지한다.
- tags는 Change-level 분류의 source of truth이며 Capability 선언과 일치시킨다.
- OPTIONAL 블록은 내용이 있을 때만 유지한다.
- 빈 섹션, 표, 목록과 placeholder를 남기지 않는다.
- 고정된 필드와 섹션 이름은 영어를 유지한다.
-->

> [!NOTE]
> <변경 이유, 핵심 변경과 기대 결과를 한 문단으로 요약한다.>

## Overview

| Why | What | Capabilities |
| --- | --- | --- |
| <변경 이유> | <핵심 변경> | `<capability>` |

<!-- OPTIONAL: 중요한 전제나 반드시 지켜야 하는 제약이 있을 때만 추가한다.

> [!IMPORTANT]
> <중요한 전제 또는 제약>
-->

<!-- OPTIONAL: 위험, 호환성 문제 또는 특별한 주의점이 있을 때만 추가한다.

> [!CAUTION]
> <주의 사항>
-->

## Why

<!-- 문제 또는 기회와 왜 지금 변경해야 하는지를 설명한다. -->

<변경 배경과 동기>

## What Changes

<!-- 외부에서 관찰 가능한 변경만 작성하고 해당하지 않는 항목은 삭제한다. -->

- **Add:** <새로운 행동 또는 Capability>
- **Modify:** <변경되는 기존 행동>
- **Remove:** <제거되는 행동>
- **BREAKING:** <호환되지 않는 변경>

## Boundaries

| In Scope | Out of Scope |
| --- | --- |
| <이번 변경이 책임지는 범위> | <의도적으로 다루지 않는 범위> |

## Capabilities

<!-- OPTIONAL SECTION: 새로운 Capability가 있을 때만 유지한다. -->

### New Capabilities

#### `<capability>`

- <Capability가 담당하는 행동과 경계>

<!-- OPTIONAL SECTION: 기존 Requirement 또는 관찰 가능한 계약이 바뀔 때만 유지한다. -->

### Modified Capabilities

#### `<existing-capability>`

- <변경되는 Requirement 또는 행동>

## Impact

<!-- 실질적인 영향이 있는 행만 유지한다. -->

| Area | Impact |
| --- | --- |
| Code / Systems | <영향> |
| Data / Contracts | <영향> |
| Interfaces / APIs | <영향> |
| Operations / Dependencies | <영향> |

<!-- OPTIONAL SECTION: 검토한 대안이나 중요한 Trade-off가 있을 때만 유지한다. 빈 하위 섹션은 삭제한다. -->

## Appendix

### Alternatives

| Alternative | Why Rejected |
| --- | --- |
| <대안> | <기각 이유> |

### Trade-offs

| Choice | Gain | Cost |
| --- | --- | --- |
| <선택> | <얻는 것> | <감수하는 것> |
