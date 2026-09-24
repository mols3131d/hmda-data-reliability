---
type: review
title: "PR #245 Final Review — Langfuse-Aware Assessment"
description: "PR #245의 Review AI utility evaluation 변경을 후속 Langfuse 도입 경계와 함께 검토합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "langfuse"
  - "mvp"
---

# PR #245 Final Review — Langfuse-Aware Assessment

> [!CAUTION]
> **Verdict: Changes Required before merge.** Review AI의 bounded context, structured utility contribution, human rubric과 repository-owned identity/safety contract는 유지할 가치가 있다. 그러나 현재 PR은 후속 Langfuse 도입이 맡을 human-evaluation workflow와 겹치는 local evaluation infrastructure를 필요 이상으로 durable하게 만들고 있으며, 이 구조를 더 보강하기 전에 감량하는 편이 낫다. 또한 Langfuse가 대체하지 못하는 input contract mismatch와 comparison role correctness 문제는 남아 있다.

- **Target** — [PR #245 · `feat(review-ai): prove MVP utility evaluation`](https://github.com/mols3131d/hmda-data-reliability/pull/245)
- **Revision** — base `e2e012d845c797ca9d3df93763bb5b7874083478`, reviewed head `3575efba7bc1f29020f50b3b359c9dd3846b65b2`
- **Scope** — Review AI bounded context와 utility evaluation implementation/spec/tests, 현재 Inbox closure plan, 그리고 다음 PR의 optional Langfuse observability/human-annotation boundary

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 **Major** | OpenSpec이 `related-table` Evidence를 요구하지만 `AgenticReviewInput`은 모든 Evidence가 incident와 같은 asset/partition이어야 한다고 강제한다. | Canonical target Evidence와 contextual Evidence의 identity 규칙을 분리해 실제 related-table context를 허용하거나, 지원하지 않을 것이라면 OpenSpec claim을 현재 contract로 축소한다. |
| F2 | 🟠 **Major** | Durable quality-basis/control hierarchy, proof bundle, dedicated store와 synthetic proof runner가 후속 Langfuse의 human annotation/score/comparison surface와 중복될 가능성이 높다. | Repository-owned evaluation semantics만 남기고 platform-like evaluation infrastructure를 merge 전에 감량한다. OpenSpec도 함께 단순화한다. |
| F3 | 🟠 **Major** | `compare_utility_evaluations()`가 baseline/candidate의 `output_kind` semantic role을 검증하지 않아 candidate-vs-candidate도 정상 comparison으로 남을 수 있다. | Minimal comparison contract를 유지한다면 `baseline`/`candidate` role을 fail-closed로 검증하고 swapped/control-role regression test를 추가한다. 해당 layer를 제거하면 제거로 해소한다. |
| F4 | 🟡 **Minor** | `eli5` Rulesync dependency는 Review AI utility proof나 Langfuse follow-up에 필요하지 않은 별도 변경이다. | #245에서 분리한다. managed Rulesync state는 정상 Rulesync workflow로 갱신한다. |

## Details

### F1 — Related-Table Evidence Contract Mismatch

#### Locations

- [`openspec/changes/review-ai-utility-evaluation/specs/reliability-agentic-review/spec.md`](../../openspec/changes/review-ai-utility-evaluation/specs/reliability-agentic-review/spec.md)
  - `Bounded review context`
  - `Context selects bounded evidence and records provenance`
- [`src/hmda_reliability/review_ai/contracts.py`](../../src/hmda_reliability/review_ai/contracts.py)
  - `AgenticReviewInput._validate_review_input`

#### Evidence

OpenSpec의 bounded-context scenario는 canonical null-spike Evidence와 함께 partition metadata, `related-table` 또는 validation Evidence가 review input에 들어오는 경우를 명시한다. 반면 현재 `AgenticReviewInput`은 모든 Evidence의 `(asset_name, partition)`이 incident의 `(asset_name, partition)`과 정확히 같지 않으면 `evidence identity must match the incident`로 거부한다.

따라서 spec이 약속하는 related-table Evidence는 현재 public input contract를 통과할 수 없다. Langfuse는 invocation과 evaluation을 관찰하는 도구이며 어떤 Evidence가 valid Review AI context인지 결정하지 않으므로 이 문제를 대체하거나 해결하지 않는다.

#### Impact

현재 상태로 merge하면 canonical spec에 실행 불가능한 scenario가 남는다. 이후 Langfuse trace에 richer context provenance를 연결하려 해도 upstream input contract에서 related-table Evidence가 이미 거부되므로 observability를 추가해도 제품 capability는 생기지 않는다.

#### Action

Review AI가 실제로 sibling/related-table context를 활용하려는 방향이라면 canonical target Evidence와 contextual Evidence의 identity rule을 최소 범위로 분리한다. Canonical null-spike PROFILE Evidence는 incident target과 exact identity를 유지하고, contextual Evidence는 명시적으로 참조된 bounded evidence라는 조건 아래 다른 asset identity를 허용하는 방식이 적절하다.

그 범위를 이번 MVP에서 원하지 않는다면 implementation을 억지로 넓히지 말고 OpenSpec에서 `related-table` claim을 제거해 실제 지원 경계와 맞춘다.

### F2 — Evaluation Infrastructure Should Be Reduced Before Langfuse

#### Locations

- [`src/hmda_reliability/review_ai/evaluation.py`](../../src/hmda_reliability/review_ai/evaluation.py)
  - `UtilityControl`
  - `ControlValidationResult`
  - `QualityBasisValidation`
  - `UtilityProofCase`
  - `UtilityProofBundle`
- [`src/hmda_reliability/review_ai/evaluation_store.py`](../../src/hmda_reliability/review_ai/evaluation_store.py)
- [`scripts/run_review_ai_utility_proof.py`](../../scripts/run_review_ai_utility_proof.py)
- [`11-report-review-ai-overengineering-assessment.md`](11-report-review-ai-overengineering-assessment.md)
- [`19-plan-review-ai-pr245-closure/14-langfuse-next-pr.md`](19-plan-review-ai-pr245-closure/14-langfuse-next-pr.md)

#### Evidence

현재 repository 내부 assessment도 quality-basis/control 계층, proof bundle, create-only evidence store와 큰 synthetic runner를 MVP보다 무거운 evaluation infrastructure로 식별하고 있다. 후속 Langfuse 계획 역시 repository가 rubric identity, evaluation semantics, same-case invariant와 deterministic safety를 계속 소유하고, Langfuse는 필요성이 확인된 tracing과 human annotation surface만 담당하도록 경계를 정의한다.

현재 Langfuse 공식 surface는 이 경계를 실질적으로 지원한다.

- [Annotation Queues](https://langfuse.com/docs/evaluation/evaluation-methods/annotation-queues)는 사람이 trace/observation/session에 score와 comment를 기록하고 domain expert review workflow를 수행하는 기능을 제공한다.
- [Scores](https://langfuse.com/docs/evaluation/scores/overview)는 human annotation을 포함한 evaluation result를 공통 score object로 저장하고 API로 조회할 수 있게 한다.
- [Compare experiments](https://langfuse.com/docs/evaluation/experiments/compare-experiments)는 baseline/candidate run을 같은 case 기준으로 비교하고 human scores와 annotation queue를 함께 사용할 수 있게 한다. 공식 문서도 baseline approval과 release gate policy 자체는 repository에 남겨야 한다고 명시한다.
- [Trace IDs & Distributed Tracing](https://langfuse.com/docs/observability/features/trace-ids-and-distributed-tracing)는 external request identity를 deterministic trace ID와 연결할 수 있게 한다.

즉 Langfuse 도입이 예정된 상황에서는 human evaluation UI, score storage, review queue와 baseline/candidate inspection을 repository 내부에서 별도 platform처럼 구현하는 비용의 정당성이 더 낮아진다.

#### Impact

#245에서 local evaluation infrastructure를 더 durable하게 만들수록 다음 PR은 integration이 아니라 migration/refactor가 된다. 특히 control hierarchy와 proof bundle/store를 canonical product contract로 굳히면 Langfuse annotation을 연결하기 위해 vendor-neutral semantics와 local persistence semantics를 동시에 유지해야 하며, 실제 제품 가치보다 compatibility cost가 커질 수 있다.

반대로 repository가 소유해야 할 의미까지 Langfuse에 넘기면 vendor dependency가 deterministic safety와 evaluation policy의 authority가 된다. 따라서 제거 대상은 evaluation semantics가 아니라 workflow/persistence 중복이다.

#### Action

Merge 전 목표 구조를 다음 수준으로 줄이는 것을 권장한다.

```text
AgenticReviewInput
        ↓
BoundedReviewContext
        ↓
AgenticReviewOutput
  + utility_contributions
        ↓
HumanUtilityEvaluation
  - case/version
  - invocation/revision/output identity
  - five rubric scores + rationale
        ↓
UtilityComparisonEvidence
  - same-case validation
  - criterion deltas
  - change_under_test
  - human decision + rationale
```

Repository에 남길 것은 다음이다.

- five-criterion rubric의 identity와 의미
- bounded context와 utility contribution contract
- exact case/version/revision/output attribution
- baseline/candidate semantic role과 same-case fail-closed validation
- deterministic safety와 advisory authority boundary
- candidate 채택 또는 delegation policy에 대한 repository-owned decision rule

다음은 우선 test/support 수준으로 낮추거나 제거한다.

- positive/restatement/hedging control의 durable runtime hierarchy — discrimination test fixture로 유지
- `QualityBasisValidation`의 durable evidence hierarchy — 실제 runtime consumer가 없다면 제거
- `UtilityProofCase` / `UtilityProofBundle` — comparison/evaluation identity와 중복되는 wrapper 제거
- `UtilityEvidenceStore`의 create-only/fsync/hard-link semantics — 현재 MVP acceptance에 필요한 별도 audit store 근거가 없다면 제거
- synthetic runner가 고정 human score와 `ACCEPT`를 생성하는 proof flow — focused tests 또는 작은 fixture support로 축소

이 감량은 code deletion만으로 끝내지 않고 현재 delta OpenSpec의 durable quality-basis/proof-bundle requirement도 같은 ownership 경계로 수정해야 한다.

### F3 — Comparison Does Not Validate Baseline/Candidate Roles

#### Locations

- [`src/hmda_reliability/review_ai/evaluation.py`](../../src/hmda_reliability/review_ai/evaluation.py)
  - `HumanUtilityEvaluation.output_kind`
  - `compare_utility_evaluations`
- [`tests/review_ai/test_utility_evaluation.py`](../../tests/review_ai/test_utility_evaluation.py)
  - `_evaluation`
  - `test_proof_bundle_store_preserves_case_basis_and_comparison`

#### Evidence

`HumanUtilityEvaluation.output_kind`는 `baseline`과 `candidate`를 구분하지만 `compare_utility_evaluations()`는 case, rubric, revision, quality basis, completeness와 deterministic facts만 비교하고 `baseline.output_kind == "baseline"` 및 `candidate.output_kind == "candidate"`를 확인하지 않는다.

테스트 helper `_evaluation()`의 기본 `output_kind`는 `candidate`다. `test_proof_bundle_store_preserves_case_basis_and_comparison`은 baseline argument를 만들 때 `output_kind="baseline"`을 지정하지 않으므로 실제로는 candidate evaluation 두 개를 비교하지만 comparison과 proof bundle이 정상 생성된다. 이는 단순한 hypothetical risk가 아니라 현재 test suite가 허용하는 실행 가능한 semantic mismatch다.

#### Impact

Baseline과 candidate는 같은 schema를 가진 두 output 이상의 의미를 가진다. 어느 것이 승인된 비교 기준이고 어느 것이 변경 후보인지 attribution이 깨지면 score delta와 human decision 자체는 형식적으로 맞더라도 comparison evidence의 의미가 잘못된다. Langfuse에서도 baseline 선택과 repository release policy를 분리하므로 repository 쪽 role validation은 여전히 필요하다.

#### Action

F2 감량 후 `HumanUtilityEvaluation`과 `UtilityComparisonEvidence`를 유지한다면 comparison boundary에서 role을 명시적으로 검증한다. swapped roles, candidate-vs-candidate, control-vs-candidate를 모두 fail-closed하는 focused regression test를 추가한다. F2 감량 과정에서 해당 custom comparison layer 자체를 제거한다면 별도 patch를 추가하지 않고 제거로 finding을 해소한다.

### F4 — Unrelated ELI5 Rulesync Scope

#### Locations

- [`rulesync.jsonc`](../../rulesync.jsonc)
- [`.agents/route/skills.jsonl`](../../.agents/route/skills.jsonl)
- [`19-plan-review-ai-pr245-closure/06-resolve-eli5-scope.md`](19-plan-review-ai-pr245-closure/06-resolve-eli5-scope.md)

#### Evidence

현재 closure plan 자체가 ELI5를 #245의 Review AI utility change와 분리해야 한다는 기준을 이미 정의한다. Review AI runtime, utility evaluation 또는 다음 Langfuse integration이 ELI5 Agent Asset에 의존한다는 근거는 확인되지 않았다.

#### Impact

기능 defect는 아니지만 67-file PR의 review surface와 변경 목적을 더 넓히고, Review AI 변경의 rollback과 ownership을 불필요하게 결합한다.

#### Action

ELI5 도입은 별도 change unit으로 이동한다. `rulesync.lock` 같은 managed state가 영향을 받는 경우 원격에서 수동 편집하지 않고 정상 Rulesync workflow에서 생성한다.

## Recommended Merge Shape

#245가 다음 PR의 Langfuse integration을 위한 깨끗한 substrate가 되려면 merge 전 상태는 다음 조건을 만족하는 편이 낫다.

1. F1을 implementation 또는 spec 축소 중 하나로 해소한다.
1. evaluation contract를 `HumanUtilityEvaluation`과 최소 `UtilityComparisonEvidence` 중심으로 줄이고 OpenSpec을 같은 경계로 맞춘다.
1. comparison을 유지한다면 F3 semantic role validation을 추가한다.
1. control discrimination은 focused test fixture로 보존하되 runtime quality-basis platform으로 승격하지 않는다.
1. dedicated proof/store/runner는 current repository-owned requirement가 입증되는 부분만 남긴다.
1. ELI5 변경을 #245에서 분리한다.
1. 감량된 head에서 focused tests, OpenSpec strict validation과 CI를 다시 실행한 뒤 fresh review를 수행한다.

다음 Langfuse PR은 그 위에서 optional trace projection과 human annotation mapping부터 시작한다. Langfuse가 unavailable이어도 Review AI core와 deterministic validation은 그대로 동작해야 하며, 첫 integration에서 Prompt Management authority 이전, generic evaluation backend, two-way sync, polling worker 또는 production-grade self-host infrastructure를 만들 필요는 없다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Reviewed revision freshness | 작성 직전 PR #245 head가 `3575efba7bc1f29020f50b3b359c9dd3846b65b2`로 유지되고 Draft/Open 상태임을 확인했다. |
| ✅ Pass | Exact-head CI | `CI Lite` run `#1075` (`35900598340`)이 reviewed head에서 `success`다. |
| ✅ Pass | Source/spec/test consistency review | `AgenticReviewInput`, utility evaluation/comparison models, relevant tests와 OpenSpec delta를 reviewed head에서 직접 대조했다. |
| ✅ Pass | Langfuse supported-surface review | 2026-09-24 기준 Langfuse 공식 문서에서 Annotation Queues, Scores, experiment comparison과 deterministic trace correlation surface를 확인했다. |
| ⚪ Not Verified | Local test execution in this review | 이 review 작성 과정에서는 별도 local checkout에서 pytest를 재실행하지 않았다. Exact-head CI와 current source/test inspection을 사용했다. |
| ⚪ Not Verified | Live Langfuse smoke | Langfuse integration은 다음 PR의 decision-first 조건 이후 opt-in smoke로 검증해야 한다. |
| ⚪ Not Verified | Independent dual-perspective review | 현재 runtime에서 repository의 `review-lead` 기반 독립 dual review를 수행하지 않았다. 이 문서를 그와 동등한 independent review로 취급하지 않는다. |

## Risks and Limits

Langfuse의 API와 product surface는 이후 변경될 수 있으므로 다음 PR에서는 공식 문서를 다시 확인해야 한다. 이 review가 권고하는 감량은 특정 Langfuse schema에 core contract를 맞추기 위한 것이 아니라, 현재도 repository-owned semantics와 platform-owned workflow를 분리할 수 있다는 근거에 기반한다.

또한 현재 offline runner와 synthetic human scores는 contract와 fixture를 검증할 수 있지만 실제 사람이 live provider output을 평가해 utility를 입증한 근거는 아니다. PR body가 이미 이 경계를 명시하고 있으므로 별도 blocker로 중복 등록하지 않지만, merge 후에도 offline proof를 live utility evidence로 승격해서는 안 된다.
