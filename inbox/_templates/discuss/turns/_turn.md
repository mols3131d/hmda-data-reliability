---
type: discuss
discussion: <discussion-id>
topic: <topic-id>
phase: <frame | evidence | dialectic | converge>
sequence: <global-sequence>
participant: <A | B>
status: completed
# OPTIONAL: dialectic phase에서 cycle을 구분할 가치가 있을 때만 유지한다.
cycle: <positive-integer>
# OPTIONAL: phase move를 추적할 가치가 있을 때만 유지한다.
move: <frame-proposal | frame-review | evidence | thesis | antithesis | synthesis | challenge | converge | research-block>
---

<!--
- 파일명: <sequence>-<participant>.md
- 예: 001-a.md, 002-b.md, 003-a.md
- sequence는 토론 전체의 persisted 시간 순서다.
- phase와 optional cycle/move는 filename이 아니라 frontmatter가 소유한다.
- 이미 상대가 소비한 turn은 수정하지 않는다. 정정은 다음 eligible turn에 기록한다.
- participant identity는 찬성/반대 진영을 의미하지 않는다.
- dialectic에서 상대 claim을 공격하기 전에 가능한 한 strongest version으로 steelman한다.
- synthesis candidate는 상대 challenge 전에는 provisional이다.
- convergence/no-finding은 가능하지만 반복 ping-pong하지 않는다.
- private chain-of-thought가 아니라 검토 가능한 claim, evidence, change와 next state만 남긴다.
-->

## Position

<현재 working hypothesis, phase contribution 또는 판단. Evidence에 따라 변경 가능하다.>

## Steelman <!-- OPTIONAL: 상대의 claim을 challenge하는 turn에서 사용 -->

<상대가 실제로 주장한 내용의 가장 강한 형태. Misunderstanding이 있으면 먼저 정정한다.>

## Evidence

- <판단을 바꿀 수 있는 핵심 evidence 또는 counterevidence>
- <필요하면 fact / inference / assumption / uncertainty를 구분한다.>

## Response <!-- OPTIONAL -->

<상대의 strongest claim, framing, evidence 또는 synthesis candidate에 대한 동의·반론·보강>

## Tension <!-- OPTIONAL: Dialectic에서 실제 contradiction을 분리할 때 사용 -->

<충돌하는 fact, assumption, criterion, constraint, risk tolerance 또는 uncertainty>

## Change <!-- OPTIONAL -->

<양보, 수정된 가정, 버린 claim 또는 이전 position에서 달라진 점과 이유>

## Proposal <!-- OPTIONAL -->

<현재 phase에서 필요한 다음 proposition, synthesis candidate 또는 convergence result. 단순 중간 타협으로 작성하지 않는다.>

## Next

<현재 phase를 계속할지, frame/evidence/dialectic으로 돌아갈지, converge/research/human decision이 필요한지와 짧은 이유>
