---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: "Implement Structured Review Validation"
description: "Natural-language blocking policy를 제거하고 structured validation, legacy provenance와 read-only authority boundary를 함께 검증합니다."
tasks_completed: 0
tasks_total: 4
---

## Tasks

Implementation은 `reliability-agentic-review` capability contract와 PR #181의 ownership boundary 위에서 수행한다. 이 Change를 predecessor contract보다 먼저 sync 또는 archive하지 않는다.

- [ ] Version the review validation contract and preserve historical evidence
  - **Covers:** `Versioned validation provenance compatibility`
  - **Test first:** Current policy에서 legacy violation을 거부하고, 기존 `forbidden-action-policy-v1` accepted/rejected JSON evidence는 exact policy와 violation을 보존해 load하는 contract test를 추가한다.
  - **Done when:** 새 `AgenticReviewValidation`은 `structured-fact-validation-v1`과 세 structured violation만 active result로 허용하고, existing create-only evidence reader는 legacy policy와 natural-language violation을 historical provenance로 읽는다.

- [ ] Restrict active deterministic validation to structured facts
  - **Covers:** `Deterministic review validation`, `Free-text variation does not change structured result`
  - **Test first:** `review_summary`, finding description과 uncertainty에 action, approval, negation, quotation 또는 prompt-injection-like wording을 넣어도 같은 structured input이면 accepted가 되는 matrix와 세 violation의 exact ordering test를 고정한다.
  - **Done when:** Validator는 Evidence references, incident identity, target column과 deterministic facts만 비교하고 natural-language pattern, segmentation과 text aggregation subsystem은 다른 위치에 재생성되지 않은 채 제거된다.

- [ ] Preserve typed read-only service and current-policy provenance
  - **Covers:** `Advisory and read-only boundary`, `New evidence uses only the current policy`
  - **Test first:** Action-like free text가 포함된 accepted provider output이 current validation policy와 create-only evidence를 남기되 Reliability objects, approval/recovery state와 target data를 변경하지 않는 service test를 추가한다.
  - **Done when:** `review_null_spike()`의 status/failure/provenance contract는 유지되고 새 invocation은 legacy policy나 violation을 기록하지 않으며 `Approval`, `RecoveryProposal` 또는 recovery executor와 연결되지 않는다.

- [ ] Align Review AI documentation and verification closure
  - **Covers:** `Deterministic and adversarial evaluation`
  - **Done when:** Review AI domain documentation과 affected fixtures가 structured-fact policy와 historical compatibility를 표현하고, obsolete active-policy references는 제거되며 `uv run pytest tests/review_ai`, `uv run pytest tests/reliability tests/review_ai tests/runtime_ai`, `uv run ruff check .`, `uv run ty check`와 strict OpenSpec validation 결과가 기록된다.
