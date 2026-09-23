# 13 — Canonicalize OpenSpec before Langfuse

## Goal

PR #245에서 구현·검증된 durable spec-level behavior가 current canonical `openspec/specs/**`에 반영되고 active Change lifecycle이 정리된 뒤에만 Langfuse 후속 작업을 시작한다.

## Preconditions

- PR #245가 실제로 `main`에 merge되었다.
- resulting main revision을 확인했다.
- #245의 active Change가 어떤 canonical Spec을 변경하는지 current OpenSpec state로 다시 확인했다.

## Work

Repository의 현재 OpenSpec workflow를 따른다. archive/sync의 정확한 명령이나 PR 단위는 현재 tool/schema guidance에서 다시 확인하며 이 문서가 별도 workflow를 발명하지 않는다.

최소한 다음 상태를 달성해야 한다.

1. `review-ai-utility-evaluation`의 구현·검증된 delta가 영향을 받는 canonical `openspec/specs/**`에 반영된다.
1. active Change가 완료된 work artifact로 적절히 archive/정리된다.
1. canonical spec validation이 통과한다.
1. active change 목록과 repository source/tests가 서로 모순되지 않는다.

## PR Boundary

Repository workflow가 canonicalization/archive를 별도 PR로 요구하거나 main에서 수행하도록 되어 있으면 그 경계를 따른다. 별도 PR이 필요하면 **그 PR이 Langfuse PR보다 먼저**다.

#245 branch history를 rewrite하거나 #245를 다시 열어 post-merge canonicalization을 억지로 포함하지 않는다.

## Validation

- `openspec list` 또는 current equivalent로 active Change 상태를 확인한다.
- current canonical spec validation을 실행한다.
- affected canonical Requirement가 #245의 durable behavior와 일치하는지 확인한다.
- source/tests와 canonical spec 사이에 알려진 semantic drift가 없는지 확인한다.

## Done When

#245가 도입한 durable contract가 canonical OpenSpec에 반영되고 active Change lifecycle이 정리되어, 다음 PR이 `changes/**`의 non-canonical delta가 아니라 current canonical state를 기준으로 시작할 수 있으면 완료한다. 그 후에만 14로 이동한다.
