---
type: review
title: "PR #245 High-Confidence Review"
description: "현재 implementation revision과 normative contract를 기준으로 PR #245의 Review AI utility proof를 재검증한 리뷰"
tags:
  - "domain:review-ai"
  - utility-evaluation
  - pull-request-review
---

# PR #245 High-Confidence Review

> [!WARNING]
> **Result: `CHANGES_REQUIRED`** — reviewed implementation revision에는 acceptance 전에 수정해야 하는 Major finding 2개가 남아 있다. CI가 통과하더라도 bounded context failure contract와 durable quality-basis contract가 현재 OpenSpec 요구를 모두 충족하지 않는다.

- **Target:** [PR #245 · `feat(review-ai): prove MVP utility evaluation`](https://github.com/mols3131d/hmda-data-reliability/pull/245)
- **Revision:** base `e2e012d845c797ca9d3df93763bb5b7874083478`, reviewed implementation head `28ddc7d2600518238cbc23ea21b0594086bde5e1`, prospective merge `ea6912888f687a5e3789fb2595540a35df2dc66e`
- **Scope:** bounded review context, structured utility contribution, human rubric/control discrimination, baseline/candidate comparison evidence, service failure boundary와 current PR readiness evidence

이 review bundle을 추가하는 commit은 reviewed implementation head 이후의 문서-only 변경이다. 아래 correctness finding은 `28ddc7d...`의 구현을 대상으로 하며, bundle 추가 자체가 해당 code path를 변경하지 않는다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 **Major** | Bounded context overflow가 typed `AgenticReviewResult` boundary를 벗어날 수 있다. | Context-size 전용 exception을 typed input rejection으로 변환하고 service-level regression test를 추가한다. |
| F2 | 🟠 **Major** | Durable quality basis가 required restatement + hedging negative controls를 모두 증명하지 않아도 valid가 될 수 있다. | Negative control semantic role을 명시하고 representative proof에 세 required role을 모두 저장·검증한다. |
| F3 | 🟡 **Minor** | Provider-visible Evidence ID와 validator allowlist가 bounded selection 이후 불일치할 수 있다. | Prompt에 노출되는 citable Evidence ID와 validator allowlist를 같은 selected set으로 정렬한다. |
| F4 | 🟡 **Minor** | PR description의 revision/validation metadata가 현재 base/head와 맞지 않는다. | Correctness fix와 current CI 이후 description을 최신 state로 다시 작성한다. |

## Details

### F1 — Context Overflow Escapes the Typed Result Boundary

#### Locations

- [`src/hmda_reliability/review_ai/context.py`](../../../src/hmda_reliability/review_ai/context.py)
  - `build_bounded_review_context`
- [`src/hmda_reliability/review_ai/prompt.py`](../../../src/hmda_reliability/review_ai/prompt.py)
  - `render_review_prompt`
- [`src/hmda_reliability/review_ai/service.py`](../../../src/hmda_reliability/review_ai/service.py)
  - `review_null_spike`
- [`tests/review_ai/test_context.py`](../../../tests/review_ai/test_context.py)
- [`tests/review_ai/test_service.py`](../../../tests/review_ai/test_service.py)

#### Evidence

`build_bounded_review_context()`는 최종 serialized context가 `max_context_bytes`를 초과하면 일반 `ValueError("bounded review context exceeds max_context_bytes")`를 발생시킨다. `render_review_prompt()`는 service preflight 중 이 builder를 먼저 호출하지만, `review_null_spike()`는 prompt preflight에서 `PromptTooLargeError`만 잡아 `INPUT_REJECTED / prompt_too_large`로 변환한다. 따라서 context-size overflow를 typed result로 변환하는 경로가 없다.

이 경로는 구성상 도달 가능하다. Context는 기본적으로 최대 8개 Evidence를 선택하며 각 item은 bounded summary와 facts를 보존하므로, 각 item이 개별 bound를 만족하면서 합산 context가 기본 16 KiB를 넘을 수 있다. 현재 context test는 bound 안에 들어가는 정상 경계를 검증하지만 service boundary에서 context overflow가 typed failure로 닫히는지는 검증하지 않는다.

#### Impact

Public service의 다른 예상 failure는 `AgenticReviewResult.status`로 정규화되지만 이 경로는 Python exception으로 종료될 수 있다. 상위 orchestration이 동일한 typed failure contract로 입력 실패를 처리할 수 없고, provider 호출 전의 bounded-input rejection이 process-level defect처럼 보일 수 있다.

#### Action

Context-size overflow를 나타내는 전용 exception을 두고 service가 그 exception만 좁게 catch해 `INPUT_REJECTED`와 명확한 failure code로 변환한다. 일반 `ValueError`를 넓게 catch해 programming defect까지 입력 오류로 숨기지 않는다. Regression test는 oversized context를 가진 유효 input에서 provider/store가 호출되지 않고 typed rejection이 반환되는지 확인해야 한다.

### F2 — Durable Quality Basis Does Not Prove Both Required Negative Controls

#### Locations

- [`openspec/changes/review-ai-utility-evaluation/specs/reliability-agentic-review/spec.md`](../../../openspec/changes/review-ai-utility-evaluation/specs/reliability-agentic-review/spec.md)
  - `Requirement: Versioned human rubric and control discrimination`
- [`src/hmda_reliability/review_ai/evaluation.py`](../../../src/hmda_reliability/review_ai/evaluation.py)
  - `UtilityControl`
  - `validate_quality_basis`
- [`scripts/run_review_ai_utility_proof.py`](../../../scripts/run_review_ai_utility_proof.py)
  - `build_representative_utility_proof`
- [`tests/review_ai/test_utility_evaluation.py`](../../../tests/review_ai/test_utility_evaluation.py)
  - `test_hedging_negative_control_discrimination`

#### Evidence

OpenSpec은 quality basis가 compliant positive control을 `PASS`, deterministic facts 또는 draft를 재진술하는 negative control을 `FAIL`, 구체적 조사 행동 없이 책임을 회피하는 hedging negative control을 `FAIL`로 판별해야 한다고 `SHALL`로 규정한다. Control scenario는 이 판별 결과가 durable quality-basis evidence에 남아야 함을 요구한다.

현재 `validate_quality_basis()`는 control의 `output_kind` 집합이 `positive_control`과 `negative_control`을 포함하는지만 확인한다. Negative control의 semantic role을 구분하지 않으므로 restatement 하나만 존재하거나 hedging 하나만 존재해도 basis가 valid가 될 수 있다. 실제 hedging regression test도 `positive + hedging` 조합으로 `basis.valid is True`를 확인하고, representative runner는 `control-positive`와 baseline 기반 `control-negative` 두 개만 durable proof basis에 넣는다.

#### Impact

Representative comparison이 참조하는 durable quality basis가 OpenSpec이 요구한 두 negative failure mode를 모두 증명하지 않아도 `COMPARED`와 human `ACCEPT`까지 생성될 수 있다. Hedging case를 독립 test에서 한 번 실패시켰다는 사실은 candidate comparison이 참조하는 durable basis가 해당 판별력을 보존한다는 증명과 다르다.

#### Action

Control에 semantic role을 명시적으로 표현하고 quality-basis validation에서 `positive`, `restatement_negative`, `hedging_negative` 세 required role의 존재, expected outcome, 동일 case/revision을 강제한다. Representative proof bundle을 store·reload한 뒤 세 역할이 각각 `PASS`, `FAIL`, `FAIL`이고 comparison이 그 완전한 basis digest를 참조하는 regression proof를 추가한다. `control_id` 문자열 parsing에 의미를 숨기지 않는다.

### F3 — Provider-Visible Evidence IDs and Validator Allowlist Can Diverge

#### Locations

- [`src/hmda_reliability/review_ai/contracts.py`](../../../src/hmda_reliability/review_ai/contracts.py)
  - `AgenticReviewInput`
- [`src/hmda_reliability/review_ai/context.py`](../../../src/hmda_reliability/review_ai/context.py)
  - `build_bounded_review_context`
- [`src/hmda_reliability/review_ai/prompt.py`](../../../src/hmda_reliability/review_ai/prompt.py)
  - `build_canonical_input`
- [`src/hmda_reliability/review_ai/service.py`](../../../src/hmda_reliability/review_ai/service.py)
  - `review_null_spike`
- [`src/hmda_reliability/review_ai/validator.py`](../../../src/hmda_reliability/review_ai/validator.py)
  - `validate_agentic_review`

#### Evidence

`AgenticReviewInput`은 incident, draft와 전체 provided Evidence ID가 같은 집합이 되도록 강제한다. Bounded context는 기본 최대 8개 Evidence만 선택하고 canonical prompt의 top-level `evidence`에는 selected items만 넣는다. 그러나 canonical `draft` projection은 원본 `draft.evidence_refs`를 그대로 포함한다. Service는 이후 validator의 `allowed_evidence_ids`를 selected bounded Evidence ID로만 제한한다.

따라서 8개를 넘는 유효 Evidence가 존재하면 omitted ID가 `draft.evidence_refs`를 통해 provider-visible 상태로 남을 수 있지만 validator allowlist에는 포함되지 않는다. Provider가 prompt에서 실제로 본 omitted ID를 인용하면 실제 fabricated identity가 아닌데도 `FABRICATED_EVIDENCE`가 발생할 수 있다.

#### Impact

Large-context review에서 false rejection이 가능하고 `fabricated_evidence` signal의 의미가 약해진다. 현재 representative fixture는 Evidence 수가 작아 이 mismatch를 통과하지 않는다.

#### Action

Bounded selected ID set을 provider-visible citable identity의 단일 authority로 만든다. 현재 설계에서는 canonical prompt에 투영하는 `draft.evidence_refs`도 selected set으로 제한하는 방식이 가장 작다. 원본 `RemediationDraft` 객체는 변경할 필요가 없다. Regression test는 `max_evidence`보다 많은 valid Evidence를 사용해 prompt 전체의 citable ID 집합과 validator allowlist가 동일함을 검증한다.

### F4 — PR Description Is Stale Against the Current Review Basis

#### Locations

- [PR #245 description](https://github.com/mols3131d/hmda-data-reliability/pull/245)
- [`docs/development/vcs-git/pull-request.md`](../../../docs/development/vcs-git/pull-request.md)
  - `Review Readiness`

#### Evidence

Review 시점의 실제 base/head는 `e2e012d845c797ca9d3df93763bb5b7874083478` / `28ddc7d2600518238cbc23ea21b0594086bde5e1`이고 prospective merge는 `ea6912888f687a5e3789fb2595540a35df2dc66e`다. PR body의 revision metadata는 더 오래된 base `2a793f4c23745abd485f26b15421b17c744760fa`와 head `1c9ea4fccfe8ff6f9a5c2332beb9f1b9c324a820`를 유지하고 있다. Validation section도 현재 prospective merge CI보다 과거의 focused result를 중심으로 설명한다.

Repository Review Readiness policy는 description claim과 validation evidence가 현재 state에 적용 가능해야 하고 base/head 등 material state가 달라지면 이전 assessment를 stale로 본다.

#### Impact

이 finding은 production correctness defect가 아니지만 current Review Readiness를 `not_ready`로 유지하는 evidence-quality 문제다. Reviewer가 현재 diff와 validation evidence를 PR body만으로 신뢰성 있게 연결하기 어렵다.

#### Action

F1–F3 수정과 current prospective-merge validation이 완료된 뒤 PR body를 최신 결과만 남기도록 갱신한다. Revision pair, validation counts와 remaining `Not Verified` 범위를 실제 current state에 맞춘 뒤 fresh readiness assessment를 수행한다.

## Scope Boundary

`docs/mvp.md`의 전체 MVP acceptance에는 같은 revision에서 실제 model invocation과 invocation evidence를 남기는 Live Agentic proof가 필요하다. 그러나 #245의 OpenSpec proposal은 live provider 운영 자동화를 이 change의 scope 밖으로 두고 offline utility infrastructure와 comparison contract에 집중한다.

따라서 Live Agentic proof 미완료는 **global MVP follow-up**이며 #245 implementation defect로 분류하지 않는다. #245가 수정·검토·병합되더라도 그 사실만으로 전체 MVP 완료를 선언할 수는 없다.

Strict JSON parser가 fenced model response를 처리하지 못할 가능성도 이번 finding에서 제외했다. Parser의 strict behavior는 확인되지만, 현재 #245 scope에서 target live model이 fenced JSON을 실제로 반환해 acceptance를 막는다는 관찰 evidence가 없다. Live proof에서 재현된 경우 별도 defect로 승격한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | CI Lite #1052 | Reviewed implementation의 prospective merge `ea6912888f687a5e3789fb2595540a35df2dc66e`에서 workflow 성공 |
| ✅ Pass | OpenSpec validation | `review-ai-utility-evaluation` change valid |
| ✅ Pass | Dependency boundary | Tach validation과 관련 dependency tests `11 passed` |
| ✅ Pass | Python validation | Ruff check/format과 `ty` 성공 |
| ✅ Pass | Selected tests | `tests/review_ai`와 utility proof script 범위 `314 passed` |
| ⚪ Not Verified | Live provider invocation | 이 review의 #245 implementation correctness scope에서는 실행하지 않음; global MVP proof로 별도 수행 필요 |

CI pass는 F1–F3이 없다는 증명이 아니다. 현재 suite가 해당 negative path 또는 durable three-role basis invariant를 직접 강제하지 않기 때문에 semantic contract gap과 automation result가 동시에 성립할 수 있다.

## Recommended Remediation Order

1. F1의 context overflow를 typed input rejection으로 닫고 service-level regression test를 추가한다.
1. F2의 control semantic role과 durable three-role quality basis를 구현하고 proof store/reload까지 검증한다.
1. F3의 provider-visible Evidence ID와 validator allowlist를 동일한 bounded selected set으로 맞춘다.
1. Current base/head 또는 prospective merge에서 OpenSpec, Python checks, Review AI tests와 proof runner를 다시 실행한다.
1. F4의 PR description을 current revision/validation evidence로 갱신한다.
1. 수정된 exact base/head에서 fresh review와 Review Readiness assessment를 수행한다.

## Risks and Limits

이 artifact는 reviewed implementation revision에 대한 evidence-backed technical review이며 independent approval을 대체하지 않는다. Live LLM/provider invocation을 이 review에서 수행하지 않았으므로 실제 model behavior, fenced response 빈도, live latency/usage와 실제 human utility를 관찰했다고 주장하지 않는다.

Finding별 source navigation과 evidence relation은 [`evidence-map.md`](evidence-map.md)에 정리했다.
