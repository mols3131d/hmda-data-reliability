---
type: discuss
title: <title>
description: <무엇을 왜 토론하는지와 최종 판단 대상을 짧게 설명한다.>
status: "draft" # draft | in_progress | completed | blocked | superseded
discussion:
  id: <discussion-id>
  type: <explore | compare | debate | challenge | converge>
  exchange: <one-shot | cross-review | iterative>
  execution: <manual | scheduled | chatbot-active-session>
  phase: <frame | evidence | dialectic | converge>
  decision_authority: <human | owning-workflow>
  lead: A
  active_topic: <topic-id>
  # OPTIONAL: dialectic phase에서 cycle을 구분할 가치가 있을 때만 유지한다.
  dialectic_cycle: <positive-integer>
# OPTIONAL: 태그가 있을 때만 필드 전체를 유지한다.
tags:
  - "<domain>"
  - "[<subdomain>]"
  - "[<capability>]"
---

<!--
작성 규칙:
- discuss artifact는 반드시 이 디렉터리를 루트로 하는 bundle이다.
- README.md가 Goal, Scope, Decision Criteria, Roles, Topics, phase/current state, References와 기본 Synthesis를 소유한다.
- participant contribution만 turns/에 분리한다.
- turn 파일명은 <sequence>-<participant>.md만 사용한다.
- 예: 001-a.md, 002-b.md, 003-a.md
- 각 turn은 discuss.md의 phase contract와 Turn Workflow를 따른다.
- Lead는 coordination을 소유하지만 truth, tie-break 또는 final decision을 소유하지 않는다.
- Synthesis가 커져 README 가독성을 해칠 때만 _synthesis.md를 사용해 synthesis.md로 분리한다.
- scheduled/chatbot runtime metadata는 해당 discuss-*.md extension에서 실제로 요구할 때만 추가한다.
- OPTIONAL 블록과 빈 placeholder를 남기지 않는다.
- KISS, DRY 원칙을 지킨다.
-->

> [!NOTE]
> <현재 토론 목적, 현재 phase와 사람이 최종적으로 결정해야 할 사항을 한 문단으로 요약한다.>

## Goal

<이 토론이 해결해야 하는 정확한 질문 또는 결정 목표>

## Scope

- **In** - <토론에 포함하는 범위>
- **Out** - <명시적으로 제외하는 범위>

## Decision Criteria

- <대안을 판단할 핵심 criterion 또는 constraint>
- <필요한 경우 추가 criterion>

## Roles

- **Lead** - <A 또는 B>; coordination과 shared-state authoring만 소유한다.
- **A** - <독립 participant 역할 또는 관점; 고정 찬반 진영으로 정의하지 않는다.>
- **B** - <독립 participant 역할 또는 관점; 고정 찬반 진영으로 정의하지 않는다.>
- **Decision Authority** - <human 또는 owning workflow>

## Topics

### T1. <Topic title>

- **Status** - <pending | active | paused | blocked | completed>
- **Question** - <이 Topic에서 답해야 할 질문>
- **Done When** - <현재 phase lifecycle을 포함한 종료 또는 전환 조건>

### T2. <Topic title> <!-- OPTIONAL -->

- **Status** - <pending | active | paused | blocked | completed>
- **Question** - <이 Topic에서 답해야 할 질문>
- **Done When** - <종료 또는 전환 조건>

## Current State

- **Phase** - <frame | evidence | dialectic | converge>
- **Working Hypothesis A** - <현재 가설 또는 unknown; evidence에 따라 변경 가능>
- **Working Hypothesis B** - <현재 가설 또는 unknown; evidence에 따라 변경 가능>
- **Material Uncertainty** - <현재 판단을 바꿀 수 있는 uncertainty>

### Evidence State <!-- Evidence 이후 필요할 때만 유지 -->

- **Supporting** - <핵심 supporting evidence>
- **Counterevidence** - <핵심 counterevidence>
- **Contested** - <해결되지 않은 evidence conflict>
- **Gap** - <추가 Research가 필요한 evidence gap>

### Dialectic State <!-- Dialectic 동안 필요할 때만 유지 -->

- **Thesis** - <현재 검증 중인 strongest proposition>
- **Antithesis** - <strongest incompatible counter-proposition 또는 constraint>
- **Conflict** - <정확한 contradiction 또는 competing assumption/criterion>
- **Synthesis Candidate** - <없으면 생략; challenge 전에는 provisional>

## References

- <canonical 문서, 코드, PR, Research/Review artifact 등>

## Turns

- `turns/<sequence>-<participant>.md`
- 예: `001-a.md`, `002-b.md`, `003-a.md`

## Synthesis <!-- Converge에서 작성. 커지면 synthesis.md로 분리한다. -->

### Outcome

<`synthesis` | `partial_agreement` | `bounded_disagreement` | `research_required` | `human_decision_required`>

### Result

<현재 evidence와 criteria가 허용하는 결론 또는 남은 선택지. Lead의 개인 입장을 shared truth로 쓰지 않는다.>

### Basis

- <핵심 decision criterion과 그것에 대한 strongest evidence/counterevidence>
- <thesis/antithesis에서 살아남거나 버려진 중요한 constraint와 이유>

### Agreement And Disagreement

- **Agreement** - <persisted turns에서 확인되는 합의>
- **Disagreement** - <남은 이견과 원인이 되는 fact, assumption, criterion, risk tolerance 또는 authority>

### Review Status

<non-lead가 synthesis omission/misrepresentation을 검토했는지와 남은 finding. 실제 review가 없으면 mutual agreement를 추정하지 않는다.>

### Next

- <권장 다음 행동, 추가 Research/Validation 또는 정확한 human decision point>
