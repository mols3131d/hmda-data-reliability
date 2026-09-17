---
type: review
title: "PR #245 Utility Proof Semantics Review"
description: "PR #245 head 0b1ebdd의 utility proof semantics, human-evaluation attribution, same-case binding을 검토합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
---

> [!IMPORTANT]
> **Blocked** — bounded context, output binding, create-only evidence store의 방향은 적절하지만, 현재 offline proof는 human utility를 독립적으로 입증하지 못하고 same-case 비교도 실제 deterministic output identity까지 강제하지 않습니다. 두 finding을 해소하기 전에는 `compared / accept` 결과를 MVP utility proof의 acceptance evidence로 사용하지 않는 것이 안전합니다.

## Review Context

- Target: PR #245 `feat(review-ai): prove MVP utility evaluation`
- Revision: base `2a793f4c23745abd485f26b15421b17c744760fa`, reviewed head `0b1ebdd31795fbb718179d57a0670cb9a95e4eb2`
- Scope: offline utility proof semantics, human rubric attribution, baseline/candidate same-case binding, 관련 OpenSpec requirement와 test oracle. 구현 변경과 live provider 실행은 제외합니다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 Major | Offline proof가 candidate output, rubric score, rationale, `ACCEPT` decision을 같은 runner 안에서 직접 생성해 실제 human utility evidence를 대체합니다. | Human evaluation artifact를 runner 밖에서 입력받거나, 현재 runner의 claim을 contract/fixture validation으로 낮추고 실제 human proof를 별도 gate로 둡니다. |
| F2 | 🟠 Major | `same case` 비교가 `case_id/version`에는 묶이지만 baseline/candidate의 incident, target column, deterministic facts와 quality-basis revision의 동일성을 comparison contract에서 강제하지 않습니다. | `COMPARED` 전에 actual output oracle과 case/input digest 및 quality-basis revision을 검증하고 mismatch negative test를 추가합니다. |

## Details

### F1 — Self-authored Human Utility Proof

#### Locations

- [`scripts/run_review_ai_utility_proof.py`](../../scripts/run_review_ai_utility_proof.py)
  - `build_representative_utility_proof`
  - `_evaluation`
- [`openspec/changes/review-ai-utility-evaluation/specs/reliability-agentic-review/spec.md`](../../openspec/changes/review-ai-utility-evaluation/specs/reliability-agentic-review/spec.md)
  - `Requirement: Versioned human rubric and control discrimination`
  - `Requirement: Baseline and candidate utility comparison evidence`
- [`tests/scripts/test_review_ai_utility_proof.py`](../../tests/scripts/test_review_ai_utility_proof.py)
  - `test_representative_fixture_proves_controls_and_comparison`

#### Evidence

Runner는 baseline output을 utility contribution 없이 만들고 candidate output에는 `evidence_gap`, `investigation_priority`, `remediation_critique`, `material_uncertainty` 네 contribution을 직접 작성합니다. 같은 함수 안에서 baseline evaluation은 다섯 rubric criterion을 모두 `0`, candidate와 positive control은 모두 `2`로 지정하며, rationale은 `Human score for <criterion>` 형식의 생성 문자열입니다. 최종 comparison decision도 `HumanDecision.ACCEPT`로 직접 전달합니다.

따라서 현재 clean-HEAD offline proof의 `compared / accept`, 각 criterion `+2`, total `+10`은 외부 human evaluator가 실제 baseline/candidate output을 읽고 판단한 결과가 아니라 proof generator가 미리 구성한 fixture와 score를 계약이 받아들이는지 확인한 결과입니다. 반면 OpenSpec은 representative output을 human evaluator가 평가하고 각 criterion에 human score와 non-empty rationale가 있어야 한다고 요구합니다.

#### Impact

현재 runner는 evaluation contract, digest binding, persistence와 replay를 검증하는 fixture로는 유효합니다. 그러나 이 결과를 그대로 “Review AI가 deterministic summary를 넘어 실제 사람의 조사·복구 판단에 기여했다”는 MVP utility proof로 사용하면 검증 대상과 판정자가 같은 코드 경계에 있어 false green이 됩니다. 특히 PR description의 `compared / accept`와 `+10`은 실제 utility보다 fixture construction을 반영합니다.

#### Action

다음 두 방식 중 하나로 proof claim과 evidence source를 일치시킵니다.

- 실제 utility proof가 목적이면 runner는 retained baseline/candidate output과 별도로 작성된 human evaluation artifact를 입력받고, score/rationale/decision을 생성하지 않습니다.
- 현재 범위를 유지하려면 runner를 `utility evaluation contract fixture` 또는 동등한 성격으로 명확히 낮추고, 실제 human utility comparison은 별도의 acceptance gate와 evidence artifact로 남깁니다.

두 경우 모두 proof generator 내부에서 human score, human rationale와 acceptance decision을 합성한 결과를 human evaluation evidence로 승격하지 않습니다.

### F2 — Same-case Binding Is Incomplete

#### Locations

