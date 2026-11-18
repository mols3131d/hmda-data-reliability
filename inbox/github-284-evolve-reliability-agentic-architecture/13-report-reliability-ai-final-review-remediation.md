---
type: report
title: "PR #284 Final Review and Test Design Remediation Report"
description: "12번 채택 계획에 따라 T1(동일 응답 배치 내 중복 tool-call ID 거부), T2(diverged_after_profile_failure의 partial 분류), T3(금지 도구 응답 실패 oracle)를 RED→GREEN 및 DualVantage 독립 리뷰(clear)로 완료한 결과를 정리한다."
tags:
  - reliability-ai
  - runtime-ai
  - testing
  - code-review
---

# PR #284 Final Review and Test Design Remediation Report

## Summary

**[12 Adoption Plan](12-plan-reliability-ai-final-test-design-adoption.md)에서 수용한 3건(P0 `T1`·`T2`, P1 `T3`)을 RED 재현 후 최소 범위로 구현·검증하고, 2차 `mols-review-dualvantage` 독립 리뷰에서 `clear`(확정 후보 0건, 미해결 항목 0건) 판정을 받았다.** 이로써 [11번 최종 리뷰 번들](11-review-reliability-agentic-final/README.md)의 병합 차단 사유(`F1`, `F2`)와 주요 테스트 oracle 공백이 모두 해소되었다.

