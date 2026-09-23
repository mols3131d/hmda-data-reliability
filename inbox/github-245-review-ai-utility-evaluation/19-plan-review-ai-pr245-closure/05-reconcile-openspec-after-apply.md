# 05 — Reconcile OpenSpec after Apply

## Goal

Stage 1 remediation 이후 active `review-ai-utility-evaluation` OpenSpec change의 requirement, design, tasks와 현재 구현·tests가 같은 상태를 설명하게 한다.

## Scope

00에서 정리한 planning owner와 Stage 1 implementation 결과를 기준으로 post-Apply consistency만 확인한다.

- reopened task가 실제로 완료됐는지 확인한다.
- task checkbox와 `tasks_completed`/`tasks_total` 같은 schema-owned progress metadata가 같은 상태를 표현하는지 확인한다.
- Stage 1에서 planning interpretation이 추가로 바뀌었다면 원인을 소유하는 artifact부터 최소 수정한다.
- Proposal/spec/design/tasks에 current implementation보다 앞서거나 뒤처진 완료 주장을 남기지 않는다.
- offline utility proof와 global Live Agentic proof의 경계를 유지한다.

이 단계는 **현재 contract reconciliation**만 소유한다. Langfuse integration, future human-eval transport 또는 generic evaluator redesign을 계획하지 않는다.

## Review Questions

- F1 typed failure boundary가 current requirement/design과 일치하는가?
- F2의 required control semantics가 spec, task, implementation과 durable proof에 같은 의미로 표현되는가?
- F3 bounded evidence boundary가 prompt와 validator에서 동일한가?
- reopened task가 실제 proof를 근거로 다시 완료됐는가?
- task checklist와 progress metadata가 같은 completion state인가?
- active Change의 완료 주장이 current tests/evidence와 일치하는가?
- offline fixture proof를 live human evaluation으로 과장하는 claim이 남아 있지 않은가?
- Langfuse를 예상한다는 이유만으로 current requirement에 없는 abstraction이나 persistence surface가 추가되지 않았는가?

## Evaluation Boundary

다음 항목은 00에서 current contract defect로 확인되지 않은 한 이 단계에서 수정하지 않는다.

- `output_fixture_id` optionalization 또는 evaluation source hierarchy
- rubric anchor schema 일반화
- standalone human evaluation store
- human-score CLI/UI
- external evaluator backend protocol
- trace/score vendor identity fields

이들이 실제 Langfuse adapter에서 필요해지면 14의 research 결과가 새 work unit에서 판단한다.

## Validation

- OpenSpec validation을 실행한다.
- relevant spec scenario와 focused test/proof를 대응시킨다.
- 구현 세부를 normative spec에 불필요하게 고정하지 않는다.
- 00에서 reopen한 task가 근거 없이 다시 완료되지 않았는지 확인한다.
- #245 completion claim이 future Langfuse capability를 포함하지 않는지 확인한다.

## Done When

OpenSpec planning, task progress metadata, current code/tests와 durable proof 사이에 알려진 semantic drift가 없고 active Change의 completion state가 actual implementation 상태와 맞으며 speculative Langfuse preparation이 섞이지 않았으면 완료한다. 그 후에만 scope cleanup으로 이동한다.
