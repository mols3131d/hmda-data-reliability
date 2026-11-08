---
type: review
title: "PR #284 Test Design Review"
description: "PR #284의 SDK 도구 호출 및 승인된 복구 상태 보고 테스트에서 반례, oracle, 모킹과 경계 재사용을 검토한다."
tags:
  - reliability-ai
  - runtime-ai
  - pull-request
  - testing
---

# PR #284 Test Design Review

> [!IMPORTANT]
> **Focused improvements; no broad redesign.** 기존 테스트는 실제 SDK 및 하위 복구 경계를 상당 부분 검증한다. 누락된 두 반례만 우선 확인한다. **아래 내용은 로컬 에이전트가 검증·반증해야 할 리뷰 후보**이며 자동 패치 지시가 아니다. 최종 인계와 우선순위는 [Final Review](README.md)를 따른다.

- **Target** — [PR #284](https://github.com/mols3131d/hmda-data-reliability/pull/284)의 `runtime_ai` → `reliability_ai.investigation`, approved recovery → `ReportEnvelope` 테스트
- **Revision** — base `f1de6256cdd1e034f655b2f2ee3997481d0b195c` → reviewed head `8b8946fd5aabf7163a6762a72092902411a9e043` (보고서 추가 시 head 갱신)
- **Scope** — provider/investigation/tool registry/execution 및 하위 DuckDB recovery 테스트와 관련 구현을 정적으로 대조했다. PR 전체 테스트·실제 모델·비용을 전수 감사한 결과는 아니다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 Major | 기존 비정상 SDK 호출 테스트는 **동일 응답 배치의 중복 ID**를 다루지 않는다. | 실제 SDK + MockTransport로 두 호출의 ID 충돌을 재현하고 배치 전체 거부, 도구 실행 0회, 원문 보존 확인 |
| F2 | 🟡 Minor | 하위 복구의 divergence 테스트가 있어도 상위 보고 테스트에는 해당 `mutation_state`와 재승인 의미가 없다. | 상위 status와 receipt에서 실제 상태·reconciliation action을 함께 확인 |

## Details

### F1 · Same-Batch Duplicate IDs Are Not Covered

#### Locations

- [`test_investigation_agent.py`](../../../tests/reliability_ai/test_investigation_agent.py)
  - `test_invalid_sdk_tool_calls_fail_without_losing_response`
  - `test_investigate_incident_detects_duplicate_tool_call_cycle`
- [`test_provider_tools.py`](../../../tests/runtime_ai/test_provider_tools.py)
  - `test_sdk_sends_tools_and_normalizes_tool_calls`
- [`provider.py`](../../../src/hmda_reliability/runtime_ai/provider.py)
  - `_normalize_tool_calls`

#### Evidence

기존 SDK 테스트는 잘못된 **개별** ID·타입·인자, valid+invalid 혼합 배치, `invalid_provider_tool_calls` 및 raw/manifest 보존을 검증한다. 그러나 같은 배치의 두 호출에 **동일 ID·상이한 유효 인자**를 부여한 사례는 없다. `duplicate_tool_call_cycle`은 **여러 턴에 걸친 동일 name+arguments 반복**이므로 다른 위험을 검증한다. 현재 `_normalize_tool_calls`에서는 배치 내 ID 유일성 확인을 볼 수 없다.

#### Impact

기존 테스트가 통과해도 한 provider 응답의 요청–결과 매칭과 실행 차단이 안전하다고 증명하지 못한다. [최종 리뷰 F1](README.md#f1--reject-duplicate-provider-tool-call-ids-before-dispatch)의 테스트 설계 공백이지 별개의 신규 생산 코드 결함을 주장하는 것은 아니다.

#### Action

1. 실제 `OpenAI` SDK + `httpx.MockTransport`로 하나의 `tool_calls` 응답에 동일 ID·서로 다른 유효 인자를 가진 호출 두 개를 넣는다. `ScriptedTransport`만 사용해서 SDK 정규화 검증을 대신하지 않는다.
1. 먼저 red test 또는 이미 존재하는 차단 경로를 확인한다. 문제가 유효하다면 `invalid_provider_tool_calls`, **주입된 spy handler 실행 0회**, raw turn 및 manifest 보존을 독립적으로 확인한다. `result.tool_calls == ()`만으로 handler의 부작용 부재를 증명하지 않는다.
1. SDK 또는 기존 safeguard가 이미 거부하면 불필요한 코드를 추가하지 않고 리뷰 F1을 기각·정정한다. 정상적인 ID가 서로 다른 다중 호출 테스트는 유지한다.

### F2 · Divergence Status Test Needs Correct Reconciliation Oracle

#### Locations

- [`test_approval_backfill_validation.py`](../../../tests/reliability/test_approval_backfill_validation.py)
  - `test_profile_failure_reports_diverged_post_mutation_state`
- [`test_execution_service.py`](../../../tests/reliability_ai/test_execution_service.py)
  - `test_post_mutation_failure_preserves_reconciliation_evidence`
- [`executor.py`](../../../src/hmda_reliability/reliability/remediation/recovery/executor.py)
  - `ApprovalBackfillValidator._execute_locked`
- [`execution/service.py`](../../../src/hmda_reliability/reliability_ai/execution/service.py)
  - `_recovery_failure_status`, `_failed_recovery_receipt`

#### Evidence

하위 실제 DuckDB 회귀는 profile 실패와 상태 divergence에서 `mutation_state="diverged_after_profile_failure"`, `reconciliation_action="request_new_validation_and_approval"`를 확인한다. 그러나 상위 parametrized 테스트는 `None → failed`와 `partition_changed → partial`만 다루고, 주입한 오류의 action은 모두 `resume_verification`이다. 따라서 상태만 파라미터에 추가하면서 action을 그대로 사용하면 **실제 하위 계약과 다른 테스트 입력**이 생긴다.

#### Impact

`ReportEnvelope.status` 오분류가 놓치고 넘어갈 수 있으며, 상위 테스트가 올바른 재승인 의미를 보존하는지 검증할 수 없다. [최종 리뷰 F2](README.md#f2--preserve-diverged-recovery-state-in-report-status)와 동일한 위험에 해당한다.

#### Action

1. 하위에서 이미 검증한 실제 예외 상태·action을 기준으로 상위 테스트에 divergence 사례를 추가한다. `mutation_state`·기대 `status`·`reconciliation_action`을 함께 parameterize하거나 focused test로 분리한다.
1. 독립 oracle은 `ReportEnvelope.status == "partial"`, 실패 영수증, 원본 `mutation_state`, `reconciliation_action="request_new_validation_and_approval"` 및 `details["context"]` 보존이다. 기존 실패 상태 회귀도 유지한다.
1. **기존 하위 DuckDB 통합 테스트를 재사용**한다. 상위 분류만 검증하는 데 새로운 전체 DB+LLM 통합 테스트를 만들 필요는 없다.

## Existing Safeguards and Scope

- **Keep** — 실제 SDK/MockTransport의 provider 경계, raw/manifest 보존, 하위 DuckDB 승인 복구, 상위 error/receipt 테스트는 적절하다. 도메인 동작을 모킹하거나 구조를 새로 만드는 방식으로 단순화하지 않는다.
- **Defer** — [초기 리뷰](adversarial-assessment.md)의 custom handler 비직렬화 테스트는 선택적 후속이다. 깊은 JSON 결과를 다루는 `test_unserializable_tool_record_preserves_safe_error_and_raw_turns`는 일반 Python 객체의 직렬화 실패를 보증하지 않지만 이를 별도 blocker로 확대하지 않는다.
- **Out of scope** — pytest marker 전면 개편, 테스트 러너 교체, 실모델 품질을 mocked output으로 검증한 것처럼 취급하는 작업.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 기존 테스트와 실제 producer/consumer 경계 대조 | 위 링크된 SDK·조사·복구 하위/상위 테스트와 구현을 PR head에서 정적으로 추적 |
| ✅ Pass | 기존 safeguard 및 가장 낮은 유효 test level 확인 | 실제 SDK MockTransport와 하위 DuckDB integration을 이미 갖추고 있음을 확인 |
| ⚪ Not Verified | 제안한 반례의 red/green 및 도구 부작용 | 로컬 pytest 또는 SDK 실패 재현을 실행하지 않았다 |
| ⚪ Not Verified | 광범위 회귀 및 모델 효용 | 이번 리뷰는 테스트 설계의 정적 판단이다. 기존 CI 통과는 미포함 반례의 정확성을 입증하지 않는다 |

## Risks and Limits

- F1·F2는 [Final Review](README.md)의 두 후보에 대응하는 **test coverage gap**이다. 독립적인 병합 차단 사유 두 건을 추가했다는 뜻이 아니다.
- 로컬 에이전트는 반례·계약·기존 보호 조치를 검증한 뒤 수용, 정정 또는 기각해야 한다. 기대 결과에 테스트나 구현을 억지로 맞추지 않는다.
