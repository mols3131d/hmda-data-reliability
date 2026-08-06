---
type: openspec-rpi
category: research
title: <title>
description: <조사 질문, 범위와 결론을 짧게 설명한다.>
status: "<draft | in_progress | completed | blocked | superseded>"
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
- 조사 질문에 답하고 다음 판단에 필요한 내용만 남긴다.
- 사실, 해석과 추론을 구분하고 주요 주장을 Evidence와 연결한다.
- 원시 자료는 evidence.md, 실행 로그는 runtime-output.md로 분리한다.
- 충분한 근거가 확보되면 조사를 종료한다.
- OPTIONAL 블록과 빈 placeholder를 남기지 않는다.
-->

> [!NOTE]
> <핵심 결론, 가장 중요한 근거와 다음 판단을 한 문단으로 요약한다.>

## Question

- **Primary:** <핵심 질문>
- **Scope:** <포함 범위와 제외 범위>
- **Stop Condition:** <조사를 종료할 충분한 근거>

<!-- OPTIONAL: 결론을 제한하는 근거 부족이나 제약이 있을 때만 추가한다.

> [!CAUTION]
> <한계 또는 불확실성>
-->

## Findings

### F1. <Finding>

<확인된 사실 또는 분석 결과>

- **Evidence** - <문서, 코드, 실험 또는 실행 결과>
- **Implication** - <결정에 미치는 의미>

<!-- OPTIONAL SECTION: 여러 선택지를 비교해야 할 때만 유지한다. -->

## Options

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| <선택지> | <장점> | <단점 또는 제약> |

## Conclusion

- **Answer** - <핵심 질문에 대한 답>
- **Recommendation** - <권장 방향과 이유>
- **Next Step** - <다음 행동 또는 추가 확인>

## Evidence

| Evidence | Supports | Location |
| --- | --- | --- |
| <문서, 코드, 실험 또는 관찰> | <뒷받침하는 Finding> | <경로, 링크 또는 참조> |

<!-- OPTIONAL SECTION: 현재 근거로 답할 수 없는 중요한 질문이 있을 때만 유지한다. -->

## Open Questions

| Question | Why It Matters | Next Step |
| --- | --- | --- |
| <질문> | <결정에 미치는 영향> | <확인 방법> |
