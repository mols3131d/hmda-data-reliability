---
type: review
title: "PR #245 Current Review AI Utility Proof Status Review"
description: "PR #245 current head에서 기존 utility proof review의 freshness와 잔여 acceptance finding을 재검증합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
---

> [!IMPORTANT]
> **Blocked** — 현재 PR head에서도 utility proof semantics의 F1/F2가 유효하며, 독립 dual-perspective formal review도 완료되지 않았습니다. `02`는 historical remediation record이고, 이 문서가 현재 head에 대한 review handoff입니다.

## Target

- **Target** — [PR #245](https://github.com/mols3131d/hmda-data-reliability/pull/245), Review AI utility proof implementation, tests, OpenSpec requirement와 관련 Inbox review
- **Revision** — base `2a793f4c23745abd485f26b15421b17c744760fa`, head `b884fa47b0791f06dc482c4b4caae5c7bb06caa6`
- **Scope** — utility proof semantics, human-evaluation attribution, baseline/candidate same-case binding, prior review freshness와 현재 PR/CI state

Live provider 실행, 구현 수정, PR 상태 변경과 merge/approval은 범위에서 제외합니다.

## Artifact Freshness

- [`02-review-review-ai-utility-evaluation-improvement.md`](02-review-review-ai-utility-evaluation-improvement.md)는 original head `17d6dbe`와 당시 uncommitted working tree를 기록한 historical remediation review입니다. F1-F5의 구현 보정 근거는 참고할 수 있지만, 현재 PR의 status source로 사용할 수 없습니다. 특히 당시의 “No commit, push, PR update” 문장은 현재 상태와 다릅니다.
- [`03-review-review-ai-utility-proof-semantics.md`](03-review-review-ai-utility-proof-semantics.md)는 parent head `0b1ebdd`를 검토했습니다. 이후 `b884fa4`는 해당 review artifact만 추가했으므로 implementation behavior는 바뀌지 않았고 F1/F2 finding은 현재 head에도 승계됩니다. 다만 exact reviewed head metadata는 현재 head와 다르므로 이 문서의 현재 판정으로 revalidate했습니다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 Major | Offline runner가 human score, rationale와 `ACCEPT` decision을 직접 합성해 실제 human utility evidence처럼 표시합니다. | 외부에 보존된 human evaluation artifact를 입력받거나, runner claim을 contract/fixture validation으로 낮추고 실제 human proof를 별도 acceptance gate로 둡니다. |
| F2 | 🟠 Major | `COMPARED`가 case label과 baseline/candidate revision만 확인하고 actual deterministic output identity 및 quality-basis revision을 강제하지 않습니다. | `COMPARED` 전에 incident, target, deterministic facts, canonical input/case digest와 quality-basis revision을 모두 검증하고 mismatch negative test를 추가합니다. |
| G1 | 🟠 Major | 필요한 독립 dual-perspective formal review가 완료되지 않았습니다. | 독립 review-lead 결과가 완료될 때까지 Draft와 Blocked 상태를 유지합니다. |

## Details

### F1 · Offline proof가 human utility evidence를 자체 생성함

#### F1 Locations

- [`scripts/run_review_ai_utility_proof.py`](../../scripts/run_review_ai_utility_proof.py)
  - `build_representative_utility_proof`
  - `_evaluation`
- [`openspec/changes/review-ai-utility-evaluation/specs/reliability-agentic-review/spec.md`](../../openspec/changes/review-ai-utility-evaluation/specs/reliability-agentic-review/spec.md)
  - `Versioned human rubric and control discrimination`
  - `Baseline and candidate utility comparison evidence`

#### F1 Evidence

현재 runner는 positive control과 candidate에 `score=2`, negative control와 baseline에 `score=0`을 코드로 지정하고, `Human score for <criterion>` rationale을 생성합니다. 이어서 `HumanDecision.ACCEPT`를 같은 runner가 comparison에 전달합니다. OpenSpec은 representative output을 `human evaluator`가 평가하고 각 criterion에 human score와 rationale이 있어야 한다고 요구합니다.

#### F1 Impact

현재 `compared / accept`와 total delta `+10`은 실제 사람이 output을 읽고 판단했다는 증거가 아니라, 미리 구성된 fixture와 evaluation contract가 통과했다는 증거입니다. 따라서 PR의 utility acceptance claim을 그대로 확정하면 evaluator와 proof generator가 같은 신뢰 경계에 놓이는 false green이 발생합니다.

#### F1 Action

실제 utility proof라면 runner가 score, rationale, decision을 생성하지 말고 별도 human evaluation artifact를 검증해야 합니다. Fixture 계약 검증만 의도했다면 명칭과 PR claim을 contract/fixture validation으로 낮추고 human utility proof를 별도 gate로 분리해야 합니다.

### F2 · Same-case attribution이 불완전함

#### F2 Locations

- [`src/hmda_reliability/review_ai/evaluation.py`](../../src/hmda_reliability/review_ai/evaluation.py)
  - `compare_utility_evaluations`
  - `UtilityComparisonEvidence`
  - `UtilityProofBundle._validate_bundle_links`
- [`tests/review_ai/test_utility_evaluation.py`](../../tests/review_ai/test_utility_evaluation.py)
  - existing digest/control mismatch coverage

#### F2 Evidence

`compare_utility_evaluations()`는 baseline/candidate의 case ID/version, rubric ID, project revision과 completeness를 확인하지만, 두 `AgenticReviewOutput`의 incident, target column, deterministic facts를 비교하지 않습니다. 또한 `quality_basis.project_revision`과 evaluation revision의 일치를 comparison 단계에서 확인하지 않습니다.

현재 head에서 transient reproduction을 실행한 결과도 다음과 같습니다.

- baseline deterministic fact `current_null_rate=0.21`, candidate `0.99`인데 `basis_valid=True`, `status=compared`, `blocker=None`
- quality basis revision이 `stale-revision`, evaluation revision이 `test-revision`이어도 `status=compared`, `blocker=None`

#### F2 Impact

동일한 case label을 가진 서로 다른 incident state 또는 stale quality basis를 비교해도 score delta가 변경 효과로 durable evidence에 기록될 수 있습니다. Digest integrity와 create-only storage가 정상이어도 attribution 전제가 틀리면 utility comparison의 의미가 훼손됩니다.

#### F2 Action

`COMPARED` 전환 조건에 baseline/candidate의 incident ID, target column, deterministic facts, canonical input 또는 case digest와 `quality_basis.project_revision == baseline.project_revision == candidate.project_revision`를 추가합니다. 각 mismatch를 `blocked` 또는 validation error로 확인하는 negative test를 추가합니다.

### G1 · 독립 formal review coverage 미완료

#### G1 Locations

- [PR #245](https://github.com/mols3131d/hmda-data-reliability/pull/245)
  - current review list is empty
  - current state is Draft
- [`03-review-review-ai-utility-proof-semantics.md`](03-review-review-ai-utility-proof-semantics.md)
  - independent dual-perspective review limitation

#### G1 Evidence

현재 PR head `b884fa4`의 CI check는 성공했지만, GitHub review submission은 없고 Draft 상태입니다. 이번 review에서 요청한 independent `review-lead`도 결과를 반환하지 않아 local same-context evidence를 formal independent review로 승격하지 않았습니다.

#### G1 Impact

F1/F2가 실제로 acceptance를 차단하는지에 대한 독립 검토 coverage가 없으므로, CI 성공만으로 PR을 merge-ready로 판단할 수 없습니다.

#### G1 Action

독립 review-lead의 quality/adversarial 결과를 완료한 뒤 현재 head를 다시 고정하고 F1/F2 disposition을 갱신합니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Current revision | PR base/head가 `2a793f4c23745abd485f26b15421b17c744760fa` / `b884fa47b0791f06dc482c4b4caae5c7bb06caa6`이고 working tree는 clean입니다. |
| ✅ Pass | Intervening change scope | `0b1ebdd..b884fa4` diff는 `03-review-review-ai-utility-proof-semantics.md` 추가 한 파일뿐이므로 implementation behavior는 unchanged입니다. |
| ✅ Pass | Remote CI | Current PR head의 CI Lite `check`는 `SUCCESS`입니다. |
| ✅ Pass | F1 source/spec cross-check | Runner의 score/rationale/decision 생성과 OpenSpec의 human-evaluator requirement를 대조했습니다. |
| ✅ Pass | F2 semantic reproduction | deterministic facts mismatch와 stale quality-basis revision 모두 `compared`/no blocker로 재현했습니다. |
| ⚪ Not Verified | Full repository suite after remediation | PR description은 remediation 이후 full suite 미실행으로 기록하고 있습니다. |
| ⚪ Not Verified | Live provider utility | Offline runner는 provider를 호출하지 않습니다. |
| ⚪ Not Verified | Independent dual-perspective review | review-lead가 결과를 반환하지 않았습니다. |

## Risks and Limits

- F1/F2는 현재 head의 implementation/spec semantics finding이며, CI가 성공해도 자동으로 해소되지 않습니다.
- 이후 utility evaluation contract, runner 또는 OpenSpec spec이 변경되면 이 report의 finding과 reproduction을 다시 확인해야 합니다.
- 이 문서는 review 결과를 기록하며 구현 수정, PR approval, Ready 전환 또는 merge를 수행하지 않습니다.
