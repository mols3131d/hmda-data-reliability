---
type: review
title: "PR #245 Current-Head Review"
description: "PR #245의 current head에서 utility comparison attribution, bounded-context failure boundary와 provider-visible evidence consistency를 재검토합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
---

# PR #245 Current-Head Review

> [!IMPORTANT]
> **Blocked** — 기존 F1/F2 보정으로 utility evaluation의 방향과 검증 범위는 크게 개선됐지만, 동일 case attribution이 실제 review input identity까지 닫히지 않았고 bounded context 경계에서 typed failure를 우회하는 예외 및 provider-visible evidence 불일치가 남아 있습니다. F1–F3를 해소하기 전에는 현재 `compared / accept` evidence를 merge-ready utility proof로 승격하지 않는 것이 안전합니다.

- **Target** — [PR #245 · `feat(review-ai): prove MVP utility evaluation`](https://github.com/mols3131d/hmda-data-reliability/pull/245)
- **Revision** — base `2a793f4c23745abd485f26b15421b17c744760fa`, reviewed head `aaf9743d2adf8b654743bc3609fa248cc0a797c7`
- **Scope** — utility comparison의 same-case attribution, bounded review context의 preflight failure behavior, provider-visible evidence reference 일관성, PR evidence metadata와 현재 CI state를 검토했습니다. Live provider/Ollama utility와 실제 human evaluation은 재실행하지 않았습니다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 **Major** | `same case` 비교가 incident/column/deterministic facts에는 묶이지만 실제 review input 또는 controlled-variable identity에는 묶이지 않습니다. | baseline/candidate가 같은 representative case를 평가했다는 사실을 durable identity로 검증하고, 의도적으로 변경한 변수만 별도로 명시합니다. |
| F2 | 🟠 **Major** | 유효한 `AgenticReviewInput`이 bounded context 크기 제한을 넘으면 typed rejection 대신 `ValueError`가 service 밖으로 전파될 수 있습니다. | context overflow를 전용 typed preflight failure로 변환하고 service-level boundary test를 추가합니다. |
| F3 | 🟠 **Major** | bounded selection에서 제외된 evidence ID가 `draft.evidence_refs`를 통해 provider prompt에는 보이지만 validator에서는 fabricated evidence로 처리될 수 있습니다. | provider-visible draft reference를 bounded evidence set과 정합하게 투영하고 `> max_evidence` 통합 테스트를 추가합니다. |
| F4 | 🟡 **Minor** | PR description의 `revision.head`가 실제 reviewed head보다 오래된 `1c9ea4f...`를 가리킵니다. | PR body를 갱신할 때 `revision.head`도 현재 설명 기준 revision으로 함께 갱신합니다. |

## Details

### F1 · Same-Case Attribution Stops Before Review Input Identity

🟠 **Major**

#### Locations

- [`src/hmda_reliability/review_ai/evaluation.py`](../../src/hmda_reliability/review_ai/evaluation.py)
  - `HumanUtilityEvaluation`
  - `UtilityProofCase`
  - `compare_utility_evaluations`
- [`scripts/run_review_ai_utility_proof.py`](../../scripts/run_review_ai_utility_proof.py)
  - `build_representative_utility_proof`
- [`inbox/github-245-review-ai-utility-evaluation/03-review-review-ai-utility-proof-semantics.md`](03-review-review-ai-utility-proof-semantics.md)
  - `F2 — Same-case Binding Is Incomplete`

#### Evidence

현재 comparison은 baseline/candidate의 `case_id`, `case_version`, `rubric_id`, `project_revision`, `incident_id`, `target_column`, `deterministic_facts`와 quality-basis revision을 검사합니다. 이 보정으로 이전 F2의 핵심 false comparison 경로는 상당 부분 닫혔습니다.

하지만 `HumanUtilityEvaluation` 자체에는 실제 provider가 검토한 `RemediationDraft`, bounded context 또는 canonical review input을 식별하는 digest가 없습니다. `UtilityProofCase.input_digest`도 현재 runner에서 전체 review input digest가 아니라 `BoundedReviewContext.digest`로 채워집니다. 따라서 같은 case label과 deterministic facts를 유지한 채 draft 또는 다른 review input 요소가 달라도 comparison contract만으로는 이를 구분할 수 없습니다.

이전 semantics review는 F2 해소 조건으로 deterministic output identity뿐 아니라 canonical input 또는 case digest를 함께 검증하도록 제안했습니다. 현재 구현은 앞부분은 반영했지만 후반의 attribution identity는 아직 남아 있습니다.

#### Impact

baseline과 candidate의 점수 차이를 `change_under_test`의 효과로 해석하려면 비교 대상이 같은 representative case이고, 의도적으로 변경한 변수 외의 입력이 고정되었다는 근거가 필요합니다. 현재 evidence는 이 전제를 완전히 재구성하지 못하므로, draft나 context 조건의 차이가 score delta에 섞여도 `COMPARED` 상태가 만들어질 수 있습니다.

이는 일반 runtime correctness보다는 Utility Proof의 attribution 신뢰성 문제입니다. create-only 저장과 output digest integrity가 정상이어도 비교 원인이 잘못 귀속되면 durable evidence의 의미가 약해집니다.

#### Action

baseline/candidate evaluation을 representative case의 stable input identity에 연결합니다. 단순히 canonical input 전체가 항상 동일해야 한다고 고정하기보다 다음을 분리하는 편이 안전합니다.

- incident와 deterministic source case를 식별하는 stable case/input identity
- baseline과 candidate 사이에서 의도적으로 바뀌는 controlled variable
- 나머지 review input이 동일하다는 검증 가능한 binding

그리고 draft 또는 고정되어야 할 input 요소가 달라진 경우 comparison이 `blocked` 또는 `inconclusive`로 끝나는 negative test를 추가합니다.

### F2 · Bounded Context Overflow Escapes the Typed Failure Contract

🟠 **Major**

#### Locations

- [`src/hmda_reliability/review_ai/context.py`](../../src/hmda_reliability/review_ai/context.py)
  - `BoundedReviewEvidence`
  - `build_bounded_review_context`
- [`src/hmda_reliability/review_ai/prompt.py`](../../src/hmda_reliability/review_ai/prompt.py)
  - `render_review_prompt`
  - `PromptTooLargeError`
- [`src/hmda_reliability/review_ai/service.py`](../../src/hmda_reliability/review_ai/service.py)
  - `review_null_spike`
- [`tests/review_ai/test_context.py`](../../tests/review_ai/test_context.py)
  - `test_context_is_bounded_and_replayable`
- [`tests/review_ai/test_service.py`](../../tests/review_ai/test_service.py)
  - preflight rejection coverage

#### Evidence

`AgenticReviewInput`은 최대 64개 Evidence를 허용하고, bounded context builder는 기본적으로 최대 8개를 선택합니다. 각 selected evidence는 summary와 bounded facts를 포함할 수 있으며, 완성된 context가 기본 `max_context_bytes=16_384`를 넘으면 `build_bounded_review_context()`가 일반 `ValueError("bounded review context exceeds max_context_bytes")`를 발생시킵니다.

`render_review_prompt()`는 이 builder를 직접 호출하지만 context overflow를 `PromptTooLargeError` 같은 service-facing typed error로 변환하지 않습니다. `review_null_spike()`의 preflight 경계는 `PromptTooLargeError`만 잡으므로 context overflow `ValueError`는 `AgenticReviewResult(status="input_rejected", ...)`로 정규화되지 않고 호출자까지 전파될 수 있습니다.

현재 context unit test는 작은 `max_context_bytes`에서 정상적으로 bound 안에 들어오는 경우를 검증하지만, service가 실제 default context limit을 넘는 유효 입력을 typed failure로 처리하는 negative path는 확인되지 않습니다.

#### Impact

Review service는 provider 호출 전 입력·프롬프트 문제를 typed result로 닫는 계약을 갖습니다. 이 경로가 일반 예외로 빠지면 호출자는 동일한 preflight 실패를 `AgenticReviewResult`로 일관되게 처리할 수 없고, orchestration이나 API boundary에서 예상하지 않은 crash로 노출될 수 있습니다.

#### Action

context overflow를 좁은 전용 예외로 표현하고 `render_review_prompt()` 또는 service preflight에서 typed rejection으로 변환합니다. 이후 실제 default bound를 넘는 유효 `AgenticReviewInput`을 구성해 다음을 검증하는 service-level test를 추가합니다.

- provider가 호출되지 않음
- evidence store가 호출되지 않음
- 예외가 밖으로 전파되지 않음
- stable failure code를 가진 `INPUT_REJECTED` 결과가 반환됨

### F3 · Provider-Visible Draft References Exceed the Allowed Evidence Set

🟠 **Major**

#### Locations

- [`src/hmda_reliability/review_ai/contracts.py`](../../src/hmda_reliability/review_ai/contracts.py)
  - `AgenticReviewInput._validate_review_input`
- [`src/hmda_reliability/review_ai/context.py`](../../src/hmda_reliability/review_ai/context.py)
  - `build_bounded_review_context`
- [`src/hmda_reliability/review_ai/prompt.py`](../../src/hmda_reliability/review_ai/prompt.py)
  - `build_canonical_input`
- [`src/hmda_reliability/review_ai/service.py`](../../src/hmda_reliability/review_ai/service.py)
  - bounded `allowed_evidence_ids`
- [`tests/review_ai/test_prompt_provider.py`](../../tests/review_ai/test_prompt_provider.py)
  - provider projection coverage
- [`tests/review_ai/test_validator.py`](../../tests/review_ai/test_validator.py)
  - fabricated evidence coverage

#### Evidence

`AgenticReviewInput`은 incident와 draft의 `evidence_refs`가 제공된 전체 Evidence ID set과 일치하도록 검증합니다. 반면 bounded context는 기본 최대 8개 Evidence만 selected set에 남깁니다.

`build_canonical_input()`은 prompt의 `evidence` 목록에는 selected evidence만 넣지만 `draft` projection의 `evidence_refs`는 원본 `RemediationDraft` 값을 그대로 포함합니다. 따라서 입력 Evidence가 8개를 초과하면 provider는 bounded `evidence` 목록에는 없는 ID를 `draft.evidence_refs`에서 볼 수 있습니다.

service validator는 의도적으로 `allowed_evidence_ids`를 bounded context의 selected evidence ID로 제한합니다. 결과적으로 provider가 prompt에서 실제로 본 omitted ID를 `evidence_used`, finding 또는 utility contribution에 참조하면 `fabricated_evidence`로 거절될 수 있습니다.

#### Impact

fabricated evidence guard 자체는 올바른 방향이지만, 현재 prompt와 validator가 서로 다른 "provider가 사용할 수 있는 evidence ID" 집합을 암묵적으로 전달합니다. 이는 모델이 prompt에 명시된 ID를 사용했음에도 deterministic guard에 의해 실패하는 false rejection을 만들 수 있고, live utility 평가에서 불필요한 validation failure로 이어질 수 있습니다.

#### Action

provider-visible canonical draft의 `evidence_refs`도 bounded selected set과 정합하게 투영하거나, omitted reference는 직접 인용 가능한 evidence가 아님을 구조적으로 분리합니다. `max_evidence`를 초과하는 입력으로 prompt-visible ID set과 validator allowed set이 일치하는지 검증하는 integration test를 추가합니다.

### F4 · PR Revision Metadata Is Stale

🟡 **Minor**

#### Locations

- [PR #245 description](https://github.com/mols3131d/hmda-data-reliability/pull/245)
  - trailing `revision` metadata
- [`.github/templates/README.md`](../../.github/templates/README.md)
  - `revision` metadata guidance

#### Evidence

review 시작 시점의 live PR head는 `aaf9743d2adf8b654743bc3609fa248cc0a797c7`이지만 PR description의 `revision.head`는 `1c9ea4fccfe8ff6f9a5c2332beb9f1b9c324a820`으로 남아 있습니다. Repository template guidance는 PR description을 갱신한 뒤 base 또는 head가 바뀌었다면 `revision`도 함께 갱신하도록 요구합니다.

#### Impact

실제 code behavior에는 영향을 주지 않지만, 이 PR은 revision-bound evidence와 replayability를 핵심 주제로 다루므로 stale metadata가 있으면 어떤 revision을 설명·검증한 본문인지 판단 비용이 커집니다.

#### Action

다음 PR description 갱신 시 body가 설명하는 exact base/head pair로 `revision` metadata를 함께 갱신합니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Reviewed revision | Review 시작 시 live PR base/head가 `2a793f4c23745abd485f26b15421b17c744760fa` / `aaf9743d2adf8b654743bc3609fa248cc0a797c7`임을 확인했습니다. |
| ✅ Pass | Current CI | [CI Lite run 35450897153](https://github.com/mols3131d/hmda-data-reliability/actions/runs/35450897153)은 성공했고 selected Review AI/utility proof tests `311 passed`, OpenSpec validation, build, Ruff/format/type, dependency checks가 통과했습니다. |
| ✅ Pass | F1 contract cross-check | comparison model, proof runner와 이전 same-case review 요구를 대조해 현재 durable input binding의 범위를 확인했습니다. |
| ✅ Pass | F2/F3 static path analysis | context builder → prompt → service validator 경로를 따라 예외 전파와 provider-visible/allowed evidence set 불일치가 도달 가능한지 확인했습니다. |
| ⚪ Not Verified | F2/F3 focused runtime reproduction | 이번 review에서는 해당 boundary case를 pytest 또는 별도 reproduction으로 직접 실행하지 않았습니다. Finding은 current code path와 contract에 근거한 static review입니다. |
| ⚪ Not Verified | Live provider utility | 실제 Ollama/provider invocation과 human utility evaluation은 이번 review에서 재실행하지 않았습니다. |
| ⚪ Not Verified | Independent dual-perspective review | 현재 ChatGPT runtime에서는 repository의 `review-lead` subagent orchestration을 사용할 수 없어 이번 review를 formal independent dual-perspective review와 동등하게 취급하지 않습니다. |

## Risks and Limits

- F1은 일반 runtime correctness가 아니라 Utility Proof attribution의 evidence gap입니다. 향후 proof contract가 controlled-variable identity를 명시적으로 정의하면 그 canonical contract를 기준으로 재평가해야 합니다.
- F2와 F3는 code path로 확인한 reachable risk이지만 이번 review에서 focused reproduction을 실행하지 않았습니다. 수정 시 negative test로 재현과 해소를 함께 고정하는 것이 필요합니다.
- 이 artifact는 reviewed head `aaf9743d2adf8b654743bc3609fa248cc0a797c7`에 대한 fresh review입니다. 이후 implementation, spec 또는 proof runner가 실질적으로 변경되면 영향을 받는 finding을 다시 검증해야 합니다.
