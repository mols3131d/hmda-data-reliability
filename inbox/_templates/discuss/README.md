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
- 토론 목적, 범위, 설정과 공유 참조만 이 파일이 소유한다.
- Topic 상태는 topics.md, participant 발언은 rounds/, 최종 종합은 synthesis.md가 소유한다.
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

## References

- <canonical 문서, 코드, PR, Research/Review artifact 등>

## Bundle

- [`topics.md`](topics.md) - Topic과 상태
- `rounds/` - A/B의 immutable turn
- `synthesis.md` - 토론 종료 시 생성하는 최종 종합
