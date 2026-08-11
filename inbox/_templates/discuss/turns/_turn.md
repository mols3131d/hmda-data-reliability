---
type: discuss
discussion: <discussion-id>
topic: <topic-id>
sequence: <global-sequence>
participant: <A | B>
participant_sequence: <participant-sequence>
status: completed
---

<!--
- 파일명: <sequence>-<participant>-<participant-sequence>.md
- 예: 001-a-001.md, 002-b-001.md, 003-a-002.md
- sequence는 토론 전체의 시간 순서, participant_sequence는 해당 participant의 발언 순서다.
- sequence 값은 정렬이 안정되도록 0-padding한다.
- 이미 상대가 소비한 turn은 수정하지 않는다. 정정은 다음 turn에 기록한다.
- 첫 turn에는 Response/Change가 필요 없으면 제거한다.
- private chain-of-thought가 아니라 검토 가능한 결론과 근거만 남긴다.
-->

## Position

<현재 입장 또는 판단>

## Evidence

- <판단을 바꿀 수 있는 핵심 근거>

## Response <!-- OPTIONAL -->

<상대의 가장 강한 주장에 대한 동의, 반론 또는 보강>

## Change <!-- OPTIONAL -->

<양보, 수정된 가정 또는 이전 입장에서 달라진 점>

## Proposal

<현재 사람이 선택할 수 있도록 제안하는 방향>

## Next

<continue | research | change-topic | synthesize 중 하나와 짧은 이유>
