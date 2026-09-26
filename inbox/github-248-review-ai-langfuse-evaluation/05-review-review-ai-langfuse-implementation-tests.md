---
type: review
title: Langfuse Implementation and Test Review
description: PR #248의 projection 구현, annotation target과 테스트 oracle을 exact head에서 독립 검토한다.
---

# Langfuse Implementation and Test Review

> [!IMPORTANT]
> **Revise** — 두 가지 material finding을 확인했다. Annotation helper가 잘못된 output/rubric을 complete로 판정할 수 있고, Langfuse SDK가 허용된 output을 media reference로 바꿔 digest 대상과 다른 값을 기록할 수 있다. 두 경로의 회귀 테스트를 추가하고 구현 경계를 보완해야 한다.

- **Target** — [PR #248](https://github.com/mols3131d/hmda-data-reliability/pull/248)
- **Revision** — base `1d7e5c70baa03540644e0dac71b740330f3e58cb`, head `397a03dd5c36d4a1b2e2ecdca0d32691a850fa80`
- **Scope** — `langfuse_projection.py`, live harness, projection/harness tests 및 선택 Langfuse 4.15.6 integration의 OpenSpec contract. Tests와 runtime behavior를 대조했고 source나 test는 수정하지 않았다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟡 Minor | `annotation_complete()`가 payload의 metadata와 target이 서로 일치하기만 하면 output과 `rubric_v1`의 실제 결합을 검증하지 않는다. | 고정 rubric을 요구하고 structured output digest를 재계산해 일치 여부를 확인한다. |
| F2 | 🟠 Major | Langfuse 4.15.6이 `data:*;base64,...` output을 media object/reference로 바꿀 수 있어 observation의 output이 계산된 digest와 달라진다. | Child에서 SDK media conversion/upload를 비활성화하고 SDK 처리 이후에도 exact output이 유지되는 회귀 검증을 추가한다. |

## Details

### F1 · Annotation completeness trusts matching metadata instead of the exact output

🟡 Minor

#### F1 code locations

- [`langfuse_projection.py`](../../src/hmda_reliability/review_ai/langfuse_projection.py#L125)
  - `annotation_complete`
- [`evaluation.py`](../../src/hmda_reliability/review_ai/evaluation.py#L77)
  - `HumanUtilityEvaluation._validate_evaluation`
- [OpenSpec delta](../../openspec/changes/review-ai-langfuse-projection/specs/reliability-agentic-review/spec.md#L47)
  - `Integration-local human annotation mapping`

#### F1 behavioral evidence

`project_invocation()`은 `RUBRIC_V1.rubric_id`와 parsed output의 digest를 생성한다. 그러나 `annotation_complete()`는 전달된 target이 payload metadata와 같은지, score 5개가 schema에 맞는지만 검사한다. `payload.output`의 존재나 digest 일치를 확인하지 않고 metadata의 rubric 값도 고정하지 않는다. 실제로 valid score 다섯 개와 metadata에 맞춘 target을 주면 output을 바꾸거나 없애고, rubric을 `rubric_v2`로 바꾸거나 잘못된 digest를 넣어도 `True`가 나온다. 반면 canonical `HumanUtilityEvaluation`은 digest를 structured output에서 다시 계산한다.

영향은 integration-local completeness false positive로 제한된다. Evaluation을 저장·import하거나 human authorship를 판정하지는 않는다.

#### F1 impact

`invocation_id + output_digest + rubric_v1`에 결합해야 하는 annotation이 다른 output 또는 지원하지 않는 rubric을 대상으로 complete로 표시될 수 있다. 사람이 이 반환값을 annotation 완료 증거로 사용하면 잘못된 사례를 repository evaluation 후보로 취급할 수 있다.

#### F1 remediation

Accepted payload의 output을 `AgenticReviewOutput`으로 검증하고 `utility_output_digest()`를 다시 계산해 metadata와 비교한다. `rubric_id == RUBRIC_V1.rubric_id`를 요구하고 output 또는 metadata가 없거나 불일치하면 `False`를 반환한다.

### F2 · SDK media handling can rewrite the exact projected output

🟠 Major

#### F2 code and SDK locations

- [`langfuse_projection.py`](../../src/hmda_reliability/review_ai/langfuse_projection.py#L149)
  - child environment allowlist
- [`langfuse_projection.py`](../../src/hmda_reliability/review_ai/langfuse_projection.py#L200)
  - `_send_to_langfuse`
- [`contracts.py`](../../src/hmda_reliability/review_ai/contracts.py#L240)
  - `AgenticReviewOutput.review_summary`
- [OpenSpec delta](../../openspec/changes/review-ai-langfuse-projection/specs/reliability-agentic-review/spec.md#L19)
  - verified accepted output projection
- [Langfuse SDK 4.15.6 span processing](https://github.com/langfuse/langfuse-python/blob/v4.15.6/langfuse/_client/span.py#L151-L169)
- [Langfuse SDK 4.15.6 media handling](https://github.com/langfuse/langfuse-python/blob/v4.15.6/langfuse/_task_manager/media_manager.py#L45-L47)

#### F2 SDK evidence

Projection metadata digest는 `start_observation()`에 넘기기 전에 `AgenticReviewOutput`에서 계산한다. 그러나 pinned SDK는 observation의 input/output/metadata를 span attribute로 만들기 전에 media processing을 적용한다. SDK 4.15.6의 `MediaManager`는 `LANGFUSE_MEDIA_UPLOAD_ENABLED` 기본값을 `True`로 두고 `data:*;base64,...` 문자열을 `LangfuseMedia`로 바꾸며 upload queue에 넣는다. Serializer는 이를 media reference로 직렬화한다.

현재 child environment allowlist는 Langfuse key와 `PATH`/Windows startup 값만 전달하므로 `LANGFUSE_MEDIA_UPLOAD_ENABLED=false`가 parent에 설정되어도 child에는 전달되지 않는다. `review_summary`는 해당 문자열 형식을 거부하지 않고 non-empty string으로 허용한다. 따라서 accepted output에 base64 data URI가 들어오면 payload에 기록한 digest의 원문과 원격 observation output representation이 달라지고 별도 media upload도 시도될 수 있다.

#### F2 impact

사람이 Langfuse에서 보는 output은 digest가 식별하는 structured output과 다를 수 있다. Exact output에 대한 human score를 만들려는 목적에서 관찰 대상이 바뀌며, SDK가 별도 media upload side effect를 수행한다. 다른 일반 문자열 output 경로에서는 이 변환이 발생하지 않는다.

#### F2 remediation

Child를 만들 때 SDK media conversion/upload를 명시적으로 비활성화해 structured text를 그대로 유지한다. Pinned SDK 경로에서 data URI가 들어간 output을 관찰시켜 최종 serialized output이 원문과 같고 media upload가 enqueue되지 않는지 검증하는 테스트를 추가한다.

## Test Coverage Gaps

- `test_annotation_requires_exact_target_and_each_valid_score_once`는 정상 projection metadata에서 target을 만든 뒤 target 값만 틀리게 바꾼다. Payload metadata와 output을 조작한 wrong-rubric, fake-digest, changed-output, missing-output 사례를 확인하지 않아 F1을 놓친다.
- Projection equality test는 SDK 호출 전 payload만 비교한다. Child invocation은 mock되고 SDK failure 테스트도 double을 사용하므로 data URI를 pinned SDK의 observation path에 통과시킨 후 serialized output/digest를 대조하는 test는 없다. 따라서 F2는 현재 35개 focused tests가 모두 통과해도 검출되지 않는다.
- 기존 test의 강점으로는 실패 record의 field 최소화, parent timeout, sanitized failure status, core result/file 보존, score 범위·중복·rationale와 잘못된 target 검증이 있다. 전체 테스트 재작성은 필요하지 않으며 위 두 regression scenario가 핵심 누락이다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Independent quality + adversarial review | 두 관점 모두 exact base/head의 source, tests와 OpenSpec을 확인했고 review-lead가 두 finding을 current-required로 조정했다. |
| ✅ Pass | Focused projection and harness tests | `UV_CACHE_DIR=/tmp/uv-cache PYTHONDONTWRITEBYTECODE=1 uv run --no-sync pytest -p no:cacheprovider -q tests/review_ai/test_langfuse_projection.py tests/review_ai/test_live_harness.py`: 35 passed. |
| ✅ Pass | Annotation mismatch reproductions | Valid scores를 유지하고 metadata/output만 바꾼 경우에도 helper가 `True`를 반환하는 것을 독립 검토가 재현했다. |
| ✅ Pass | SDK source inspection | Langfuse `v4.15.6`의 span, media manager와 serializer를 확인했다. `data:` 변환 경로는 확인했지만 이 환경에 optional SDK가 없어 custom data-URI SDK runtime smoke는 실행하지 못했다. |
| ⚪ Not Verified | SDK runtime and remote destination | SDK를 설치한 isolated run, 실제 Langfuse ingestion/UI 및 human scoring은 실행하지 않았다. |
| ✅ Pass | Current PR CI | [CI Lite #1090](https://github.com/mols3131d/hmda-data-reliability/actions/runs/36254388936)이 reviewed head `397a03d`에서 성공했다. |

## Risks and Limits

이번 finding은 optional external projection 및 local completeness helper에 한정된다. Core review result, local provenance, recovery/approval 권한은 변경되지 않는다. Review-lead 확인과 test 실행 후 worktree는 clean이었다. 이 보고서는 독립 review evidence이며 approval이나 merge 결정을 대신하지 않는다.
