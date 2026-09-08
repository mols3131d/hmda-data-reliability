---
type: review
title: <title>
description: <검토 대상과 검토 목적을 한 문장으로 설명한다.>
# OPTIONAL: 검색·회수에 실제 도움이 되는 분류만 유지한다.
tags:
  - "domain:<domain>"
  - "capability:<capability>"
  - "<tag>"
---

# <title>

> [!IMPORTANT]
> **<Pass | Revise | Blocked>** — <핵심 판정과 가장 중요한 이유, 필요한 다음 조치를 1~3문장으로 요약한다.>

| Target | Revision | Scope |
| --- | --- | --- |
| <linked target> | `<revision>` | <실제로 검토한 범위> |

## Findings

<!-- Finding이 없으면 table 대신 "확인된 finding 없음."으로 작성한다. -->

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | <severity> | <문제 또는 관찰을 한 문장으로 요약> | <필요한 조치> |

## Details <!-- OPTIONAL: summary만으로 판단하기 어려운 finding만 작성한다. -->

### F1 · <finding title>

<severity>

#### Locations

- <linked file or artifact>
  - `<symbol, test, requirement 또는 section>`

#### Evidence

<확인한 사실과 finding의 근거를 설명한다.>

#### Impact

<수정하지 않을 때의 실제 영향이나 위험을 설명한다.>

#### Action

<필요한 변경 또는 충족 조건을 설명한다.>

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| <✅ Pass / ❌ Fail / ⚪ Not Verified> | <검증 항목> | <테스트, 문서 또는 관찰 근거> |

## Risks and Limits <!-- OPTIONAL -->

- <남아 있는 위험, 검토 범위의 제한 또는 재검토 조건>
