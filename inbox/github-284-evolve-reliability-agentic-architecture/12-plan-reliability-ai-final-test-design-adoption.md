---
type: plan
title: "PR #284 Final Review and Test Design Adoption Plan"
description: "11번 최종 리뷰·테스트 설계 번들의 후보 6건을 최신 HEAD(800e613e)와 대조해 수용 대상 3건(T1·T2·T3)과 보류·제외 3건을 판정하고 RED→GREEN 착수 계획을 정의한다."
tags:
  - reliability-ai
  - runtime-ai
  - testing
  - code-review
---

# PR #284 Final Review and Test Design Adoption Plan

## Summary

**11번 최종 리뷰 번들([Final Review](11-review-reliability-agentic-final/README.md), [Final Test Design Report](11-review-reliability-agentic-final/report-test-design-final.md))의 후보 6건을 최신 `HEAD`(`800e613e370ee5799aa7dca11080df06e730ead2`)의 코드·정본 명세·기존 테스트와 독립 대조한 결과, 실제 코드·테스트 보강으로 수용할 항목은 3건(P0 2건 + P1 경량 보강 1건)이며 나머지 3건은 보류·제외(`Defer` / `No-op`)로 판정한다.**

수용한 3건은 기존 아키텍처나 공개 API를 넓히지 않고 [Migration Tasks](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/tasks.md)의 기존 소유 과제(Task 2·Task 4) 안에서 RED 재현 → 최소 수정 → GREEN 및 독립 리뷰(`mols-review-dualvantage`) 순서로 처리한다.

- **Work unit:** PR #284, branch `agent/refactor/evolve-reliability-agentic-architecture`
- **Baseline HEAD:** `800e613e370ee5799aa7dca11080df06e730ead2` (base `f1de6256cdd1e034f655b2f2ee3997481d0b195c`)
- **Governing contract:** [Reliability Agentic Review Spec](../../openspec/specs/reliability-agentic-review/spec.md), [Migration Tasks](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/tasks.md)

## Candidate Adjudication Matrix