| Item | Verified State (`2026-11-09`) |
| --- | --- |
| PR | [#284: refactor: evolve reliability into agentic domains](https://github.com/mols3131d/hmda-data-reliability/pull/284), Open / Draft |
| Owning branch | `agent/refactor/evolve-reliability-agentic-architecture` |
| Baseline HEAD | `800e613e370ee5799aa7dca11080df06e730ead2` (base `f1de6256cdd1e034f655b2f2ee3997481d0b195c`) |
| Modified code & tests | [`src/hmda_reliability/runtime_ai/provider.py`](../../src/hmda_reliability/runtime_ai/provider.py), [`src/hmda_reliability/reliability_ai/execution/service.py`](../../src/hmda_reliability/reliability_ai/execution/service.py), [`tests/reliability_ai/test_investigation_agent.py`](../../tests/reliability_ai/test_investigation_agent.py), [`tests/reliability_ai/test_execution_service.py`](../../tests/reliability_ai/test_execution_service.py) |
| OpenSpec tracking | [Migration Tasks](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/tasks.md) Task 2·Task 4 재개 후 완료 재확인 (`7/7 all_done`) |
| Independent review | 2차 `mols-review-dualvantage` 판정 `clear` (1차 리뷰 `C1` 테스트 인자 스키마 정합성 보완 완료) |

## Completed Remediations (RED → GREEN)

### 1. P0 · T1 — Reject Same-Batch Duplicate Tool-Call IDs Before Dispatch

- **Observed RED**: [`_normalize_tool_calls`](../../src/hmda_reliability/runtime_ai/provider.py)에 배치 내 ID 유일성 검사가 없을 때, 동일 응답 내 중복 ID 호출이 정규화를 통과해 도구 디스패치 루프로 진입함을 확인했다.
- **Minimal Fix**: [`_normalize_tool_calls`](../../src/hmda_reliability/runtime_ai/provider.py)에서 `ToolCall` 생성(`NonEmptyStr` 공백 strip 정규화 포함) 직후 `seen_ids: set[str]`로 중복 `call.id`를 검사하고, 중복 발견 시 `ValueError("duplicate function tool call id")`를 발생시켜 배치 전체를 거부하도록 수정했다.
- **Independent Review C1 Resolution & Test Oracle**: 1차 `mols-review-dualvantage` 리뷰에서 초기 테스트 인자에 `_ProfileArguments` 스키마가 금지하는 `baseline_ref`가 포함되어 가드 없이도 스키마 검증 단계에서 `spy_handler`가 차단된다는 후보(`C1`)가 확인되었다. 이를 수용해 [`test_duplicate_sdk_tool_call_ids_fail_before_dispatch`](../../tests/reliability_ai/test_investigation_agent.py)의 두 `compare_profiles` 호출을 스키마상 모두 유효하고 서로 다른 cycle fingerprint를 갖는 `'{"column":"income"}'`과 `'{}'`(ID는 `"dup_call"`과 `" dup_call "`)로 교정했다. 수정 후 `result.status == "error"`, `failure_code == "invalid_provider_tool_calls"`, `spy_calls == []`, 요청 1회, 로컬 본문 및 `raw_tool_calls` 보존을 확인했다.

### 2. P0 · T2 — Preserve `diverged_after_profile_failure` as `partial` in `ReportEnvelope`

- **Observed RED**: [`test_post_mutation_failure_preserves_reconciliation_evidence`](../../tests/reliability_ai/test_execution_service.py)에 `("diverged_after_profile_failure", "request_new_validation_and_approval", "partial")` 사례를 추가했을 때 `AssertionError: assert 'failed' == 'partial'`로 실패함을 확인했다.
- **Minimal Fix & GREEN**: [`_recovery_failure_status`](../../src/hmda_reliability/reliability_ai/execution/service.py)의 `"partial"` 허용 집합에 `"diverged_after_profile_failure"` 한 값만 추가했다. 재실행 결과 `report.status == "partial"`, `receipt.mutation_state == "diverged_after_profile_failure"`, `receipt.reconciliation_action == "request_new_validation_and_approval"`, `receipt.details["context"]` 보존 및 기존 `None → failed`, `partition_changed → partial` 회귀 유지를 확인했다.

### 3. P1 · T3 — Assert Upper Failure Outcome for Forbidden Tool Response

- **Oracle Tightening**: [`test_delegated_task_enforces_empty_tool_allowlist_and_timeout`](../../tests/reliability_ai/test_execution_service.py)에서 `execute_delegated_task`의 반환값을 받아 `report.status == "failed"`, `report.investigation.failure_code == "tool_not_allowed"`, `report.execution_receipts == ()`를 직접 검증하도록 보강했다.

## Verification Evidence

| Check | Command / Scope | Result |
| --- | --- | --- |
| Focused T1·T2·T3 pytest | `uv run --no-sync pytest tests/reliability_ai/test_investigation_agent.py tests/reliability_ai/test_execution_service.py -k 'duplicate_sdk_tool_call_ids_fail_before_dispatch or post_mutation_failure_preserves_reconciliation_evidence or enforces_empty_tool_allowlist'` | **5 passed** (T1·T2 RED 확인 후 GREEN 전환) |
| AI·Runtime·Recovery 스위트 | `env TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" uv run --no-sync pytest tests/reliability_ai tests/runtime_ai tests/reliability/test_approval_backfill_validation.py -n auto -q --tb=short` | **281 passed** |
| 정적 분석·경계 검사 | `ruff check`, `ruff format --check`, `ty check`, `tach check` | **All passed** (진단 0건) |
| OpenSpec·Markdown·Inbox | `openspec validate reliability-agentic-review-enable-bounded-tools --strict`, `rumdl check`, `validate_inbox_artifacts.py` | **All passed** (`tasks_completed: 7/7`, `state: all_done`) |
| 2차 DualVantage 독립 리뷰 | `mols-review-dualvantage` (Verifier + Challenger 동시 실행, C1 수정 반영 후) | **`clear`** (확정 후보 0건, 미해결 항목 0건, Verifier 독립 실행 133 passed 확인) |

## Remaining Actions

1. **Ready 전환 및 병합 판단**: 수정된 코드·테스트·OpenSpec Tasks 및 인박스 문서(`12`, `13`)는 서명 커밋으로 원격 브랜치에 반영하고 PR #284 본문(`revision.head` 포함)도 동기화한다. 사람의 판단에 따라 Draft 해제(`Ready for review`) 및 Squash Merge를 진행한다.
1. **비차단 후속 및 운영 평가 분리**: [12 Adoption Plan](12-plan-reliability-ai-final-test-design-adoption.md)에서 `Defer`로 분류한 custom handler 비직렬화 반환 정규화(`11·F2`)와 프롬프트 인젝션 역할 테스트(`P2·T4`), 그리고 실모델 재실험·5개 기준 인간 평가는 본 PR의 오프라인 코드·계약 완료와 구분하여 관리한다.
