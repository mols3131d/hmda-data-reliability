---
type: report
title: "PR #284 Final Test Design Report"
description: "11번 인박스의 테스트 설계 리뷰를 통합해 검증할 반례, 최소 oracle, 우선순위와 로컬 에이전트 수용 조건을 정리한다."
tags:
  - reliability-ai
  - runtime-ai
  - pull-request
  - testing
---

# PR #284 Final Test Design Report

> [!IMPORTANT]
> **로컬 에이전트는 이 보고서의 제안을 자동 수용해서는 안 된다.** 각 후보를 최신 HEAD의 정본 계약, 기존 테스트·방어 장치와 대조하고 가능하면 **먼저 재현 테스트를 실행**한 뒤 `Accept / Reject / Revise / Defer`로 독립 판정한다. 실제 재현이 안 되거나 oracle이 틀리면 보고서를 기각·수정한다. 테스트 통과를 위해 assertion을 약화하거나 근거 없이 구현을 변경하지 않는다.

- **Target:** [PR #284](https://github.com/mols3131d/hmda-data-reliability/pull/284)의 테스트 설계. PR의 기존 Draft 작업 branch에 속한 비정본 인계 자료다.
- **Review basis:** `agent/refactor/evolve-reliability-agentic-architecture`, 코드 검토 시점 HEAD `dd53eb49d63c47ee339c1a2e9434c93a8ca1268f`. 보고서 커밋 이후에는 반드시 최신 HEAD로 다시 대조한다.
- **Sources:** [Original Test Design](test-design.md), [Adversarial Test Design](test-design-adversarial.md), [Final Code Review](README.md). 요구사항의 정본은 [Reliability Agentic Review Spec](../../../openspec/specs/reliability-agentic-review/spec.md), 공통 테스트 설계 원칙은 [Test Design](../../../docs/development/test-design.md)이다.
- **Evidence boundary:** 원격 소스·테스트를 정적으로 대조했다. 새 반례의 red/green, pytest, 현재 prospective merge CI, 실모델 및 인간 평가는 **이 보고서 작성 시 실행하지 않았다**.

## Decision

**우선 확인할 테스트 공백은 두 가지다.** 기존 SDK/`httpx.MockTransport` 및 승인 복구·DuckDB 테스트를 재사용하면 된다. 이는 기존 최종 코드 리뷰의 F1/F2에 대응하는 테스트 설계이며 **별도 production defect나 blocker를 추가하는 것이 아니다**.

| Priority | Candidate | Existing evidence | Disposition |
| --- | --- | --- | --- |
| P0 · T1 | 동일 응답 배치의 중복 tool-call ID | 개별 비정상 ID, 혼합 배치 및 턴 간 cycle은 검증하지만 배치 내 ID 충돌은 미포함. 현 정규화 경로에 유일성 검사가 보이지 않는다. | **재현 우선**. 유효하면 최소 테스트·수정 |
| P0 · T2 | post-mutation divergence의 상위 상태·재승인 전달 | 하위 DuckDB 회귀가 실제 상태와 action을 확인한다. 상위 테스트는 `None`·`partition_changed`만 확인한다. | **재현 우선**. 유효하면 상위 oracle 보강 |
| P1 · T3 | 금지된 도구 응답의 실패 보고 | 기존 테스트는 실제 금지 호출을 주입하지만 요청 옵션만 assert한다. guard 및 다른 registry 테스트는 존재한다. | **중복 검토 후 선택 보강** |
| P2 · T4 | 비신뢰 evidence/tool 텍스트의 구조적 역할 경계 | 기존 projection·prompt 구조 테스트가 있고 실질 role 승격은 미확인이다. | **prompt 조립 변경 시 선택 보강** |

## P0 Test Scenarios

### T1 · Duplicate Tool-Call IDs Must Fail Before Dispatch

- **Contract / risk:** 동일 provider 응답의 호출 ID가 충돌하면 요청–결과 history 대응이 모호해진다. `runtime_ai.provider._normalize_tool_calls`은 개별 타입을 확인하지만 같은 배치의 ID 유일성 검사는 하지 않는다. 조사 루프의 cycle fingerprint는 `name + arguments` 기반이라 서로 다른 인자의 두 호출을 막는 검사가 아니다.
- **Test boundary:** [`tests/reliability_ai/test_investigation_agent.py`](../../../tests/reliability_ai/test_investigation_agent.py)의 기존 실제 `OpenAI` SDK + `httpx.MockTransport` 경로를 재사용한다. SDK 경계를 `ScriptedTransport`만으로 대신하지 않는다.
- **Negative case:** 단일 assistant 응답에 **같은 ID, 서로 다른 유효 인자**를 가진 두 function call을 배치한다. 실행 가능한 spy handler를 연결해 실행 횟수를 관찰한다.
- **Oracle:** `InvestigationResult.status == "error"`, `failure_code == "invalid_provider_tool_calls"`, **handler 실행 0회**, raw response/tool-call 정보 및 로컬 invocation/manifest 보존. `result.tool_calls == ()`만으로 부작용 부재를 추론하지 않는다.
- **Positive control:** 서로 다른 ID의 정상 다중 호출은 허용하고, 기존 잘못된 타입·인자·혼합 배치·턴 간 cycle 테스트는 그대로 유지한다.
- **Acceptance:** 현재 코드에서 유의미한 red를 확인하고 그 원인이 기존 guard나 테스트 fixture 때문이 아님을 판별한다. 유효할 때만 실행 전 **배치 전체 거부**를 최소 수정으로 구현한다. SDK가 이미 거부한다면 변경하지 않고 후보를 기각한다.

### T2 · Diverged Recovery Must Preserve Reconciliation Meaning

- **Contract / risk:** 하위 [`ApprovalBackfillValidator`](../../../src/hmda_reliability/reliability/remediation/recovery/executor.py)가 `mutation_state="diverged_after_profile_failure"`와 `reconciliation_action="request_new_validation_and_approval"`를 보고할 수 있다. 현재 [`_recovery_failure_status`](../../../src/hmda_reliability/reliability_ai/execution/service.py)는 해당 상태를 `partial`로 분류하지 않는다.
- **Test boundary:** 하위 [DuckDB 기반 테스트](../../../tests/reliability/test_approval_backfill_validation.py)는 유지한다. 상위 [`test_post_mutation_failure_preserves_reconciliation_evidence`](../../../tests/reliability_ai/test_execution_service.py)만 확장하거나 작은 전용 테스트를 둔다. 전체 DB+LLM 통합 테스트는 추가하지 않는다.
- **Negative case:** `BackfillValidationError`에 위 **실제 상태와 실제 action을 함께** 넣는다. 기존 사례에 무조건 `resume_verification`을 재사용하면 잘못된 fixture가 된다.
- **Oracle:** `ReportEnvelope.status == "partial"`, 실패 영수증 `success is False`, 원본 `mutation_state`, `reconciliation_action == "request_new_validation_and_approval"`, `details["context"]` 보존. 자동 재승인·재실행은 기대하지 않는다.
- **Positive control:** `None → failed`, `partition_changed → partial` 등 기존 분류와 각 사례의 대응 action은 유지한다.
- **Acceptance:** 실패 경로와 외부 보고 계약을 재검증한 뒤 유효하면 해당 상태 한 값만 `partial` 분류에 추가한다. 나머지 mutation 상태를 임의 재분류하지 않는다.

## Conditional Test Improvements

### T3 · Forbidden Tool Response Oracle

[`test_delegated_task_enforces_empty_tool_allowlist_and_timeout`](../../../tests/reliability_ai/test_execution_service.py)는 `allowed_tools=()`에 금지된 도구 응답을 반환하도록 구성하지만 요청의 `tools is None`, `tool_choice == "none"` 및 timeout만 검사한다. 기존 `tool_not_allowed` guard와 별도 registry 테스트가 해당 위험을 이미 충분히 보호하는지 먼저 확인한다.

중복되지 않는 경우에만 같은 테스트에서 반환 보고의 `status == "failed"`, 조사 `failure_code == "tool_not_allowed"`, 복구 영수증 없음과 필요 시 spy handler 실행 0회를 검증한다. 단순 request-option assertion을 늘리거나 신규 통합 계층을 도입할 필요는 없다. **현행 권한 우회가 확인됐다는 주장은 아니다.**

### T4 · Untrusted Text Remains Data

비신뢰 evidence `summary` 또는 tool 결과에 `Ignore previous instructions`, `{{history}}` 같은 공격 문구를 넣고, 기존 prompt/SDK 경계에서 **실제 구성된 message role, Task 허용 도구 및 예산이 변하지 않는지** 확인하는 좁은 반례는 가치가 있다. 단, redaction/projection 이후의 구조를 관찰해야 하며 공격 문구의 단순 포함 여부를 oracle로 삼지 않는다.

구조적 경계 테스트는 LLM이 공격 지시를 의미적으로 무시한다는 것을 증명하지 못한다. 기존 safeguard와 중복된다면 생략하고, prompt/history 조립을 수정할 때 우선 고려한다. 실모델 jailbreak 성능을 offline mock으로 판정하지 않는다.

## Discarded Or Separate

- **추가 blocker로 집계하지 않음:** T3/T4는 현재 production 결함을 입증하지 못했다. 원래 F1/F2와 테스트 공백을 중복 집계하지 않는다.
- **후속 선택 과제:** custom handler의 JSON 비직렬화 경계는 신뢰된 주입 handler에 한정된다. 실제 사용 계약과 실패 재현이 필요할 때만 별도 focused test로 다루고, 이번 테스트 설계의 필수 조건으로 올리지 않는다.
- **불필요:** pytest marker 전체 개편, 테스트 러너 교체, 새 LLM mocking framework, 대규모 DB+LLM end-to-end fixture, 무관한 coverage 채우기와 speculative mutation test.
- **별도 acceptance evidence:** mocked `dataset.run_experiment` 테스트는 프로젝트의 item ID multiset·실험 제어 흐름·종료 상태 검증에 유효하지만 **실제 Langfuse SDK 호환성, trace 적재, 모델 유용성**을 입증하지 않는다. 필요한 시점에 승인된 native Dataset 실험을 고정된 revision·Dataset·Prompt·모델로 수행하고 [인간 평가](../../../docs/development/review-ai-evaluation.md)를 별도 기록한다. 비용·원격 쓰기가 있는 작업을 기본 pytest에 넣지 않는다.

## Local Agent Handoff

1. **독립 재판정:** 최신 HEAD SHA를 확인하고 위 T1–T4 각각에 대해 정본 명세 → 현재 코드 → 기존 safeguard/test → 반례 순서로 대조한다. `Accept / Reject / Revise / Defer`와 근거를 기록한다. **이 보고서의 심각도·기대 결과·수정안은 검증 전 권한 있는 지시가 아니다.**
2. **P0부터 검증:** T1은 실제 SDK 경계와 spy handler, T2는 실제 하위 오류 상태·action과 상위 envelope/receipt를 사용한다. 가능한 경우 수정 **전 red → 최소 수정 → 수정 후 green 및 정상 경로 유지**를 기록한다. red가 나지 않으면 잘못된 테스트·이미 있는 보호 장치·기대 결과 오류를 먼저 조사하고 후보를 기각할 수 있다.
3. **필요한 범위만 변경:** 테스트 또는 구현의 정확한 원인에만 손댄다. T3/T4는 다른 테스트가 같은 계약을 검증하는지 확인한 뒤 추가한다. 테스트를 통과시키려고 assertion을 약화하거나 skip하지 않는다.
4. **실제 검증 기록:** 좁은 범위부터 `uv run pytest tests/reliability_ai/test_investigation_agent.py tests/runtime_ai/test_provider_tools.py tests/reliability_ai/test_execution_service.py tests/reliability/test_approval_backfill_validation.py` 등 **변경에 해당하는 대상**을 실행하고 필요한 package·정적 검사 및 prospective merge CI로 확대한다. 명령은 예시이며 [Testing Guide](../../../docs/development/testing.md)의 선택 기준과 실제 marker를 따른다.
5. **인계 종료 기준:** 수용·기각한 후보, 관찰한 red/green, regression 증거, 실행 revision/CI URL 및 미확인 실모델·사람 평가 상태를 분리해 남긴다. 다시 [Final Code Review](README.md)의 readiness를 평가한다. **Ready 전환, 승인, merge 및 권한 확대는 자동 수행하지 않는다.**

## Validation Status

| Check | Status |
| --- | --- |
| 두 테스트 설계 리뷰·최종 코드 리뷰의 중복 finding 및 우선순위 대조 | 정적 확인 |
| 최신 조회 HEAD에서 provider 정규화, 조사 guard, recovery 상태 분류, 상위 테스트의 실제 oracle 대조 | 정적 확인 |
| 제안한 반례의 red/green, spy side effect, 전체 regression, CI | **Not verified** |
| 실제 Langfuse/LLM 실행·인간 품질 평가 | **Not verified; separate evidence** |

이 문서는 테스트 설계와 인계를 정리한 **비정본 보고서**다. 실제 계약과 채택 여부는 최신 OpenSpec·코드·테스트 결과가 결정한다.