| ID | Source Candidate | Decision | Code & Contract Basis |
| --- | --- | --- | --- |
| **P0 · T1** | 동일 응답 배치 내 중복 `tool_call.id` 거부 및 SDK→조사 회귀 ([Final Review F1](11-review-reliability-agentic-final/README.md#f1--reject-duplicate-provider-tool-call-ids-before-dispatch)) | **Accept (`current_required`)** | [`_normalize_tool_calls`](../../src/hmda_reliability/runtime_ai/provider.py)는 개별 `id` 형식만 검사하고 배치 내 ID 유일성을 확인하지 않는다. 조사 루프의 cycle 키는 `name + canonical_arguments`이므로 **동일 ID·서로 다른 유효 인자** 두 호출이 한 응답에 오면 둘 다 실행되어 같은 `tool_call_id`가 이력에 중복 기록된다. |
| **P0 · T2** | 백필 커밋 후 프로파일 실패 시 `diverged_after_profile_failure` 상위 상태(`partial`) 분류 및 복구 영수증 테스트 ([Final Review F2](11-review-reliability-agentic-final/README.md#f2--preserve-diverged-recovery-state-in-report-status)) | **Accept (`current_required`)** | 하위 [`ApprovalBackfillValidator`](../../src/hmda_reliability/reliability/remediation/recovery/executor.py)는 커밋 후 프로파일 실패 및 상태 불일치 시 `mutation_state="diverged_after_profile_failure"`, `reconciliation_action="request_new_validation_and_approval"`를 발생시킨다. 그러나 상위 [`_recovery_failure_status`](../../src/hmda_reliability/reliability_ai/execution/service.py) 허용 집합에 이 값이 빠져 `ReportEnvelope.status`가 `"failed"`로 축약된다. |
| **P1 · T3** | 금지된 도구 응답(`allowed_tools=()`)에 대한 상위 실패 결과 Oracle 보강 ([Adversarial Test F1](11-review-reliability-agentic-final/test-design-adversarial.md#f1--assert-the-result-of-a-forbidden-tool-call)) | **Accept (경량 테스트 보강)** | [`test_delegated_task_enforces_empty_tool_allowlist_and_timeout`](../../tests/reliability_ai/test_execution_service.py)은 이미 금지된 도구 호출 응답을 주입하고도 반환된 `ReportEnvelope`를 확인하지 않으며, 현재 스위트 전체에 `"tool_not_allowed"` 반환을 직접 검증하는 assertion이 없다. 반환값 assertion 4줄 추가로 공백을 닫는다. |
| **P2 · T4** | 비신뢰 Evidence/도구 텍스트의 프롬프트 인젝션 역할 승격 방어 테스트 ([Adversarial Test F2](11-review-reliability-agentic-final/test-design-adversarial.md#f2--test-untrusted-content-without-pretending-to-test-model-obedience)) | **Defer (보류)** | [`investigate_incident`](../../src/hmda_reliability/reliability_ai/investigation/service.py)는 `canonical_input`과 `history`를 별도 메시지로 직렬화하며 기존 프롬프트 등록·관측 테스트가 system/user/history 역할 분리와 도구 allowlist 고정을 이미 검증한다. 현재 역할 승격 결함이 없다. |
| **11 · F2** | Custom handler 비직렬화(`datetime` 등) 반환 시 `json.dumps` 예외 정규화 ([Adversarial Code F2](11-review-reliability-agentic-final/adversarial-assessment.md#f2--non-json-tool-results-escape-error-normalization)) | **Defer (비차단 후속)** | 기본 [`ToolRegistry.from_review_input`](../../src/hmda_reliability/reliability_ai/investigation/tools.py) 경로는 모두 JSON-safe 값만 반환한다. 외부에서 비표준 객체를 반환하는 custom callback을 직접 주입할 때만 해당하므로 최종 리뷰 판정과 동일하게 후속으로 분리한다. |
| **Adv · F3** | Mocked Dataset 실험과 실모델·인간 평가 증거 분리 ([Adversarial Test F3](11-review-reliability-agentic-final/test-design-adversarial.md#f3--do-not-promote-mocked-dataset-completion-to-live-utility-evidence)) | **No-op (기반영)** | 코드·테스트 수정 대상이 아니며, 이미 PR #284 본문과 [10 Self-Review Report](10-report-reliability-agentic-merge-readiness-self-review.md)에서 오프라인 통과와 실모델·인간 평가를 분리 기록하고 있다. |

## Execution Sequence (TDD & Verification)

1. **OpenSpec Owning Tasks 재개 (`tasks.md`)**
   - [Migration Tasks](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/tasks.md)에서 T2/T3의 소유 과제인 **Task 2**와 T1의 소유 과제인 **Task 4**를 일시 재개(`tasks_completed: 5`)하고 각 테스트 조건을 명시한다.
1. **Step 1 — RED 재현 및 테스트 보강**
   - **T1 (`test_investigation_agent.py`)**: 실제 `OpenAI` SDK + `httpx.MockTransport` 경로에서 동일 ID(`"dup_call"` 및 공백 포함 `" dup_call "`)와 서로 다른 유효 `_ProfileArguments` 인자(`{"column":"income"}`, `{}`)를 가진 두 `compare_profiles` 호출을 반환하는 테스트(`test_duplicate_sdk_tool_call_ids_fail_before_dispatch`)를 추가하고 spy handler 호출 횟수를 관찰해 RED를 확인한다.
   - **T2 (`test_execution_service.py`)**: `test_post_mutation_failure_preserves_reconciliation_evidence`를 `(mutation_state, reconciliation_action, expected_status)` 3-튜플로 확장해 `("diverged_after_profile_failure", "request_new_validation_and_approval", "partial")`에서 RED를 확인한다.
   - **T3 (`test_execution_service.py`)**: `test_delegated_task_enforces_empty_tool_allowlist_and_timeout`에서 반환된 `report`의 `status == "failed"`, `investigation.failure_code == "tool_not_allowed"`, `execution_receipts == ()`를 검증한다.
1. **Step 2 — 최소 구현 및 GREEN 확인**
   - **T1 (`runtime_ai/provider.py`)**: `_normalize_tool_calls`에서 `seen_ids: set[str]`로 strip된 `ToolCall.id` 유일성을 검사해 중복 시 `ValueError("duplicate function tool call id")`를 발생시킨다. 기존 `invalid_provider_tool_calls` 및 `raw_tool_calls` 로컬 보존 경로가 그대로 동작하는지 확인한다.
   - **T2 (`reliability_ai/execution/service.py`)**: `_recovery_failure_status`의 `"partial"` 집합에 `"diverged_after_profile_failure"` 한 값만 추가한다.
1. **Step 3 — 회귀·정적 검사·독립 리뷰 및 완료 보고서(`13`) 작성**
   - `tests/reliability_ai`, `tests/runtime_ai`, `tests/reliability/test_approval_backfill_validation.py` 및 `ruff`, `ty`, `tach`, OpenSpec 검증을 실행한다.
   - `mols-review-dualvantage` 독립 서브에이전트 리뷰로 수정 상태를 재검증한다.
   - Task 2·Task 4를 다시 완료(`7/7 all_done`)로 닫고, 실행·검증·독립 리뷰 결과를 `13-report-reliability-ai-final-review-remediation.md`에 기록한다.
