---
type: review
title: "PR #245 Review AI Utility Evaluation Improvement Review"
description: "PR #245 기존 리뷰의 F1-F5를 개선 루프로 보완한 현재 작업 트리의 검증 결과입니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
---

> [!IMPORTANT]
> **Blocked** — 현재 작업 트리에서 F1-F5의 로컬 보정과 회귀 검증은 확인했지만, 새 독립 dual-perspective review-lead가 완료되지 않아 formal review gate를 통과했다고 판정할 수 없습니다.

## Review Target

- Base: `1cff7550f0be2e09ee7c5937f6f4c2eea2aeb1d3`
- Original reviewed head: `17d6dbe21daef38f78cd8ab6631c1e56b5b4672a`
- Current target: the uncommitted working tree after the improvement loop
- Review source: [`00-review-review-ai-utility-evaluation.md`](00-review-review-ai-utility-evaluation.md)
- Plan source: [`01-plan-review-ai-utility-evaluation-improvement.md`](01-plan-review-ai-utility-evaluation-improvement.md)

## Scope

- Review AI provider canonical input and invocation provenance
- Utility proof controls, output/comparison evidence, and project-revision provenance
- Utility proof-store path safety and fsync rollback behavior

Out of scope: live provider execution, PR/GitHub mutation, commit/push/merge, and unrelated Airflow timeout remediation.

## Findings Summary

| Finding | Original severity | Current disposition | Evidence |
| --- | --- | --- | --- |
| F1 raw/unbounded provider evidence | Major | Resolved locally | bounded selected-evidence projection is shared by provider input, validator allow-list, and invocation provenance |
| F2 score/control evidence not bound to actual output | Major | Resolved locally | evaluation/control/comparison models retain actual output and recompute digest, contribution kinds, and deterministic oracle |
| F3 unsafe proof ID/path handling | Major | Resolved locally | `load_proof()` and `write_proof()` share the safe ID/root-bound path helper |
| F4 fsync failure leaves final evidence | Minor | Resolved locally | linked final artifact is rolled back; rollback failure is surfaced as indeterminate |
| F5 case revision differs from input revision | Minor | Resolved locally | runner and proof models use one canonical non-empty revision; automatic HEAD attribution requires a clean tracked worktree |
| G1 fresh independent formal review unavailable | Major | **Blocked** | required independent review-lead did not complete after remediation |

## Remediation Review

### F1 — bounded provider and invocation provenance

`build_canonical_input()` now projects only the bounded context's selected evidence facts and provenance. Raw `Evidence.payload` is not copied into the provider-facing canonical input. The same selected evidence IDs are used for provider citation validation and the persisted invocation record, so a provider cannot cite omitted original evidence.

Relevant implementation: `src/hmda_reliability/review_ai/prompt.py`, `service.py`, and `validator.py`.

### F2 — actual-output utility evidence

`HumanUtilityEvaluation`, `UtilityComparisonEvidence`, and `UtilityControl` now retain the actual `AgenticReviewOutput`. Model validation recomputes the output digest and contribution kinds instead of trusting caller-supplied strings. Controls also compare the actual output to the deterministic expected incident, target column, and facts oracle. An incomplete five-criterion control, a digest mismatch, a wrong deterministic oracle, and a negative control with non-restatement output are rejected.

Relevant implementation: `src/hmda_reliability/review_ai/evaluation.py` and `scripts/run_review_ai_utility_proof.py`.

### F3/F4 — create-only proof-store boundary

Proof IDs are validated before path construction and both read/write paths remain root-bound. The write path removes a linked final artifact when a later directory fsync fails; if cleanup itself fails, the operation reports that rollback is indeterminate rather than hiding the condition.

Relevant implementation: `src/hmda_reliability/review_ai/evaluation_store.py`.

### F5 — one revision across the proof

The runner canonicalizes a single non-empty `project_revision` and passes it through input, controls, evaluations, comparison, quality basis, and proof case. `--project-revision auto` uses `HEAD` only when tracked files are clean; a dirty tracked worktree requires an explicit revision. The offline proof reload confirmed equality across the stored bundle.

Relevant implementation: `scripts/run_review_ai_utility_proof.py` and `src/hmda_reliability/review_ai/evaluation.py`.

## Validation Evidence

| Result | Check | Evidence |
| --- | --- | --- |
| Pass | Focused tests | `tests/review_ai tests/scripts/test_review_ai_utility_proof.py`: `109 passed` |
| Pass | Offline proof | Explicit revision generated `compared` and `accept`; reload assertions confirmed case/comparison/quality-basis revision equality and actual-output binding |
| Pass | Type/lint/format | `ty check`, Ruff check, Ruff format check, and `git diff --check` passed |
| Pass | OpenSpec | Local `openspec validate review-ai-utility-evaluation --strict` passed |
| Pass | Documentation maintenance | `rumdl check docs/development/testing.md` passed |
| Not Verified | Exact final full suite | A broader pre-Loop-2 run had `650 passed, 1 skipped, 5 failed`; all five failures were unrelated Airflow subprocess timeouts. The full suite was not rerun after the Loop-2 code changes. |
| Not Verified | Live provider | Deliberately out of scope for this offline proof |
| Not Verified | Fresh formal independent review | Review-lead did not complete the required specialist review after remediation |

## Review Decision

The current implementation has local evidence addressing all original F1-F5 findings, including the F2/F5 findings raised by the first improvement review. This is not an approval or merge-ready decision because G1 remains open: the required independent dual-perspective review coverage was unavailable.

No commit, push, PR update, approval, or merge was performed.

## Loops State

- Phase: Finalize
- Readiness: n/a
- Loop: 2/30
- Acceptance: candidate, not accepted
- Material gap: fresh independent formal review evidence
- Next: BLOCKED until the independent review gate can complete
