# PR #245 Review Evidence Map

## Purpose

이 문서는 bundle root [`README.md`](README.md)의 finding을 source contract, implementation, tests와 current GitHub evidence에 연결하는 navigation aid다. 별도 verdict나 requirement를 소유하지 않으며 README의 review 결과를 대체하지 않는다.

## Reviewed State

- Base: `e2e012d845c797ca9d3df93763bb5b7874083478`
- Reviewed implementation head: `28ddc7d2600518238cbc23ea21b0594086bde5e1`
- Prospective merge validated by CI Lite #1052: `ea6912888f687a5e3789fb2595540a35df2dc66e`
- PR state at review: Open, Draft, mergeable

## Finding Evidence

| Finding | Contract / Policy | Implementation | Existing Validation | Gap Established |
| --- | --- | --- | --- | --- |
| F1 | Public service docstring promises typed failure states | [`context.py`](../../../src/hmda_reliability/review_ai/context.py), [`prompt.py`](../../../src/hmda_reliability/review_ai/prompt.py), [`service.py`](../../../src/hmda_reliability/review_ai/service.py) | [`test_context.py`](../../../tests/review_ai/test_context.py), [`test_service.py`](../../../tests/review_ai/test_service.py) | Context-size `ValueError` has no service mapping and overflow service test is absent |
| F2 | [`reliability-agentic-review/spec.md`](../../../openspec/changes/review-ai-utility-evaluation/specs/reliability-agentic-review/spec.md) requires positive PASS + restatement FAIL + hedging FAIL in durable quality basis | [`evaluation.py`](../../../src/hmda_reliability/review_ai/evaluation.py), [`run_review_ai_utility_proof.py`](../../../scripts/run_review_ai_utility_proof.py) | [`test_utility_evaluation.py`](../../../tests/review_ai/test_utility_evaluation.py), [`test_review_ai_utility_proof.py`](../../../tests/scripts/test_review_ai_utility_proof.py) | Validator only distinguishes positive/negative kind; representative durable basis does not require both negative semantic roles |
| F3 | Bounded-context and fabricated-evidence contracts require a coherent citable evidence boundary | [`contracts.py`](../../../src/hmda_reliability/review_ai/contracts.py), [`context.py`](../../../src/hmda_reliability/review_ai/context.py), [`prompt.py`](../../../src/hmda_reliability/review_ai/prompt.py), [`validator.py`](../../../src/hmda_reliability/review_ai/validator.py), [`service.py`](../../../src/hmda_reliability/review_ai/service.py) | [`test_prompt_provider.py`](../../../tests/review_ai/test_prompt_provider.py), [`test_validator.py`](../../../tests/review_ai/test_validator.py) | Full draft refs can remain prompt-visible while validator allows only selected Evidence IDs |
| F4 | [`pull-request.md`](../../../docs/development/vcs-git/pull-request.md) requires current description and validation evidence for Review Readiness | [PR #245](https://github.com/mols3131d/hmda-data-reliability/pull/245) | [CI Lite #1052](https://github.com/mols3131d/hmda-data-reliability/actions/runs/35767830646) | PR body revision metadata predates current base/head and prospective-merge validation |

## Scope Evidence

- [`openspec/changes/review-ai-utility-evaluation/proposal.md`](../../../openspec/changes/review-ai-utility-evaluation/proposal.md) limits #245 to bounded context, utility evaluation/comparison, deterministic tests and controlled representative proof; live provider operation automation is outside this change.
- [`docs/mvp.md`](../../../docs/mvp.md) separately requires a Live Agentic proof for overall MVP acceptance.
- [`scripts/run_review_ai_utility_proof.py`](../../../scripts/run_review_ai_utility_proof.py) explicitly describes itself as offline contract/fixture validation and states that it does not replace formal live human evaluation evidence.

이 boundary 때문에 Live Agentic proof는 README의 PR-level finding에서 제외하고 global MVP follow-up으로만 유지한다.

## Validation Evidence

- CI Lite run: [#1052](https://github.com/mols3131d/hmda-data-reliability/actions/runs/35767830646)
- Prospective merge revision: `ea6912888f687a5e3789fb2595540a35df2dc66e`
- OpenSpec: `review-ai-utility-evaluation` valid
- Dependency boundary tests: `11 passed`
- Selected Review AI and utility proof tests: `314 passed`
- Live provider invocation: not verified by this review
