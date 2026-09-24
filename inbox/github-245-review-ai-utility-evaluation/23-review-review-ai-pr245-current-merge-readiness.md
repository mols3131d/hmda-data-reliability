---
type: review
title: "PR #245 Current Merge Readiness Review"
description: "PR #245의 최신 head를 기준으로 구현, CI, OpenSpec 정합성과 실제 merge 전 남은 조건을 검토합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
  - "merge-readiness"
---

# PR #245 Current Merge Readiness Review

> [!WARNING]
> **Conditionally Ready.** Reviewed head `598a99aa192654464c95bad617512acd0034bd1f`의 구현과 prospective-merge CI는 merge 가능한 수준이다. 추가 evaluation infrastructure를 만들 필요는 없다. 다만 merge 전에 OpenSpec design의 stale utility-candidate 문장과 PR description의 stale CI 상태를 현재 구현에 맞게 정리하고 Draft 상태를 해제하는 것이 적절하다.

- **Target** — [PR #245 · `feat(review-ai): prove MVP utility evaluation`](https://github.com/mols3131d/hmda-data-reliability/pull/245)
- **Revision** — base `569c2b9c2c9f5b765d7210217325f8e1b99ee365`, reviewed head `598a99aa192654464c95bad617512acd0034bd1f`
- **Scope** — 최신 PR mergeability, prospective-merge CI, Review AI utility evaluation contract/tests, active OpenSpec completion 상태와 merge 전 문서 정합성

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟡 **Minor** | OpenSpec design이 contribution이 있는 output만 utility proof candidate로 평가한다고 서술하지만 current evaluation contract는 이를 validity condition으로 요구하지 않는다. | `design.md`의 해당 문장을 human rubric이 utility를 판정하고 contribution 존재 자체는 pass 조건이 아니라는 현재 경계로 수정한다. 코드나 새 abstraction은 추가하지 않는다. |
| F2 | 🟡 **Minor** | PR description은 최신 head의 `CI Lite`가 아직 결과 대기 중이라고 기록하지만 run #1080은 이미 성공했다. | Validation 문장을 current CI result로 갱신한다. |

## Details

### F1 — OpenSpec Design Still Implies a Contribution Gate

#### Locations

- [`openspec/changes/review-ai-utility-evaluation/design.md`](../../openspec/changes/review-ai-utility-evaluation/design.md)
  - `Technical Delta`
- [`src/hmda_reliability/review_ai/evaluation.py`](../../src/hmda_reliability/review_ai/evaluation.py)
  - `HumanUtilityEvaluation`
  - `compare_utility_evaluations`

#### Evidence

`design.md`는 새 utility evaluation이 `utility_contributions`가 있는 output만 utility proof candidate로 평가한다고 서술한다. 그러나 current `HumanUtilityEvaluation`은 exact output digest, five-criterion score/rationale, case/version, invocation, revision과 baseline/candidate role을 검증할 뿐 contribution 존재를 validity invariant로 사용하지 않는다.

현재 감량 방향과 다음 Langfuse integration boundary도 utility의 최종 판정을 model-declared contribution 존재가 아니라 human rubric에 남기는 편이 일관된다. Positive/restatement/hedging 사례는 runtime quality hierarchy가 아니라 test fixture로만 유지된다.

#### Impact

Runtime correctness를 깨뜨리지는 않지만 design document가 실제 contract보다 강한 gate를 암시한다. 다음 Langfuse human annotation mapping에서 이 문장을 그대로 읽으면 contribution 존재를 utility score의 proxy로 잘못 구현할 가능성이 생긴다.

#### Action

해당 문장만 current implementation과 ownership boundary에 맞춘다. `utility_contributions` schema 자체, `HumanUtilityEvaluation` 또는 comparison contract를 확장하지 않는다.

### F2 — PR Validation Text Is Stale

#### Locations

- [PR #245 description](https://github.com/mols3131d/hmda-data-reliability/pull/245)
  - `Validation`
- [CI Lite run #1080](https://github.com/mols3131d/hmda-data-reliability/actions/runs/35993534919)

#### Evidence

PR description은 `GitHub CI Lite는 새 head에서 결과를 기다리는 중입니다.`라고 기록한다. Reviewed head `598a99aa192654464c95bad617512acd0034bd1f`에 연결된 `CI Lite` run #1080은 `completed / success`이며, prospective merge checkout, OpenSpec validation, Python validation, package build, dependency boundary, chatbot routes와 selected tests가 모두 성공했다.

#### Impact

Merge correctness 문제는 아니지만 PR이 전달하는 validation freshness가 실제 GitHub 상태보다 뒤처진다. Merge 직전 독자가 current head의 검증 상태를 잘못 판단할 수 있다.

#### Action

대기 문장을 run #1080 성공으로 갱신하고 exact reviewed head를 유지한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | GitHub mergeability | Reviewed head에서 PR #245는 `mergeable: true`이며 base는 current `main` `569c2b9c2c9f5b765d7210217325f8e1b99ee365`다. |
| ✅ Pass | Exact-head CI Lite | Run #1080 (`35993534919`)이 reviewed head `598a99aa192654464c95bad617512acd0034bd1f`에서 `completed / success`다. |
| ✅ Pass | Prospective merge validation | CI job의 `Checkout prospective merge`, `Validate OpenSpec`, `Validate Python`, `Verify package build`, `Check Python dependency boundaries`, `Validate chatbot routes`, `Run selected tests`가 모두 성공했다. |
| ✅ Pass | OpenSpec task completion | `openspec/changes/review-ai-utility-evaluation/tasks.md`는 `tasks_completed: 6`, `tasks_total: 6`이며 여섯 task가 모두 완료 상태다. |
| ✅ Pass | Evaluation simplification boundary | Dedicated proof store와 fixed-score proof runner는 제거되어 있고 current comparison은 case/version/revision, output role, deterministic facts와 exact output digest를 fail-closed로 검증한다. |
| ⚪ Not Verified | Live provider and human utility | 실제 human evaluator의 utility assessment와 live provider proof는 이 merge-readiness review에서 수행하지 않았다. 현재 PR도 이를 deterministic fixture proof와 구분하고 있으며 다음 LLMOps/Langfuse 단계의 evidence로 남긴다. |
| ⚪ Not Verified | Dual-perspective independent orchestration | 이 runtime에서는 repository의 `review-lead` subagent orchestration을 사용할 수 없어 동일 context의 review methodology로 검토했다. 이 보고서를 독립 GitHub approval로 취급하지 않는다. |

## Risks and Limits

이 review는 `598a99aa192654464c95bad617512acd0034bd1f`를 대상으로 한다. 이 Inbox artifact를 branch에 추가하는 commit 자체는 reviewed head 이후의 documentation-only change이므로, 실제 merge 시점에는 resulting head의 GitHub CI freshness를 다시 확인해야 한다.

`HumanUtilityEvaluation`은 현재 same case를 `case_id`, `case_version`, `project_revision`, baseline/candidate role과 deterministic incident facts로 묶는다. 전체 canonical review input identity를 별도 digest로 고정하지는 않는다. 이 한계를 해결하기 위해 #245에서 generic experiment registry, evaluation backend, 별도 persistence 또는 controlled-experiment framework를 선제 구축하는 것은 권장하지 않는다. 다음 Langfuse integration에서 실제 annotation/import가 exact input identity를 요구할 때 repository-owned invocation provenance를 사용해 필요한 최소 binding만 추가하는 편이 낫다.
