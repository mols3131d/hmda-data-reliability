# 13 — Verify or Canonicalize OpenSpec before Langfuse

## Goal

PR #245 merge 뒤 current canonical `openspec/specs/**`와 active Change lifecycle을 확인하고, #245의 durable spec-level behavior가 아직 canonical state에 반영되지 않았다면 current OpenSpec workflow로 필요한 최소 canonicalization만 수행한다.

이 파일은 #245를 다시 수정하는 작업이 아니라 **post-merge transition gate의 handoff seed**다.

## Preconditions

- PR #245가 실제로 `main`에 merge되었다.
- resulting main revision을 확인했다.
- #245의 active Change가 어떤 canonical Spec을 변경하는지 current OpenSpec state로 다시 확인했다.

## Verify First

먼저 다음을 확인한다.

1. affected canonical `openspec/specs/**`가 #245의 durable behavior를 이미 반영하는가?
1. `review-ai-utility-evaluation` Change가 current workflow상 이미 archive/정리됐는가?
1. canonical spec validation과 source/tests가 서로 일치하는가?

세 조건이 이미 충족되면 추가 archive/sync 작업을 만들지 않고 이 gate를 완료한다.

## Canonicalize Only if Needed

Canonical state가 아직 뒤처져 있을 때만 repository의 current OpenSpec workflow를 따른다. archive/sync의 exact command나 PR unit은 current tool/schema guidance에서 다시 확인하며 이 문서가 별도 workflow를 발명하지 않는다.

필요한 경우 최소한 다음 state를 달성한다.

- 구현·검증된 delta가 affected canonical `openspec/specs/**`에 반영됨
- active Change가 completed work artifact로 적절히 archive/정리됨
- canonical spec validation 통과
- active change 목록과 repository source/tests 사이 known contradiction 없음

## Ownership Handoff

Repository workflow가 canonicalization/archive를 별도 branch 또는 PR로 수행하게 하면 active planning, validation과 durable Inbox context는 그 새 work unit이 소유한다. 이 #245 Inbox 파일을 post-merge 작업의 mutable status owner로 사용하지 않는다.

별도 PR이 필요하면 **그 PR이 Langfuse PR보다 먼저**다. #245 branch history를 rewrite하거나 merged PR을 다시 열어 canonicalization을 억지로 포함하지 않는다.

## Validation

- `openspec list` 또는 current equivalent로 active Change 상태를 확인한다.
- current canonical spec validation을 실행한다.
- affected canonical Requirement가 #245의 durable behavior와 일치하는지 확인한다.
- source/tests와 canonical spec 사이에 known semantic drift가 없는지 확인한다.

## Done When

추가 작업 없이 이미 canonical한 상태이거나, 필요한 최소 canonicalization을 완료해 다음 PR이 `changes/**`의 non-canonical delta가 아니라 current canonical state를 기준으로 시작할 수 있으면 완료한다. 그 후에만 14를 사용한다.
