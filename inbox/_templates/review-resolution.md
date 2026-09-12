---
type: review-resolution
title: <title>
description: <어떤 review finding을 어떤 범위에서 해소했는지 한 문장으로 설명한다.>
# OPTIONAL: 검색·회수에 실제 도움이 되는 분류만 유지한다.
tags:
  - "domain:<domain>"
  - "capability:<capability>"
  - "<tag>"
---

# <title>

> [!IMPORTANT]
> **<Resolved | Partial | Blocked>** — <전체 해소 상태와 가장 중요한 결과 또는 필요한 다음 조치를 1~3문장으로 요약한다.>

- **Source Review** — <linked review artifact>
- **Review Revision** — `<revision reviewed by the source review>`
- **Resolution Revision** — `<revision containing the resolution>`
- **Scope** — <이번 resolution에서 다룬 finding과 범위>

## Findings

<!-- Source Review의 stable finding ID를 그대로 사용한다. -->

| ID | Disposition | Resolution | Verification |
| --- | --- | --- | --- |
| F1 | <Resolved | No Change | Deferred | Blocked> | <적용한 변경 또는 disposition의 핵심 근거> | <검증 결과 또는 evidence> |

## Details <!-- OPTIONAL: summary만으로 resolution을 판단하기 어려운 finding만 작성한다. -->

### F1 · <finding title>

#### Locations

- <linked file or artifact>
  - `<symbol, test, requirement 또는 section>`

#### Resolution

<실제로 변경한 내용 또는 변경하지 않은 이유를 설명한다.>

#### Verification

<finding이 해소되었는지 확인하기 위해 수행한 검증과 그 결과를 설명한다.>

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| <✅ Pass / ❌ Fail / ⚪ Not Verified> | <검증 항목> | <테스트, 문서 또는 관찰 근거> |

## Risks and Limits <!-- OPTIONAL -->

- <남아 있는 위험, 미해소 finding, 검증 한계 또는 재검토 조건>
