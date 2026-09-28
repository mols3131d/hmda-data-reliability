---
type: review
title: PR 251 Adversarial Review
description: PR #251의 evaluation subdomain refactor를 failure path, false green, evidence freshness와 hidden assumption 관점에서 적대적으로 검토한다.
tags:
  - domain:review-ai
  - adversarial-review
---

# PR 251 Adversarial Review

> [!IMPORTANT]
> **Pass with one note** — challenge-first 적대적 리뷰에서 새 material runtime, serialization 또는 test defect는 확인하지 못했다. PR 본문의 current-head 표기가 실제 GitHub state보다 뒤처진 문제만 `🔵 Note`로 남긴다. 이는 human-review readiness 전에 정리할 evidence housekeeping이며 code/test correctness finding은 아니다.

- **Target** — [PR #251](https://github.com/mols3131d/hmda-data-reliability/pull/251) 전체 변경 중 Review Value evaluation, Langfuse child boundary, 관련 tests와 review evidence
- **Revision** — base `5532dca2fd93696d40ba870471fa2359c5662335`; review state capture head `a6a4c37367015a3b6cf9c5d153c09f9f53c62ac4`. Executable source/test는 `724580a7f1c051acb9f2a5ed3c43a00a947b4b59` 이후 변경되지 않았고, 그 뒤 현재 capture까지 변경은 Inbox와 OpenSpec Markdown뿐이다.
- **Scope** — Python API/wire compatibility, fail-closed comparison, Langfuse subprocess isolation과 failure handling, test false-green 가능성, validation evidence freshness, 과잉 finding 여부

이 문서는 **적대적 리뷰를 수행한 결과**다. 정상 경로를 재확인하는 대신 숨은 전제, 신뢰 경계, stale evidence, false-green과 기존 safeguard가 놓칠 수 있는 failure path를 우선 공격했다. 다만 이 채팅 runtime에서 별도 `review-lead`와 격리된 specialist context를 새로 실행한 것은 아니므로, 이 결과를 fresh independent dual-perspective review나 GitHub approval로 표현하지 않는다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🔵 Note | PR 본문은 `ebcdc420...`을 `Current PR head`로 적지만 review state capture head는 `a6a4c373...`였고 그 head의 CI Lite #1106도 성공했다. | Ready/human review 진입 직전에 PR body의 current head와 current CI를 실제 state로 갱신한다. Code/test 변경은 필요 없다. |

### F1 · Review Evidence Freshness

#### Locations

- [PR #251 description](https://github.com/mols3131d/hmda-data-reliability/pull/251)
  - `Validation`의 `Current PR head`
  - 마지막 `revision.head`
- [CI Lite #1106](https://github.com/mols3131d/hmda-data-reliability/actions/runs/36454147966)

#### Evidence

Review state를 캡처했을 때 GitHub의 실제 PR head는 `a6a4c37367015a3b6cf9c5d153c09f9f53c62ac4`였지만 본문은 `ebcdc4204ef8225df88dcb86719ead736c88ceaf`을 current head로 유지했다. `a6a4c373...`의 CI Lite #1106은 prospective merge checkout, Markdown/Inbox/OpenSpec validation, dependency boundary, package build, Python validation과 selected tests를 포함해 성공했다.

Source review continuity는 별개로 유지된다. `724580a7...` 이후 `a6a4c373...`까지 `src/**`와 `tests/**` 변경은 없으며 후속 delta는 Inbox와 OpenSpec Markdown이다. 따라서 stale body는 이전 source-review verdict를 자동으로 무효화하는 runtime defect 근거가 아니다.

이 09 artifact를 publication하면 PR head는 review state capture 이후 다시 이동한다. 따라서 이 문서가 특정 publication head를 다시 `current`라고 고정하지 않고, Ready 전환 직전 live GitHub state를 PR body가 소유하도록 남긴다.

#### Impact

사람이 PR 본문만 읽으면 최신 publication revision과 current CI attribution을 잘못 이해할 수 있다. 그러나 executable source/test가 바뀐 것은 아니므로 이를 correctness defect나 merge blocker로 확대하면 과잉 리뷰가 된다.

#### Action

Human review 또는 Ready 전환 직전에 PR body의 current revision과 CI 링크만 최신 state로 갱신한다. Historical source review, full-suite와 current publication evidence는 revision별로 계속 분리한다.

## Rejected Hypotheses

적대적 리뷰에서 plausible한 failure 가설을 먼저 만들고 baseline, typed boundary, existing tests와 recorded evidence로 다시 공격했다. 아래 후보는 실제 개선 아이디어일 수 있지만 #251의 current-required finding으로 승격하면 과도하다고 판단했다.

| Candidate | Attack | Re-check | Disposition |
| --- | --- | --- | --- |
| Golden baseline provenance | Golden fixture가 PR base와 다른 history에서 만들어져 잘못된 wire contract를 고정할 수 있다. | Fixture는 pre-refactor `6e64cc7`에서 캡처됐고 #248 squash base `5532dca2`는 같은 repository tree를 가진다. [Completion evidence](01-report-review-ai-evaluation-subdomain-completion.md)는 historical source에서 current model과 독립적으로 golden을 만든 과정과 mutation 검출을 기록한다. | **Rejected.** 현재 serialization oracle의 provenance를 무효화할 근거가 없다. |
| Deterministic-fact equality | Python equality의 type coercion 때문에 다른 facts가 same-case comparison을 통과할 수 있다. | `AgenticReviewOutput.deterministic_facts`는 raw dict가 아니라 typed `NullSpikeFacts` model을 통과하고, comparison model은 output digest와 deterministic facts를 함께 검증한다. | **Rejected for this change.** 도달 가능한 PR-specific regression path를 확인하지 못했다. |
| Child `python -m` relocation | Mocked subprocess argv만 맞고 실제 새 module entrypoint는 실행되지 않을 수 있다. | Maintained test는 새 module argv와 importability를 고정하고, [Completion evidence](01-report-review-ai-evaluation-subdomain-completion.md)는 exact reviewed source에서 malformed input으로 실제 `python -m hmda_reliability.review_ai.evaluation.langfuse` 실행 probe를 기록한다. | **Optional hardening.** Maintained component execution test 추가는 가치가 있지만 현재 blocker는 아니다. |
| Langfuse SDK skip means false green | CI의 `1 skipped` 때문에 optional adapter 전체가 검증된 것처럼 보일 수 있다. | Skip은 dependency 부재로 명시돼 있고 [CI skip trade-off report](08-report-review-ai-langfuse-ci-skip-tradeoffs.md)가 검증 범위와 선택지를 분리한다. Source review와 PR body도 remote ingestion을 검증했다고 주장하지 않는다. | **Known limit, not a defect.** SDK 집중 CI는 별도 개선 후보다. |
| Extra defensive tests | non-ASCII digest, child env exact key set, ordinary non-zero child return code를 모두 새 테스트로 요구할 수 있다. | 해당 behavior와 test gap은 대부분 base에도 존재했고 #251은 owner/path와 public Python naming을 주로 바꾼다. [Test design review](07-review-review-ai-evaluation-test-design.md)도 이를 inherited debt 또는 optional hardening으로 분류했다. | **Rejected as PR-required work.** 별도 risk-driven test improvement로 분리한다. |

## Method

보고서 자체가 finding을 부풀리는 방향으로 고착되지 않도록 두 번의 substantive improvement loop를 사용했다.

1. **Research → Challenge → Review** — live PR state, base/head continuity, source/test diff, canonical Spec, 기존 review와 CI evidence를 다시 조사했다. 공격 가설을 만들고 실제 reachability, baseline과 safeguard를 확인해 살아남지 못한 가설을 제거했다.
1. **Reframe → Draft → Adversarial Review** — 첫 판단에서 stale PR body를 material finding으로 과대평가한 부분을 다시 검토했다. Executable delta가 없고 current-head CI도 성공했다는 근거를 반영해 `🔵 Note`로 낮추고, optional hardening과 inherited debt를 current-required finding에서 분리했다.

두 번째 review에서 추가 조사가 결론을 바꿀 가능성이 낮아졌으므로 loop를 종료했다. Finding 개수를 늘리는 대신 실제 영향과 evidence attribution을 우선했다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Live PR state capture | Review 시점 PR은 open Draft, base `5532dca2...`, head `a6a4c373...`, mergeable 상태였다. |
| ✅ Pass | Executable source continuity | `724580a7...` → `a6a4c373...` 비교에서 변경은 Inbox와 OpenSpec Markdown뿐이며 `src/**`, `tests/**` delta는 없다. |
| ✅ Pass | Current-head CI before publication | CI Lite [#1106](https://github.com/mols3131d/hmda-data-reliability/actions/runs/36454147966)은 `a6a4c373...` prospective merge에서 성공했다. Markdown/Inbox/OpenSpec validation, dependency boundary, package build, Python validation과 selected tests가 모두 성공했다. |
| ✅ Pass | Adversarial attack-surface review | `evaluation/value.py`, `evaluation/langfuse.py`, public API/tests, canonical Review AI Spec과 existing review evidence를 failure path, compatibility와 false-green 관점에서 교차 검토했다. |
| ✅ Pass | Over-review audit | Golden provenance, typed deterministic facts, child entrypoint, optional SDK skip과 defensive-test 후보를 baseline·reachability·existing safeguard와 대조해 current-required finding 여부를 다시 판정했다. |
| ⚪ Not Verified | Fresh independent specialist orchestration | 이 채팅 runtime에서 별도 `review-lead`가 quality/adversarial specialist를 격리 실행한 fresh review는 수행하지 않았다. 같은 context의 challenge-first pass를 독립 검토라고 부르지 않는다. |
| ⚪ Not Verified | Broader runtime proof | Current publication head full suite, 외부 Python consumer/wheel install runtime, 실제 Langfuse ingestion/UI와 human utility evaluation은 새로 검증하지 않았다. |

## Risks and Limits

- 이 artifact의 publication commit은 review state capture 뒤 PR head를 이동시킨다. Publication commit이 이 파일만 추가한다면 executable verdict 범위는 확대하지 않지만, publication-head Markdown/Inbox validation은 해당 head의 CI가 별도로 소유한다.
- PR body의 revision freshness는 source correctness와 별개다. 이를 이유로 새 code/test work를 만드는 것은 권장하지 않는다.
- 이후 `src/**`, `tests/**` 또는 canonical evaluation/Langfuse contract가 materially 변경되면 이 adversarial verdict를 재사용하지 않고 affected attack surface를 다시 검토해야 한다.
- 이 review는 Ready 전환, GitHub approval 또는 merge authority를 부여하지 않는다.
