---
type: review
title: PR 251 Test Design Deep Review
description: PR #251의 evaluation/Langfuse refactor 테스트가 변경 위험을 적절히 검증하는지와 과잉 finding 여부를 검토한다.
tags:
  - domain:review-ai
  - testing
---

# PR 251 Test Design Deep Review

> [!IMPORTANT]
> **Pass** — reviewed executable revision `ebcdc4204ef8225df88dcb86719ead736c88ceaf`의 테스트 설계에서 PR #251 acceptance 전에 수정해야 할 material finding은 확인하지 못했다. 새 테스트는 이번 refactor가 만든 serialization, Python public surface와 child module relocation 위험을 직접 겨냥하고, 기존 Langfuse failure/isolation 테스트를 재사용한다. 초기 심층 검토에서 제기한 추가 테스트 후보는 base/head와 governing contract를 다시 대조한 결과 대부분 inherited test debt 또는 optional hardening으로 분류했으며 현재 PR의 required change로 채택하지 않는다.

- **Target** — [PR #251](https://github.com/mols3131d/hmda-data-reliability/pull/251)
- **Revision** — base `5532dca2fd93696d40ba870471fa2359c5662335`, reviewed executable head `ebcdc4204ef8225df88dcb86719ead736c88ceaf`; 이 review artifact publication 이후 PR head가 이동하더라도 source/test가 바뀌지 않은 Inbox-only commit에는 이 verdict의 executable scope를 확대하지 않는다.
- **Scope** — Review Value evaluation 계약, pre-refactor serialization/digest compatibility, Python public surface, Langfuse child module relocation과 기존 failure/isolation semantics를 검증하는 테스트의 scenario·oracle·level·false-green 위험

이 문서는 [merge-readiness review](06-review-review-ai-evaluation-subdomain-merge-readiness.md)를 대체하지 않는다. Merge readiness 전체가 아니라 테스트 설계와 과잉 finding 여부만 좁게 검토한다.

## Findings

확인된 material finding 없음.

## Review Method

Repository의 [Test Design](../../docs/development/test-design.md)이 요구하는 `Requirement → Observable Contract → Risk → Scenario → Independent Oracle → Test Level` 연결을 기준으로 시작했다. 단순 test count나 coverage가 아니라 production의 의미 있는 mutation이 현재 oracle을 통과할 수 있는지도 확인했다.

그 뒤 finding이 과도해지는 것을 막기 위해 각 후보를 다음 세 범주로 다시 분류했다.

- **PR-specific risk** — #251의 move/rename 때문에 새로 생긴 회귀 위험
- **Preservation risk** — 기존 behavior지만 이번 refactor가 보존한다고 명시해 현재 변경에서 다시 확인할 가치가 있는 위험
- **Inherited debt** — base revision에도 같은 테스트 공백이 있었고 #251이 해당 behavior를 실질적으로 바꾸지 않은 경우

Inherited debt나 일반적인 defensive hardening은 현재 변경의 observable regression 근거가 없으면 PR finding으로 승격하지 않았다.

## Test Design Assessment

| Risk | Current Evidence | Assessment |
| --- | --- | --- |
| Serialized comparison shape/value가 API rename 중 바뀜 | [`test_comparison_json_matches_pre_refactor_golden`](https://github.com/mols3131d/hmda-data-reliability/blob/ebcdc4204ef8225df88dcb86719ead736c88ceaf/tests/review_ai/test_utility_evaluation.py)은 pre-refactor `6e64cc7`에서 캡처한 static compared/blocked JSON 전체를 current model output과 비교한다. Fixture는 nested score/delta field, enum value, embedded output과 digest를 포함한다. | **Strong.** Current implementation으로 expected를 재생성하지 않아 oracle이 production implementation과 독립적이다. |
| Partial assertion이 nested wire rename을 놓침 | [Completion report](01-report-review-ai-evaluation-subdomain-completion.md)는 `baseline_score`/`candidate_score` rename mutation에서 기존 tests가 `15 passed`였지만 새 golden cases가 `4 failed`였음을 기록한다. | **Strong.** 실제 false-green mutation을 보강된 테스트가 검출했다는 직접 evidence가 있다. |
| Python API rename에서 old/new surface가 섞임 | [`test_review_value_api_exposes_only_intended_names`](https://github.com/mols3131d/hmda-data-reliability/blob/ebcdc4204ef8225df88dcb86719ead736c88ceaf/tests/review_ai/test_utility_evaluation.py)과 [`test_review_ai_exports_only_consumer_surface`](../../tests/review_ai/test_public_surface.py)가 evaluation package와 `review_ai` root의 curated export를 확인한다. | **Appropriate.** Alias 없는 pre-1.0 rename이라는 design decision에 맞는 가장 낮은 비용의 unit oracle이다. |
| Child process가 이전 module path를 계속 사용함 | [`test_child_receives_only_selected_environment_and_bounded_payload`](https://github.com/mols3131d/hmda-data-reliability/blob/ebcdc4204ef8225df88dcb86719ead736c88ceaf/tests/review_ai/test_langfuse_projection.py)이 spawned argv를 `python -m hmda_reliability.review_ai.evaluation.langfuse`로 고정하고 새 module path importability를 확인한다. | **Appropriate for relocation.** Path consumer 변경을 직접 검증한다. |
| 새 child module이 실제 executable entrypoint로 동작하지 않음 | Maintained test는 실제 새 module을 subprocess로 실행하지 않지만 [Completion report](01-report-review-ai-evaluation-subdomain-completion.md)는 exact reviewed source에서 malformed JSON을 새 `python -m` path에 전달해 exit `1`, 빈 stdout/stderr를 확인한 독립 probe를 기록한다. | **Sufficient for this refactor, not ideal regression coverage.** Reviewed executable revision의 실행 가능성은 직접 확인됐고 source의 `__main__` behavior는 base에서 기계적으로 이동했다. Maintained component probe는 future hardening이지 현재 blocker는 아니다. |
| Langfuse optional boundary가 relocation 중 약화됨 | Existing unit/component tests가 disabled no-spawn, bounded payload, selected environment, timeout, real stalled-child termination, media disable, harness result preservation과 SDK failure propagation을 계속 검증한다. | **Appropriate reuse.** 이 behavior는 #251에서 재설계하지 않고 owner/path만 이동하며 기존 scenario를 다시 구현할 이유가 없다. |
| Optional SDK behavior가 dependency 없이 항상 green | Pinned Langfuse media processor integration test는 SDK가 있을 때 실제 package behavior를 검증하고, reviewed executable-head CI는 dependency 부재를 `1 skipped`로 명시한다. Historical source validation에서는 Langfuse가 설치된 환경의 관련 suite도 통과했다. | **Transparent limit.** Skip을 pass처럼 해석하지 않고 별도 evidence 범위를 유지한다. |

## Over-Review Audit

초기 심층 검토에서 plausible해 보였던 후보를 다시 공격적으로 검토했다. 아래 항목은 실제 개선 아이디어일 수 있으나 현재 PR의 required finding으로 만들면 scope와 baseline을 과도하게 넓힌다고 판단했다.

| Candidate | Initial Concern | Re-check | Final Disposition |
| --- | --- | --- | --- |
| 실제 `python -m ...evaluation.langfuse` component test 추가 | `find_spec()`과 mocked argv는 `__main__` 실행을 증명하지 않는다. Python 3.13에서 이미 import된 module의 `find_spec()`은 `sys.modules[name].__spec__`을 반환한다. | Test task는 새 argv와 importable module assertion을 명시적으로 요구한다. 더 중요하게 exact reviewed source에는 실제 malformed-input `python -m` probe가 있다. Current `__main__` block은 base behavior의 이동이며 실행 의미 변경이 없다. | **Optional hardening.** 다음 entrypoint 변경에서 maintained component probe를 추가하면 좋지만 #251 blocker로 만들지 않는다. |
| non-ASCII historical digest vector 추가 | 현재 golden 문자열이 ASCII라 `ensure_ascii=False`가 제거돼도 대표 digest가 같을 수 있다. Python JSON default는 `ensure_ascii=True`다. | `_canonical_json_bytes()`의 `ensure_ascii=False`, separators, sort와 UTF-8 encoding은 base에서 head로 그대로 이동했다. 이번 task는 representative pre-refactor digest를 pin하는 것이며 character-domain 전체를 새로 검증하는 변경이 아니다. | **Optional hardening.** Digest algorithm 변경 작업이 생길 때 Unicode vector가 더 직접적인 regression test다. 현재 PR finding은 아니다. |
| `ReviewValueAssessment`의 duplicate/reordered criterion rejection 추가 | 현재 negative test는 4개 score로 줄여 `min_length`를 검증하므로 custom exact-order validator 제거를 잡지 못한다. | 같은 테스트와 validator가 base revision에도 존재하며 #251은 symbol/owner를 이동할 뿐 해당 invariant를 변경하지 않았다. | **Inherited test debt.** 별도 test-quality 개선 후보이며 #251 required change로 만들지 않는다. |
| Child environment exact key-set assertion | 현재 test는 `PROVIDER_API_KEY`, `OTEL_RESOURCE_ATTRIBUTES` 두 예시가 빠지는지만 확인해 exact allowlist mutation을 모두 잡지는 못한다. | Implementation과 test가 base에서 동일하고 #251은 environment policy를 바꾸지 않았다. | **Inherited test debt.** Isolation contract를 후속 강화할 수 있으나 relocation acceptance와 분리한다. |
| Child `returncode=1` → `export_failed` 직접 case | Exception과 timeout, returncode `0`은 검증하지만 ordinary non-zero `CompletedProcess` case가 없다. | Return-code mapping과 해당 test gap 모두 base부터 동일하다. #251의 child path move가 이 branch logic을 변경하지 않았다. | **Inherited test debt.** 별도 failure-boundary test improvement로 분리한다. |

외부 Python 3.13 문서도 두 counterfactual 자체는 사실임을 확인한다. [`importlib.util.find_spec()`](https://docs.python.org/3.13/library/importlib.html#importlib.util.find_spec)은 module이 `sys.modules`에 있으면 기존 `__spec__`을 반환하고, [`json.dumps()`](https://docs.python.org/3.13/library/json.html#json.dumps)는 `ensure_ascii=True`가 기본이다. 다만 counterfactual이 기술적으로 가능하다는 사실만으로 현재 PR의 material regression risk가 되는 것은 아니다. Base revision, changed surface와 explicit acceptance를 함께 봐야 한다.

## Why The Current Tests Are Proportionate

이번 PR의 핵심은 새로운 evaluation behavior를 설계하는 것이 아니라 owner/path와 Python symbol을 정리하면서 observable behavior를 보존하는 것이다. 따라서 가장 위험한 부분은 모든 기존 validator branch를 다시 테스트하는 것이 아니라 다음 세 가지다.

1. **Stored/wire evidence drift** — historical static golden과 mutation proof가 직접 보호한다.
1. **Consumer import drift** — evaluation/root public-surface test와 repository consumer migration이 보호한다.
1. **Executable child path drift** — spawned argv/import path test와 exact reviewed-source `python -m` probe가 보호한다.

이 세 경계 뒤의 rubric validation, Langfuse isolation과 failure behavior는 base에서 이미 테스트됐고 구현도 의미 변경 없이 이동했다. 해당 기존 테스트를 유지하면서 새 relocation/serialization regression oracle만 추가한 구성이 repository의 “가장 낮은 비용으로 contract를 신뢰성 있게 입증” 원칙에 더 가깝다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Governing test-design contract | [Test Design](../../docs/development/test-design.md), OpenSpec [design](../../openspec/changes/review-ai-evaluation-subdomain-refactor/design.md), [spec](../../openspec/changes/review-ai-evaluation-subdomain-refactor/specs/reliability-agentic-review/spec.md), [tasks](../../openspec/changes/review-ai-evaluation-subdomain-refactor/tasks.md)의 requirement, scenario, boundary와 requested test evidence를 대조했다. |
| ✅ Pass | Base/head test comparison | Base `5532dca2`와 reviewed executable head `ebcdc420`의 evaluation/Langfuse tests를 직접 대조해 새 coverage와 inherited gap을 분리했다. |
| ✅ Pass | Golden provenance and mutation evidence | Static fixture가 historical source에서 생성됐고 current implementation으로 expected를 만들지 않았으며 nested field rename mutation을 실제로 kill했다는 기록을 확인했다. |
| ✅ Pass | Child entrypoint evidence | Head test의 new module argv/import assertion과 completion report의 actual `python -m` malformed-input probe를 함께 확인했다. |
| ✅ Pass | Runtime semantic challenge | Python 3.13 공식 문서에서 `find_spec()`의 `sys.modules` behavior와 JSON `ensure_ascii` default를 확인해 초기 false-green 가설 자체를 검증한 뒤 PR materiality를 다시 판정했다. |
| ✅ Pass | Reviewed executable-head prospective merge CI | `ebcdc420`의 CI Lite #1103은 prospective merge에서 selected tests **186 passed, 1 skipped**, package build, dependency boundary와 Python/OpenSpec validation을 통과했다. |
| ⚪ Not Verified | Report-publication head CI | 이 review artifact를 추가하면서 PR head는 reviewed executable revision 이후의 Inbox-only commit으로 이동한다. Publication commit의 CI 결과를 `ebcdc420` source/test 검증 근거로 소급하지 않으며, report formatting/Inbox validation은 해당 publication-head CI가 별도로 소유한다. |
| ⚪ Not Verified | Fresh local mutation run | 이 review에서는 production source를 변형하거나 새 test를 실행하지 않았다. Mutation 판단은 recorded historical mutation evidence와 source-level counterfactual analysis에 한정한다. |
| ⚪ Not Verified | Reviewed executable-head full suite / remote Langfuse / human evaluation | PR body가 명시한 것처럼 `ebcdc420` full suite, 실제 Langfuse ingestion/UI와 human utility 평가는 이 review에서 새로 검증하지 않았다. |

## Risks and Limits

- Maintained suite에 실제 새 `python -m` child를 실행하는 component regression test가 없다는 점은 남는다. Reviewed executable revision의 직접 probe와 unchanged behavior가 있어 merge blocker로 보지 않지만, child entrypoint를 다시 수정하는 change에서는 component test를 primary evidence로 승격하는 편이 낫다.
- Historical golden은 현재 representative ASCII fixture에 대해 매우 강하지만 canonical digest의 가능한 모든 문자열 domain을 exhaustive하게 증명하지 않는다. Digest algorithm 자체를 변경할 때는 non-ASCII vector를 추가하는 것이 합리적이다.
- Assessment exact-order, exact environment allowlist, ordinary child non-zero exit 같은 inherited test-quality 개선은 현재 PR의 required change와 분리해야 한다. 별도 작업으로 다룰 때에도 실제 risk와 expected information gain을 기준으로 우선순위를 정한다.
- Source/test 또는 evaluation/Langfuse normative contract가 다시 materially 변경되면 이 verdict를 재사용하지 않고 affected risk와 oracle을 다시 검토해야 한다.
