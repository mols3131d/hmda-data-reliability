---
type: review
title: Langfuse Deep Self Review
description: PR #248의 Langfuse projection 구현, 검증 경계와 문서 계약을 최신 로컬 head에서 심층 점검한다.
---

# Langfuse Deep Self Review

> [!IMPORTANT]
> **Revise** — annotation completeness helper가 잘못된 rubric과 output digest를 가진 snapshot도 complete로 판정하는 Minor finding을 확인했다. 이 helper의 결과를 신뢰 가능한 completeness 신호로 쓰기 전에 `rubric_v1`과 실제 structured output digest를 검증해야 한다.

- **Target** — [PR #248](https://github.com/mols3131d/hmda-data-reliability/pull/248)
- **Revision** — base `1d7e5c70baa03540644e0dac71b740330f3e58cb`, reviewed local HEAD `44d424356d9a27870f6e9c8c1966abcf7edc86a8`
- **Scope** — PR diff의 projection module, live harness, tests, OpenSpec delta, architecture/domain/testing guide와 optional dependency/configuration. 현재 원격 PR state는 이 세션에서 조회되지 않았다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟡 Minor | `annotation_complete()`가 target을 metadata와 비교할 뿐 fixed rubric 및 digest-to-output 관계를 확인하지 않아 malformed annotation snapshot을 complete로 반환한다. | `rubric_v1`을 요구하고 structured output에서 digest를 다시 계산해 일치할 때만 complete로 판정한다. |

## Details

### F1 · Annotation completeness does not verify the exact rubric and output

🟡 Minor

#### Locations

- [`langfuse_projection.py`](../../src/hmda_reliability/review_ai/langfuse_projection.py#L125)
  - `annotation_complete`
- [`evaluation.py`](../../src/hmda_reliability/review_ai/evaluation.py#L77)
  - `HumanUtilityEvaluation._validate_evaluation`
- [OpenSpec delta](../../openspec/changes/review-ai-langfuse-projection/specs/reliability-agentic-review/spec.md#L47)
  - `Integration-local human annotation mapping`

#### Evidence

`project_invocation()`은 accepted output에서 `utility_output_digest()`를 계산하고 `RUBRIC_V1.rubric_id`를 기록한다. 그러나 `annotation_complete()`는 snapshot의 `metadata.status`와 호출자가 넘긴 `target`이 snapshot metadata와 같은지만 확인한 뒤 score들을 검증한다. Metadata의 rubric이 `rubric_v1`인지, digest가 SHA-256 형식인지, digest가 snapshot의 structured output을 실제로 가리키는지는 확인하지 않는다. 반면 canonical `HumanUtilityEvaluation`은 output digest를 다시 계산해 output과 일치시킨다.

최소 runtime 재현에서 `status="accepted"`, `output_digest="not-a-sha256-output-digest"`, `rubric_id="rubric_v999"`인 metadata와 그 값에 맞춘 target, 다섯 개의 유효한 score를 넘기자 함수가 `True`를 반환했다. 이 snapshot에는 output도 없었다.

#### Impact

잘못된 rubric 또는 변경·누락된 output을 대상으로 만든 점수도 repository helper에서 complete로 표시될 수 있다. 이 boolean을 annotation completeness 증거로 사용하는 사람이나 자동화가 잘못된 평가 대상을 받아들일 수 있다. Helper가 evaluation을 저장하거나 import하지 않으므로 현재 Review AI 결과와 승인 권한에는 영향을 주지 않는다.

#### Action

Accepted snapshot의 output을 `AgenticReviewOutput`으로 검증하고 `utility_output_digest()` 결과가 metadata의 digest와 일치하는지 확인한다. `rubric_id`도 `RUBRIC_V1.rubric_id`와 같아야 complete를 반환하도록 한다. malformed/missing output, digest 또는 metadata는 `False`로 처리한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ❌ Fail | Annotation snapshot boundary reproduction | `UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync python`으로 잘못된 rubric/digest와 일치하는 target을 전달했을 때 `annotation_complete(...)`가 `True`를 반환했다. |
| ✅ Pass | Diff hygiene at reviewed head | `git diff --check 1d7e5c70baa03540644e0dac71b740330f3e58cb...HEAD`가 오류 없이 끝났다. |
| ✅ Pass | Reviewed source identity | Projection module, projection tests, live harness의 SHA-256이 이전 [독립 구현 리뷰](03-review-review-ai-langfuse-local.md)에 기록된 값과 일치한다. |
| ✅ Pass | Review artifact contract and Markdown | `python3 scripts/validate_inbox_artifacts.py`와 `UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync rumdl check`가 이 보고서에서 통과했다. |
| ⚪ Not Verified | Current remote PR/CI state | `gh pr view 248`에서 `api.github.com` 연결 오류가 발생했다. 로컬 tracking ref는 reviewed HEAD와 같지만 원격 상태를 새로 조회하지 못했다. 기존 구현·문서 validation evidence는 [local validation report](02-report-review-ai-langfuse-local-validation.md)에 보존되어 있다. |

## Risks and Limits

이 보고서는 요청된 self-review이며 독립 리뷰나 PR approval이 아니다. 앞선 독립 리뷰는 동일 구현 파일 hash에서 clear였으나 F1을 포착하지 못했다. 본 보고서는 그 completeness 경계에 대한 추가 finding으로 앞선 판정을 보완한다. 실제 Langfuse ingestion과 human annotation은 endpoint/project가 없는 기존 범위와 같이 검증하지 않았다.
