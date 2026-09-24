---
type: plan
title: "PR #245 Review AI Utility Evaluation Improvement Plan"
description: "기존 PR #245 review의 F1-F5를 active OpenSpec contract 안에서 보완하는 개선 계획입니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
---

## Loops State

- Phase: Finalize
- Readiness: n/a
- Loop: 2/30
- Acceptance: candidate, not accepted
- Material gap: fresh independent formal review evidence
- Next: BLOCKED

## Goal

PR #245의 Review AI utility proof가 bounded context, 실제 output provenance, create-only artifact 경계와 revision provenance를 결정론적으로 보존하도록 개선한다.

## Active Scope

### In scope

- `src/hmda_reliability/review_ai/prompt.py`와 service/validator의 bounded evidence projection
- `src/hmda_reliability/review_ai/evaluation.py`의 control/comparison binding
- `src/hmda_reliability/review_ai/evaluation_store.py`의 proof ID와 fsync failure handling
- `scripts/run_review_ai_utility_proof.py`의 representative fixture provenance
- 직접 관련된 Review AI 및 utility proof tests
- 이 개선 루프의 Research/Review evidence를 이 Inbox bundle에 기록

### Out of scope

- live provider 호출 또는 automatic LLM judge
- recovery, approval, incident detection과 `runtime_ai` contract 변경
- PR/GitHub 상태 변경, commit, push, merge
- unrelated full-suite Airflow timeout remediation

## Acceptance Conditions

- Provider canonical input과 새 invocation provenance에는 raw/unbounded `Evidence.payload`가 없고 bounded projection만 남는다.
- Positive/negative control과 baseline/candidate evidence는 실제 output digest/fixture identity와 contribution kind를 검증하며 불완전한 다섯 criterion control은 quality basis를 통과하지 못한다.
- `load_proof()`와 `write_proof()`는 동일한 safe ID/root-bound helper를 사용한다.
- utility proof store는 directory fsync failure 뒤 final artifact를 남기지 않으며 rollback failure를 숨기지 않는다.
- proof case, input, evaluation/comparison evidence가 동일한 non-empty project revision에 연결된다.
- focused tests, lint/format/type checks와 가능한 OpenSpec validation의 결과가 Review artifact에 기록된다.

## Research Basis

- 지정된 Inbox review `00-review-review-ai-utility-evaluation.md`의 F1-F5를 현재 HEAD `17d6dbe`에서 재검토했다.
- active OpenSpec Change `review-ai-utility-evaluation`은 `spec-driven-tdd`이며 planning tasks는 6/6 complete 상태다. Review feedback은 동일 Change의 implementation remediation으로 처리하고 범위를 넓히지 않는다.
- local `openspec status`와 `openspec instructions apply`는 성공했지만 pinned npm invocation은 무출력 대기되어 중단했다. strict validation은 별도 limitation으로 남긴다.

## Work Plan

1. Prompt/provenance가 context projection의 selected evidence만 사용하고 validator도 provider-visible reference subset을 검사하도록 보완한다.
1. Utility evaluation model과 runner를 output digest, fixture identity, contribution oracle, complete rubric, project revision에 연결한다.
1. Proof store의 safe path helper와 directory fsync rollback을 구현한다.
1. F1-F5 회귀 tests를 먼저 보강하고 focused suite를 실행한다.
1. 변경된 상태를 별도 review pass로 검증하고 finding disposition을 기록한다.

## Review Transition

구현 후 Review에서 material finding이 남으면 가장 이른 stale prerequisite로 돌아간다. 독립 review capability가 unavailable하면 그 coverage gap을 숨기지 않고 `Not Verified`로 남긴다.

## Loop 2 Remediation

첫 Review에서 F2와 F5가 `current_required`로 남았다. digest와 fixture ID만 가진 baseline/candidate evaluation은 직접 forged evidence를 허용했고, revision 공백 정규화와 dirty tracked worktree의 자동 `HEAD` 귀속이 end-to-end로 보장되지 않았다.

다음 변경을 적용했다.

- `HumanUtilityEvaluation`과 `UtilityComparisonEvidence`가 실제 `AgenticReviewOutput`을 보존하고 digest/contribution kind를 재계산해 검증한다.
- Positive/negative control은 expected incident identity, target column과 deterministic facts oracle에 결속되며, 불완전 rubric과 restatement가 아닌 negative output을 quality basis에서 거부한다.
- Proof case, evaluation, comparison과 quality basis가 동일한 canonical non-empty revision을 사용한다.
- Utility proof runner의 `auto` revision은 clean tracked worktree에서만 HEAD를 사용하고, 작업 중에는 명시적 `--project-revision`을 요구한다.

Loop 2 validation: `tests/review_ai tests/scripts/test_review_ai_utility_proof.py` 109 passed; ty, Ruff, format, `git diff --check`, local `openspec validate review-ai-utility-evaluation --strict`, `rumdl check docs/development/testing.md` passed; explicit revision offline proof reload passed. Next is fresh independent Review of the changed state.
