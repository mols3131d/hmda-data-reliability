---
type: discuss
title: <title>
description: <무엇을 왜 토론하는지와 최종 판단 대상을 짧게 설명한다.>
status: "draft" # draft | in_progress | completed | blocked | superseded
discussion:
  id: <discussion-id>
  type: <explore | compare | debate | challenge | converge>
  exchange: <one-shot | cross-review | iterative>
  cadence: <manual | scheduled>
  decision_authority: <human | owning-workflow>
  # OPTIONAL: scheduled일 때만 유지한다.
  lead: A
  started_at: <timestamp>
  ends_at: <timestamp>
  active_topic: <topic-id>
  round_work: <rpi-loop | none>
# OPTIONAL: 태그가 있을 때만 필드 전체를 유지한다.
tags:
  - "<domain>"
  - "[<subdomain>]"
  - "[<capability>]"
---

<!--
작성 규칙:
- discuss artifact는 반드시 이 디렉터리를 루트로 하는 번들이다.
- README.md가 Goal, Scope, Topics, 상태, 설정, References와 기본 Synthesis를 소유한다.
- participant 발언만 rounds/에 분리한다.
- Synthesis가 커져 README 가독성을 해칠 때만 _synthesis.md를 사용해 synthesis.md로 분리한다.
- scheduled가 아니면 scheduled 전용 frontmatter 필드를 제거한다.
- OPTIONAL 블록과 빈 placeholder를 남기지 않는다.
- KISS, DRY 원칙을 지킨다.
-->

> [!NOTE]
> <현재 토론 목적과 사람이 최종적으로 결정해야 할 사항을 한 문단으로 요약한다.>

## Goal

<이 토론이 해결해야 하는 질문 또는 결정 목표>

## Scope

- **In** - <토론에 포함하는 범위>
- **Out** - <명시적으로 제외하는 범위>

## Topics

### T1. <Topic title>

- **Status** - <pending | active | paused | blocked | completed>
- **Question** - <이 Topic에서 답해야 할 질문>
- **Done When** - <종료 또는 전환 조건>

### T2. <Topic title> <!-- OPTIONAL -->

- **Status** - <pending | active | paused | blocked | completed>
- **Question** - <이 Topic에서 답해야 할 질문>
- **Done When** - <종료 또는 전환 조건>

## References

- <canonical 문서, 코드, PR, Research/Review artifact 등>

## Synthesis <!-- 토론 종료 시 작성. 커지면 synthesis.md로 분리한다. -->

### Result

<각 Topic의 결론 또는 남은 선택지>

### Evidence

- <핵심 근거와 반대 근거>

### Agreement And Disagreement

- <합의점, 남은 이견과 그 원인>

### Next

- <권장 다음 행동, 추가 Research/Validation, 인간 결정이 필요한 항목>
