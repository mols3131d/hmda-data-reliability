---
title: <title>
description: <무엇을 왜 조사하는 문서인지, 주요 범위와 판단 대상을 짧게 설명한다.>
status: "draft" # draft | in_progress | completed | blocked | superseded
# OPTIONAL: 태그가 있을 때만 필드 전체를 유지한다.
tags:
  - "<domain>"
  - "[<subdomain>]"
  - "[<capability>]"
  - "[<field>]"
  - "[<tag>]"
  - "[<...>]"
---

<!--
작성 규칙:
- 조사 질문에 답하고 다음 판단에 필요한 내용만 남긴다.
- 사실, 해석과 추론을 구분하고 주요 주장을 Evidence와 연결한다.
- 원시 자료는 evidence.md, 실행 로그는 runtime-output.md로 분리한다.
- 충분한 근거가 확보되면 조사를 종료한다.
- OPTIONAL 블록과 빈 placeholder를 남기지 않는다.
- KISS, DRY 원칙 준수.
- 템플릿의 규모 보다 내용이 커지면 다른 문서로 분리한다.
-->

> [!NOTE]
> <핵심 결론, 가장 중요한 근거와 다음 판단을 한 문단으로 요약한다.>

## Question

<조사의 목적과 핵심 질문들을 KISS하게 작성한다.>

### Scope

- <포함 범위와 제외 범위>

### Stop Condition <!-- OPTIONAL: 조사 종료 기준을 명시할 필요가 있을 때만 추가한다. -->

<!--
> [!CAUTION]
> <결론의 한계 또는 불확실성>
-->

- <조사를 종료할 충분한 근거를 KISS하게 작성한다.>

## Findings

### F1. <Finding>

<확인된 사실 또는 분석 결과>[^evidence_name]

#### [<...>]

[<...>][^evidence_name][^evidence_name_2][^tmi_detail]

### [F0. <...>]

[<...>]

## Options <!-- OPTIONAL SECTION: 여러 선택지를 비교해야 할 때만 유지한다. -->

<!--
비교 방식은 목적에 따라 하나를 선택하고, 사용하지 않는 형식은 삭제한다.
- 각 옵션의 특성과 trade-off를 설명하는 것이 중요하면 Strengths / Weaknesses 형식을 사용한다.
- 여러 옵션을 동일한 기준으로 직접 비교해야 하면 Comparison Matrix를 사용한다.
-->

### <Option 1>

<옵션에 대한 설명>

| Strengths | Weaknesses |
| --------- | ------------ |
| <장점 1> | <단점 또는 제약 1> |
| <장점 2> | <단점 또는 제약 2> |

### <Option 2>

<옵션에 대한 설명>

| Strengths | Weaknesses |
| --------- | ------------ |
| <장점 1> | <단점 또는 제약 1> |
| <장점 2> | <단점 또는 제약 2> |

<!-- OR: 동일 기준 비교가 더 적합한 경우 아래 형식을 사용한다. -->

| Criterion | <Option 1> | <Option 2> | <Option 3> |
| --------- | ---------- | ---------- | ---------- |
| <비교 기준 1> | <평가> | <평가> | <평가> |
| <비교 기준 2> | <평가> | <평가> | <평가> |
| <비교 기준 3> | <평가> | <평가> | <평가> |

## Conclusion

### <Conclusion 1>

<핵심 질문 해소를 위한 정보들을 KISS하게 작성하고, 근거와 연결한다>

#### <...>

...

#### Recommendation & Next Step

<권장 방향과 이유> & <다음 행동 또는 추가 확인>

## Open Questions <!-- OPTIONAL SECTION: 현재 근거로 답할 수 없는 중요한 질문이 있을 때만 유지한다. -->

| Question | Why It Matters | Next Step |
| --- | --- | --- |
| <질문> | <결정에 미치는 영향> | <확인 방법> |

[^evidence_name]: evidence
[^evidence_name_2]: evidence
<!-- [^evidence_{근거의 케밥 케이스 이름}]: 근거 경로, line number 등 식별 정보와 간략한 설명 -->
[^tmi_detail]: detail
<!-- [^footnote_name]: 중요도는 낮지만, 많은 분량을 가진 정보를 풋노트에 작성 -->
