# 05 — Reconcile OpenSpec after Apply

## Goal

Stage 1 remediation 이후 active `review-ai-utility-evaluation` OpenSpec change의 requirement, design, tasks와 현재 구현·tests가 같은 상태를 설명하게 한다.

## Scope

00에서 정리한 planning owner와 Stage 1 implementation 결과를 기준으로 post-Apply consistency만 확인한다.

- reopened task가 실제로 완료됐는지 확인한다.
- Stage 1에서 planning interpretation이 추가로 바뀌었다면 원인을 소유하는 artifact부터 최소 수정한다.
- Proposal/spec/design/tasks에 current implementation보다 앞서거나 뒤처진 완료 주장을 남기지 않는다.
- offline utility proof와 global Live Agentic proof의 경계를 유지한다.

이 단계에서 새 기능, Langfuse integration 또는 generic evaluator redesign을 추가하지 않는다.

## Review Questions

- F1 typed failure boundary가 current requirement/design과 일치하는가?
- F2의 required control semantics가 spec, task, implementation과 durable proof에 같은 의미로 표현되는가?
- F3 bounded evidence boundary가 prompt와 validator에서 동일한가?
- reopened task가 실제 proof를 근거로 다시 완료됐는가?
- active Change의 완료 주장이 current tests/evidence와 일치하는가?

## Validation

- OpenSpec validation을 실행한다.
- relevant spec scenario와 focused test/proof를 대응시킨다.
- 구현 세부를 normative spec에 불필요하게 고정하지 않는다.
- 00에서 reopen한 task가 근거 없이 다시 완료되지 않았는지 확인한다.

## Done When

OpenSpec planning, current code/tests와 durable proof 사이에 알려진 semantic drift가 없고 active Change의 task state가 실제 implementation 상태와 맞으면 완료한다. 그 후에만 scope cleanup으로 이동한다.
