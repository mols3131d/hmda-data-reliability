---
type: review
category: review
title: <title>
description: <검토 대상, 범위와 결과를 짧게 설명한다.>
status: "<pending | in_progress | completed | blocked>"
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
- 검토 대상 revision, Evidence, Finding과 판정을 연결한다.
- 확인된 문제만 기록하고 같은 문제를 반복하지 않는다.
- 문제가 없는 영역을 형식적으로 나열하지 않는다.
- OPTIONAL 블록과 빈 placeholder를 남기지 않는다.
-->

> [!NOTE]
> <Verdict, 가장 중요한 근거와 다음 조치를 한 문단으로 요약한다.>

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| <검토 대상> | <commit, branch, path 또는 version> | <검토 범위> | <Pass / Revise / Blocked> |

<!-- OPTIONAL: 검토를 제한하거나 차단한 조건이 있을 때만 추가한다.

> [!CAUTION]
> <누락된 근거, 외부 의존성 또는 검토 제한>
-->

<!-- OPTIONAL SECTION: 실질적인 문제가 있을 때만 유지한다. -->

## Findings

### F1. <Finding title>

- **Severity** - <Critical / Major / Minor>
- **Location** - <문서, Requirement, 파일 또는 동작>
- **Evidence** - <확인된 관찰 결과>
- **Impact** - <수정하지 않을 때의 영향>
- **Required Change** - <필요한 수정 또는 충족 조건>

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| <검증 항목> | <테스트, 문서 또는 관찰 근거> | <Pass / Fail / Not Verified> |

<!-- OPTIONAL SECTION: 필수 수정은 아니지만 후속 가치가 있을 때만 유지한다. -->

## Remaining Risks

- <남은 위험, 제한 또는 후속 확인>

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| <Pass / Revise / Blocked> | <판정을 결정한 핵심 근거> | <owning artifact, PR, Issue 또는 후속 Change> |