- [`src/hmda_reliability/review_ai/evaluation.py`](../../src/hmda_reliability/review_ai/evaluation.py)
  - `compare_utility_evaluations`
  - `UtilityComparisonEvidence`
  - `UtilityProofBundle._validate_bundle_links`
- [`src/hmda_reliability/review_ai/evaluation_store.py`](../../src/hmda_reliability/review_ai/evaluation_store.py)
  - `UtilityEvidenceStore.write`
- [`tests/review_ai/test_utility_evaluation.py`](../../tests/review_ai/test_utility_evaluation.py)

#### Evidence

`compare_utility_evaluations()`는 baseline/candidate의 `case_id`, `case_version`, `rubric_id`, `project_revision`, rubric completeness를 비교합니다. 그러나 `COMPARED` 상태를 만들기 전에 두 `AgenticReviewOutput`의 `incident_id`, `target_column`, `deterministic_facts`가 같은지 확인하지 않습니다. 동일한 `case_id/version` 문자열을 가진 서로 다른 deterministic incident output도 comparison contract 자체에서는 비교 대상으로 통과할 수 있습니다.

또한 comparison 생성 시 `quality_basis.project_revision`과 baseline/candidate의 `project_revision`이 같은지 직접 검증하지 않습니다. `UtilityProofBundle`은 valid quality basis를 bundle에 넣었을 때 revision을 추가로 묶지만, `UtilityEvidenceStore.write()`는 standalone `UtilityComparisonEvidence`도 durable evidence로 저장할 수 있습니다. 따라서 comparison contract 자체의 `COMPARED` 의미가 proof bundle 경계보다 약합니다.

현재 tests는 case ID mismatch, incomplete evaluation, digest tampering과 control mismatch를 다루지만, 같은 `case_id/version` 아래 deterministic facts가 다른 baseline/candidate 또는 stale quality-basis revision을 `COMPARED`에서 차단하는 negative case는 확인되지 않았습니다.

#### Impact

PR이 주장하는 score delta는 “같은 representative case에서 변경 전후 output만 달라졌다”는 전제가 성립할 때 의미가 있습니다. 현재 contract는 그 전제를 label 수준에서만 강제하므로 fixture identity가 잘못 유지되거나 stale basis가 재사용되면 다른 incident state 사이의 score 차이를 변경 효과로 기록할 수 있습니다. 이 경우 create-only 저장과 digest integrity가 모두 정상이어도 attribution 자체가 잘못됩니다.

#### Action

`COMPARED`가 되기 전에 최소한 다음 identity를 deterministic하게 검증합니다.

- baseline/candidate `incident_id`
- `target_column`
- `deterministic_facts`
- representative case 또는 canonical input digest
- `quality_basis.project_revision == baseline.project_revision == candidate.project_revision`

그리고 deterministic facts mismatch와 stale quality-basis revision이 `blocked` 또는 validation error로 끝나는 negative test를 추가합니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Reviewed revision | Artifact 작성 직전 PR #245 head가 `0b1ebdd31795fbb718179d57a0670cb9a95e4eb2`, base가 `2a793f4c23745abd485f26b15421b17c744760fa`임을 다시 확인했습니다. |
| ✅ Pass | Existing Inbox continuity | 기존 `00` review, `01` plan, `02` remediation review를 보존하고 sequence 다음 번호인 `03` fresh review로 분리했습니다. |
| ✅ Pass | Contract/code/test cross-check | OpenSpec human-rubric requirement를 runner, evaluation contract, store, related tests와 대조했습니다. |
| ✅ Pass | CI state | Reviewed head의 GitHub `CI Lite` workflow가 success 상태임을 확인했습니다. |
| ⚪ Not Verified | Local focused tests | 이번 review session에서는 pytest를 직접 재실행하지 않았습니다. PR이 보고한 focused test evidence와 CI result를 별도 evidence로만 취급했습니다. |
| ⚪ Not Verified | Full repository suite | PR description 자체가 remediation 이후 full suite를 미실행으로 기록하고 있습니다. |
| ⚪ Not Verified | Live provider utility | Offline proof는 provider를 호출하지 않으므로 실제 provider output의 utility는 이 review에서 검증하지 않았습니다. |
| ⚪ Not Verified | Independent dual-perspective review | 현재 runtime에서 repository `review-lead` orchestration을 사용할 수 없어 같은-context review로 수행했습니다. 이를 formal independent review와 동등하게 취급하지 않습니다. |

## Risks and Limits

- 이 artifact는 reviewed head `0b1ebdd31795fbb718179d57a0670cb9a95e4eb2`에 대한 판단입니다. 이후 implementation, spec 또는 proof runner가 실질적으로 변경되면 findings를 다시 검증해야 합니다.
- F1과 F2는 CI pass 여부와 독립적인 proof semantics 문제입니다. 기존 automated validation이 모두 통과해도 두 acceptance gap은 남을 수 있습니다.
- 이 review는 기존 `02` artifact를 폐기하거나 수정하지 않습니다. `02`는 당시 F1-F5 remediation 상태를 기록하고, 이 문서는 그 이후 current-head proof claim을 별도로 검토한 fresh review입니다.
