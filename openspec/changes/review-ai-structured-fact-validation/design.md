---
type: openspec-spec-driven-tdd-design
category: design
title: "Structured Review Validation Boundary"
description: "Active validation을 structured facts에 한정하면서 immutable legacy provenance를 versioned contract로 계속 읽는 technical delta를 정의합니다."
---

## Technical Delta

### D1. Use the validation policy identity as a provenance discriminator

- **Decision:** `AgenticReviewValidation.policy_id`는 유지하되 active default를 `structured-fact-validation-v1`로 변경한다. 하나의 versioned validation contract가 current structured violations와 historical `forbidden-action-policy-v1` violations를 policy별 invariant로 구분한다.
- **Rationale:** Main에 이미 create-only invocation evidence writer와 typed loader가 있고 기존 record는 `forbidden-action-policy-v1`, `authority_escalation`, `forbidden_action`을 저장할 수 있다. Policy field와 legacy enum value를 즉시 삭제하면 immutable historical record를 현재 loader로 읽을 수 없다.
- **Trade-off:** Legacy policy와 두 violation symbol은 provenance compatibility surface로 남지만 active validator는 생성할 수 없다. Policy별 allowed violation set을 contract validation으로 제한하고 active validator test로 current output을 고정한다.

### D2. Remove natural-language inspection from the validator boundary

- **Decision:** `validate_agentic_review()`는 Evidence reference, incident ID, target column과 deterministic facts 비교만 수행한다. `incident_type`은 `AgenticReviewOutput` schema가 `null_spike`로 제한한다. Free-text fields를 합치거나 segment/pattern으로 검사하는 helper와 policy data는 삭제하며 다른 module이나 configuration으로 옮기지 않는다.
- **Rationale:** Action 또는 approval text를 해석하는 책임을 이동하면 같은 semantic judge가 다른 위치에 남는다. 실제 execution safety는 Review AI와 dependency 방향이 분리된 typed approval/recovery boundary가 소유한다.

### Boundary Changes

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| Active `AgenticReviewValidation` | `structured-fact-validation-v1`, 세 structured violation, stable order와 uniqueness | free-text command/authority 의미 |
| Legacy validation provenance | 기존 policy identity와 violation의 typed deserialization | current acceptance 또는 authority 판단 |
| `review_null_spike()` | structured validation, typed result와 create-only invocation evidence | `Approval`, `RecoveryProposal`, recovery executor invocation |

### Migration Strategy

- 이 delta Spec은 completed active Change `reliability-agentic-review`의 capability contract를 전제로 한다. 해당 contract가 canonical Spec에 반영되기 전에 이 Change를 먼저 sync 또는 archive하지 않는다.
- Invocation evidence grain과 create-only storage path는 변경하지 않는다. 기존 JSON record를 rewrite하거나 in-place migration하지 않는다.
- Versioned validation contract는 current policy에서 legacy violation을 거부하고 legacy policy에서 historical violation을 보존한다. 새 service invocation은 current policy만 기록한다.
- Validator phrase corpus는 structured contract, wording-invariance와 side-effect oracle로 교체한다. Natural-language regex를 evaluation helper나 test-only classifier로 재생성하지 않는다.
- Implementation은 PR #181의 `review_ai -> reliability/runtime_ai`, `runtime_ai -> no review_ai/reliability`, `reliability -> no AI package` dependency boundary를 그대로 사용한다.
