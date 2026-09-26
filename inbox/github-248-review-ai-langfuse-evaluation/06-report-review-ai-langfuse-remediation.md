---
type: report
title: Langfuse Review Findings Remediation
description: PR 248의 annotation target 및 SDK output 변환 finding 수정과 독립 검토, 로컬 검증 결과를 기록한다.
---

# Langfuse Review Findings Remediation

2026-09-27 KST. 이 보고서는 PR #248의 리뷰 finding F1/F2 remediation을 기록한다. 구현은 parent `0c0ff02a384943d60810997e5404ee6786564967`에서 시작해 code head `521e44e90fd535ddb7ca4671b5d117f5e4f9a346`에 반영했다. 구현 계약과 완료 task는 [OpenSpec Change](../../openspec/changes/review-ai-langfuse-projection/tasks.md)가 소유한다.

## 수정 사항

- **F1 — annotation target completeness:** `annotation_complete()`가 accepted output을 `AgenticReviewOutput`으로 검증하고 정규 JSON value와 type을 모델 정규화 전후 비교한다. 이후 output digest, 고정 `rubric_v1`, invocation target, metadata 및 각 score를 함께 검증하며 누락·변형·불일치는 `False`로 처리한다. Pydantic이 `"0.01"`을 숫자로 강제 변환해 digest 불일치가 가려지던 추가 경로도 canonical JSON 비교로 막았다.
- **F2 — SDK media rewrite:** Langfuse child environment에서 `LANGFUSE_MEDIA_UPLOAD_ENABLED=false`를 강제한다. 상위 환경 변수가 `true`여도 data URI가 원문 output으로 남고 media upload queue가 사용되지 않는다. 기본 projection 테스트에 더해 pinned Langfuse 4.15.6 `MediaManager`를 통과하는 네트워크 없는 검증을 추가했다.
- OpenSpec delta와 testing guide 및 Review AI domain guide에 exact output/type 검증과 SDK media 처리 경계를 반영했다.

## 독립 검토

독립 `review-lead`가 정확한 code head `521e44e90fd535ddb7ca4671b5d117f5e4f9a346`을 검토했고 **`clear`**로 판정했다. F1의 wrong rubric, fake digest, changed/malformed output, Pydantic coercion과 malformed score 경로 및 F2의 parent 환경이 `true`인 경우를 테스트와 대조했다. 이 검토에서 추가 `current_required` 결함은 발견되지 않았다.

검토자가 기록한 후속 항목은 **`follow_up` · `acceptance_gap`**이다. 기본 CI의 locked 환경에는 optional `langfuse` extra가 없어 pinned SDK processor 테스트가 skip될 수 있다. child 환경값과 output digest를 확인하는 일반 테스트는 extra 없이도 실행되며, 이 remediation에서는 extra를 설치한 로컬 환경에서 SDK-specific test를 실제 실행했다. CI 전용 extra 추가 여부는 별도 후속 선택이다.

## 검증

| Check | Result | Evidence |
| --- | --- | --- |
| Test-first regressions | Pass | F1/F2 재현 테스트가 기존 동작에서 실패하는 것을 확인한 뒤 수정했다. 독립 검토가 찾은 문자열-to-number coercion 경로도 먼저 실패 테스트로 추가했다. |
| Projection and harness | Pass | `pytest tests/review_ai/test_langfuse_projection.py tests/review_ai/test_live_harness.py`: 44 passed. 선택 SDK extra가 설치된 상태에서 SDK processor test를 포함해 실행했다. |
| Review AI and Runtime AI | Pass | `pytest tests/review_ai tests/runtime_ai`: 182 passed. |
| Pinned SDK media processor | Pass | Langfuse 4.15.6 `MediaManager`에 data URI output을 전달하고 output 보존 및 빈 upload queue를 확인했다. 네트워크 전송은 하지 않았다. |
| Static and architecture checks | Pass | Ruff check/format, project-wide `ty check`, `tach check`, `git diff --check`. |
| Specs and docs | Pass | `openspec validate review-ai-langfuse-projection --strict`와 변경 Markdown `rumdl check`. |
| Independent review | Pass | `review-lead` exact-head assessment: `clear`; 추가 `current_required` 없음. |

## 남은 검증 경계

사용자 확인에 따라 실제 Langfuse endpoint/project 없이 로컬 구현과 검증만 진행했다. 따라서 실제 원격 ingestion, 배포 UI의 annotation 동작, 사람의 다섯 rubric 채점, workflow utility는 **Not Verified**다. `submitted_unverified`는 원격 수신이나 human utility acceptance를 뜻하지 않는다.

기본 CI에서 optional SDK-specific test가 skip될 수 있다는 검토 follow-up도 남는다. SDK 4.15.6의 media 동작은 이 보고서 작성 시 로컬 extra 환경에서 검증했다. 관련 upstream 구현은 [pinned MediaManager](https://github.com/langfuse/langfuse-python/blob/v4.15.6/langfuse/_task_manager/media_manager.py)와 [pinned environment variable definitions](https://github.com/langfuse/langfuse-python/blob/v4.15.6/langfuse/_client/environment_variables.py)에서 확인할 수 있다.

```yaml
revision:
  reviewed_base: 0c0ff02a384943d60810997e5404ee6786564967
  reviewed_code_head: 521e44e90fd535ddb7ca4671b5d117f5e4f9a346
```
