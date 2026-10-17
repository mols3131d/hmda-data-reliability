---
type: review
title: <title>
description: <검토 대상과 다관점 리뷰의 목적·범위를 한 문장으로 설명한다.>
# OPTIONAL: 검색·회수에 실제 도움이 되는 분류만 유지한다.
tags:
  - "domain:<domain>"
  - "capability:<capability>"
  - "<tag>"
---

# <title>

> [!IMPORTANT]
> **<Pass | Revise | Blocked>** — <최종 판정, 핵심 근거와 필요한 다음 조치를 1~3문장으로 요약한다.>

- **Target** — <linked target>
- **Revision** — `<revision>`
- **Scope** — <실제로 검토한 범위>

## Findings

<!-- 수용한 후보 중 실제 근거가 확인된 최종 finding만 기록한다. 드랍·미해결 후보는 넣지 않는다. -->
<!-- Finding이 없으면 table 대신 "확인된 finding 없음."으로 작성한다. -->

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | <severity> | <검증된 문제 또는 관찰> | <필요한 조치> |

## Perspectives

<!-- 실제 수행한 관점만 기록한다. 서로 다른 관점과 독립된 리뷰 수행을 혼동하지 않는다. -->
<!-- 주요 주장·반론·견해 차이와 근거를 짧게 남긴다. -->

| Perspective | Reviewer / Method | Focus | Assessment and Evidence |
| --- | --- | --- | --- |
| <정확성·보안·운영성 등 실제 관점> | <검토 주체와 방법; 동일 컨텍스트 여부> | <확인한 범위> | <주장·반론·증거 링크> |

## Candidate Decisions

<!-- 관점별 후보를 중복 제거해 C1, C2...로 식별한다. 같은 후보를 여러 관점에서 제시했다면 한 행에 묶는다. -->
<!-- Accept는 확인된 최종 Finding ID에 연결한다. Drop에는 구체적인 근거를 남긴다. -->
<!-- Open은 해결된 것으로 간주하지 않고 Risks and Limits에 검증 또는 결정 조건을 기록한다. -->

| ID | Perspectives | Candidate | Decision | Rationale | Finding |
| --- | --- | --- | --- | --- | --- |
| C1 | <관점 또는 검토 주체> | <후보 의견> | <Accept / Drop / Open> | <수용 근거, 드랍 이유 또는 미해결 사유와 증거> | <F1 또는 —> |

## Details <!-- OPTIONAL: 최종 finding의 summary만으로 판단하기 어려울 때 작성한다. -->

### F1 · <finding title>

<severity>

#### Locations

- <linked file or artifact>
  - `<symbol, test, requirement 또는 section>`

#### Evidence

<직접 확인한 사실, 기존 safeguard와 반론을 검토한 근거를 설명한다.>

#### Impact

<수정하지 않을 때의 실제 영향이나 위험을 설명한다.>

#### Action

<필요한 변경 또는 충족 조건을 설명한다.>

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| <✅ Pass / ❌ Fail / ⚪ Not Verified> | <실제로 수행한 검증 또는 확인하지 못한 항목> | <테스트, 문서 또는 관찰 근거; 미검증 이유> |

## Risks and Limits <!-- OPTIONAL -->

- <C-ID가 Open인 경우 필요한 추가 검증·결정과 담당 주체, 관점 간 미해결 견해 차이 또는 review coverage 제한>
