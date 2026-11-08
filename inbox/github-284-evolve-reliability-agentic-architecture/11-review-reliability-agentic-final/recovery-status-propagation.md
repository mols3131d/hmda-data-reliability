---
type: review
title: "PR #284 Recovery Status Propagation Review"
description: "PR #284의 승인된 백필 실행에서 mutation 이후 검증 실패가 상위 보고 상태로 전달되는 계약을 검토한다."
tags:
  - reliability-ai
  - recovery
  - pull-request
  - code-review
---

# PR #284 Recovery Status Propagation Review

> [!NOTE]
> **초기 검토 기록입니다.** 이 문서의 판정과 수정 우선순위는 [최종 리뷰](README.md)에서 재검토했습니다. 실제 작업은 최종 리뷰를 먼저 확인하세요.

> [!WARNING]
> **Revise (changes_required)** — 백필 후 프로파일 검증 실패 시 하위 실행기가 반환할 수 있는 `diverged_after_profile_failure`가 상위 상태 변환에서 빠져 있다. 실제 변경이 있었던 실패도 `ReportEnvelope.status="failed"`로 분류될 수 있으므로, 상태 분류와 회귀 테스트를 보완한 뒤 재검토한다.

- **Target** — [PR #284: refactor: evolve reliability into agentic domains](https://github.com/mols3131d/hmda-data-reliability/pull/284)
- **Revision** — base `f1de6256cdd1e034f655b2f2ee3997481d0b195c` → code head `860fbcaeb45f40d9803c20a7e14ad43c7e0920f3` (보고서 작성 전 PR head `32a07d92e1268c1e2878aedef54cfa8d7c3b207e`; 마지막 커밋은 인박스 문서만 추가)
- **Scope** — `reliability_ai.execution`의 승인된 복구 처리 및 `reliability.remediation.recovery`의 상태 의미, 관련 OpenSpec·회귀 테스트를 정적으로 대조했다. 전체 PR 167개 변경 파일의 전수·실행 리뷰는 아니다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟡 Minor | 변경 후 상태가 예상과 달라진 백필 검증 실패를 상위 보고가 일반 `failed`로 축약할 수 있다. | `diverged_after_profile_failure`를 변경 발생 상태로 분류하고 focused regression을 추가 |

## Details

### F1 · Diverged Post-Mutation Failure Is Misclassified

#### Locations

- [`execution/service.py`](../../../src/hmda_reliability/reliability_ai/execution/service.py)
  - `execute_delegated_task`의 `BackfillValidationError` 처리: 208–219행
  - `_recovery_failure_status`: 348–362행
- [`recovery/executor.py`](../../../src/hmda_reliability/reliability/remediation/recovery/executor.py)
  - `ApprovalBackfillValidator._execute_locked`: 183–260행
- [`test_execution_service.py`](../../../tests/reliability_ai/test_execution_service.py)
  - `test_post_mutation_failure_preserves_reconciliation_evidence`: 406행부터

#### Evidence

하위 백필 실행기는 `completed_mutation_state`를 설정한 뒤 `create_profile_snapshot`에서 `ProfileSnapshotError`가 발생하고 실제 content/freshness 상태가 승인된 예상 상태와 다르면 `BackfillValidationError(mutation_state="diverged_after_profile_failure", reconciliation_action="request_new_validation_and_approval")`를 발생시킨다.

상위 실행기는 해당 예외를 포착하지만 `_recovery_failure_status`가 허용한 상태 목록(`partition_changed`, `partition_replaced`, `already_recovered`, `table_replaced`, `already_restored`)에 `diverged_after_profile_failure`가 없어 `failed`를 반환한다. 현재 테스트는 `None → failed` 및 `partition_changed → partial`만 대조한다.

#### Impact

상위 감독자는 이미 발생한 데이터 변경과 불일치를 일반 실패로 취급할 수 있다. 이는 복구 후 상태를 점검하거나 신규 승인 여부를 판단하는 흐름을 혼동시킨다. 다만 `ExecutionReceipt`에는 원래 `mutation_state`, `reconciliation_action`, 예외 context가 남으므로 권한 우회나 상세 근거의 완전한 손실은 확인되지 않았다.

#### Action

- `_recovery_failure_status`가 `diverged_after_profile_failure`를 `partial`로 반환하게 최소 수정한다. 확정된 전체 mutation-state 의미를 하위 도메인 계약과 대조하고 다른 상태를 임의로 변경하지 않는다.
- 기존 `test_post_mutation_failure_preserves_reconciliation_evidence`에 `("diverged_after_profile_failure", "partial")` 경계 사례를 추가한다. `reconciliation_action="request_new_validation_and_approval"` 및 영수증의 원래 상태·context 보존도 확인한다.
- 수정 후 focused pytest와 영향받는 정적·CI 검증을 최신 revision 기준으로 다시 수행한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 대상 PR과 revision 확인 | GitHub PR 메타데이터: base `f1de6256`, 문서 작성 전 head `32a07d92`, Draft/Open |
| ✅ Pass | 하위 실행 → 예외 → 상위 상태 분류 정적 추적 | 링크된 `executor.py`, `execution/service.py`의 조건문 및 상태 목록 확인 |
| ✅ Pass | 관련 회귀 테스트 범위 확인 | `test_execution_service.py`의 기존 실패 분류 parameter 확인 |
| ⚪ Not Verified | 위 분기의 실제 재현 및 수정 후 테스트 | 이 검토는 원격 소스 정적 분석이다. focused pytest, 런타임 재현, 로컬 전체 스위트를 실행하지 않았다 |
| ⚪ Not Verified | 최신 문서 커밋의 CI와 제품 모델 품질 | PR 설명에 이전 코드 revision의 CI 통과가 기록됐으나, 신규 테스트·최종 모델 재실험·인간 효용 평가를 이 검토가 수행한 것은 아니다 |

## Risks and Limits

- **Evidence confidence:** F1은 소스에서 도출한 조건부 실행 경로에 근거한 `SUPPORTED` finding이다. 실제 데이터 변경을 재현한 `CONFIRMED` 실행 결과로 표현하지 않는다.
- **Scope relation / disposition:** 이 PR이 추가한 `ReportEnvelope` 상태 의미와 직접 연결된 `contract_dependency / current_required`다. 수정은 기존 위임 보고 계약 내에서 가능하며 승인·복구 권한을 확장하지 않는다.
- **Prior review:** [기존 Adversarial Code Review](adversarial-assessment.md)의 별도 F1(중복 tool-call ID), F2(주입형 handler 직렬화 오류)는 이 보고서의 F1과 독립적이며 해결 여부를 재검증하지 않았다. 두 검토의 finding을 혼동하거나 해결됐다고 간주하지 않는다.
- **Handoff:** 이 보고서는 read-only 검토 결과를 기록한다. 승인된 복구 코드·테스트는 수정하지 않았고 PR의 Ready 전환·approval·merge도 수행하지 않았다. 위 경계 테스트가 실패하는지 확인하고 필요한 수정·재검증을 거친 후 review readiness를 다시 판단한다.
