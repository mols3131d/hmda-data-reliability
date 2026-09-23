# 13 — Canonicalize OpenSpec before Langfuse

## Goal

PR #245에서 구현·검증된 durable spec-level behavior가 current canonical `openspec/specs/**`에 반영되고 active Change lifecycle이 정리된 뒤에만 Langfuse follow-up을 시작한다.

이 파일은 #245를 다시 수정하는 작업이 아니라 **post-merge transition gate의 handoff seed**다.

## Preconditions

- PR #245가 실제로 `main`에 merge되었다.
- resulting main revision을 확인했다.
- #245의 active Change가 어떤 canonical Spec을 변경하는지 current OpenSpec state로 다시 확인했다.

## Work

Repository의 current OpenSpec workflow를 따른다. archive/sync의 exact command나 PR unit은 현재 tool/schema guidance에서 다시 확인하며 이 문서가 별도 workflow를 발명하지 않는다.

최소한 다음 state를 달성해야 한다.

1. `review-ai-utility-evaluation`의 구현·검증된 delta가 영향을 받는 canonical `openspec/specs/**`에 반영된다.
1. active Change가 완료된 work artifact로 적절히 archive/정리된다.
1. canonical spec validation이 통과한다.
1. active change 목록과 repository source/tests가 서로 모순되지 않는다.

## Ownership Handoff

Repository workflow가 canonicalization/archive를 별도 branch 또는 PR로 수행하게 하면 active planning, validation과 durable Inbox context는 그 새 work unit이 소유한다. 이 #245 Inbox 파일을 post-merge 작업의 mutable status owner로 사용하지 않는다.

별도 PR이 필요하면 **그 PR이 Langfuse PR보다 먼저**다. #245 branch history를 rewrite하거나 merged PR을 다시 열어 canonicalization을 억지로 포함하지 않는다.

## Validation

- `openspec list` 또는 current equivalent로 active Change 상태를 확인한다.
- current canonical spec validation을 실행한다.
- affected canonical Requirement가 #245의 durable behavior와 일치하는지 확인한다.
- source/tests와 canonical spec 사이에 알려진 semantic drift가 없는지 확인한다.

## Done When

#245가 도입한 durable contract가 canonical OpenSpec에 반영되고 active Change lifecycle이 정리되어, 다음 PR이 `changes/**`의 non-canonical delta가 아니라 current canonical state를 기준으로 시작할 수 있으면 완료한다. 그 후에만 14를 사용한다.
