---
type: review
title: "PR #284 Final Review Adjudication"
description: "PR #284의 인박스 리뷰 11·12를 최신 코드·계약·테스트와 대조해 필수 수정과 비차단 후속 개선을 구분한 최종 리뷰 및 로컬 에이전트 인계."
tags:
  - reliability-ai
  - runtime-ai
  - pull-request
  - code-review
---

# PR #284 Final Review Adjudication

> [!IMPORTANT]
> **이 번들의 최종 리뷰입니다.** 로컬 에이전트는 아래 **Findings**와 **Local Agent Handoff**를 우선 적용합니다. [Adversarial review](adversarial-assessment.md) 및 [Recovery status review](recovery-status-propagation.md)는 초기 후보·근거를 보존한 참고 자료이며, 우선순위와 최종 처분은 이 문서에 따릅니다.

> [!WARNING]
> **Revise (changes_required)** — [리뷰 11](adversarial-assessment.md)·[리뷰 12](recovery-status-propagation.md)의 세 후보를 최신 소스에 대조했다. **병합 전 수정할 문제는 2건(F1, F2)**이다. 기본 경로가 아닌 신뢰된 custom handler의 비직렬화 반환 문제는 실제 도달 가능한 예외지만, 현재 병합 차단 사유에서 제외하고 선택적 후속 개선으로 분리한다.

- **Target** — [PR #284: refactor: evolve reliability into agentic domains](https://github.com/mols3131d/hmda-data-reliability/pull/284)
- **Revision** — base `f1de6256cdd1e034f655b2f2ee3997481d0b195c` → reviewed head `8981c375430bf04904066c6ac2218c76b91fb3f5` (이후 본 보고서 추가 시 head는 변경됨)
- **Scope** — 리뷰 11·12의 세 candidate를 provider 정규화·도구 실행·복구 상태 전달 및 직접 관련 계약·테스트에 한정해 재검증했다. 별도의 PR 전체 전수 리뷰나 독립 서브에이전트 재심사는 수행하지 않았다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 Major | 한 provider 응답에 중복된 tool-call ID가 있어도 서로 다른 인자의 두 도구 호출이 실행되어 요청–결과 대응이 모호해질 수 있다. | 정규화 단계에서 배치 전체 거부, SDK→조사 회귀 테스트 |
| F2 | 🟡 Minor | 백필 후 `diverged_after_profile_failure`가 `ReportEnvelope.status="failed"`로 축약되어 변경·불일치 상태를 상위 보고에서 과소 표현한다. | `partial` 분류 추가, 영수증·재승인 요구 회귀 테스트 |

## Candidate Decisions

| Source | Candidate | Decision | Reason |
| --- | --- | --- | --- |
| [11 · F1](adversarial-assessment.md#f1--duplicate-provider-tool-call-ids-are-accepted) | 동일 응답의 tool-call ID 충돌 | **Accept → F1 / current_required** | ID 유일성 검사 부재와 이름·인자 기반 cycle fingerprint를 현재 코드에서 확인했다. 이번 변경의 matching-history 계약에 직접 연관된다. |
| [11 · F2](adversarial-assessment.md#f2--non-json-tool-results-escape-error-normalization) | custom handler의 비직렬화 결과가 오류 정규화 밖으로 이탈 | **Defer → follow_up / non-blocking** | 예외 경로는 실제지만 caller가 명시적으로 주입한 handler가 JSON 비호환 값을 반환할 때만 발생한다. 확인한 기본 handler 결과에는 적용되지 않으며, 현 PR의 필수 acceptance를 단독 차단할 근거는 부족하다. |
| [12 · F1](recovery-status-propagation.md#f1--diverged-post-mutation-failure-is-misclassified) | post-mutation divergence의 상위 상태 오분류 | **Accept → F2 / current_required** | 하위 실행기에서 생성하는 상태가 상위 분류 목록에 없다는 것을 확인했다. 승인된 복구 상태의 의미 전달과 직접 관련된다. |

두 필수 finding은 **각기 다른 root cause**이므로 별개로 유지한다. 반면 신규 발견처럼 표현된 무승인 mutation, 원래 복구 영수증의 완전한 손실, 기본 handler의 정상 출력에서 발생하는 직렬화 실패는 확인되지 않아 최종 finding에 포함하지 않는다.

## Details

### F1 · Reject Duplicate Provider Tool-Call IDs Before Dispatch

#### Locations

- [`src/hmda_reliability/runtime_ai/provider.py`](../../../src/hmda_reliability/runtime_ai/provider.py)
  - `_normalize_tool_calls` (434–465행), `_OpenAIChatCompletionTransport.create` (382–394행)
- [`src/hmda_reliability/reliability_ai/investigation/service.py`](../../../src/hmda_reliability/reliability_ai/investigation/service.py)
  - `executed_call_fingerprints`, `history` 및 `registry.execute` (478–555행)
- [`tests/reliability_ai/test_investigation_agent.py`](../../../tests/reliability_ai/test_investigation_agent.py)
  - `test_invalid_sdk_tool_calls_fail_without_losing_response` 및 SDK `httpx.MockTransport` 패턴

#### Evidence

`_normalize_tool_calls`는 개별 `id`의 형식만 검사하고 한 응답 내 중복을 검사하지 않는다. 반면 조사 루프의 반복 탐지는 `function.name + canonical arguments`를 기준으로 하므로 **ID는 같지만 인자가 다른 두 요청**은 둘 다 실행될 수 있다. 이 경우 두 tool message가 같은 `tool_call_id`로 이력에 들어가 matching 관계를 모호하게 만든다. 기존 invalid-tool-call 오류 경로는 raw 호출과 failure code를 보존하므로 새 에러 체계를 만들 필요는 없다.

#### Impact

잘못된 provider 출력이 실행 경계를 통과해 후속 모델 이력과 invocation provenance의 요청–결과 매핑을 불명확하게 만든다. 이 경로가 무승인 데이터 변경을 허용한다는 근거는 없다. **정적 경로로 입증한 위험이며 실제 SDK 재현 테스트는 미실행**이다.

#### Action

1. `_normalize_tool_calls`에서 응답 배치 내 `id` 유일성을 검사하고, 중복 발견 시 실행 전 `ValueError`로 배치 전체를 거부한다. 기존 `invalid_provider_tool_calls`·`raw_tool_calls` 보존 경로를 재사용한다.
1. `test_investigation_agent.py`의 실제 SDK + `httpx.MockTransport` 사례에 **서로 다른 인자와 동일 ID인 두 호출**을 추가한다. 도구 실행 0회, `InvestigationResult(status="error", failure_code="invalid_provider_tool_calls")`, 회수 가능한 raw turn과 manifest를 검증한다.
1. 정상적인 서로 다른 ID 호출과 기존 cycle detection 동작이 유지되는지 확인한다.

### F2 · Preserve Diverged Recovery State In Report Status

#### Locations

- [`src/hmda_reliability/reliability/remediation/recovery/executor.py`](../../../src/hmda_reliability/reliability/remediation/recovery/executor.py)
  - `ApprovalBackfillValidator._execute_locked` (183–260행)
- [`src/hmda_reliability/reliability_ai/execution/service.py`](../../../src/hmda_reliability/reliability_ai/execution/service.py)
  - `BackfillValidationError` 처리 (208–221행), `_recovery_failure_status` (348–362행)
- [`tests/reliability_ai/test_execution_service.py`](../../../tests/reliability_ai/test_execution_service.py)
  - `test_post_mutation_failure_preserves_reconciliation_evidence` (406–455행)

#### Evidence

하위 실행기는 profile snapshot 실패와 예상 상태 대비 실제 identity/freshness 불일치가 겹치면 `BackfillValidationError(mutation_state="diverged_after_profile_failure", reconciliation_action="request_new_validation_and_approval")`를 발생시킨다. 상위 `_recovery_failure_status`에는 이 상태가 없어서 `failed`로 분류된다. **기존 `ExecutionReceipt`는 원래 mutation state와 reconciliation context를 보존한다.** 따라서 문제는 정보 전체 손실이 아니라 envelope의 상태 축약이다.

#### Impact

영수증까지 읽지 않는 supervisor나 보고 소비자가 변경 이후 상태의 불일치 및 신규 검증·승인 필요성을 일반 실행 실패로 해석할 수 있다. 별도 승인 게이트를 우회한다는 증거는 없다.

#### Action

1. `_recovery_failure_status`의 `partial` 허용 목록에 `diverged_after_profile_failure` **한 값만** 추가한다. 다른 상태의 의미를 추측해 일괄 변경하지 않는다.
1. 기존 parametrized test에 `("diverged_after_profile_failure", "partial")`를 추가한다. 해당 사례에서 `reconciliation_action="request_new_validation_and_approval"`, 원본 `mutation_state`, `details["context"]`가 보존되는지도 검증한다.
1. `None → failed`, `partition_changed → partial` 기존 사례를 유지해 상위 상태 분류의 회귀를 막는다.

## Non-Blocking Follow-up

**11 · F2 — Custom handler JSON serialization.** `ToolRegistry.execute`의 `try/except`는 `project_remote_output(self._dispatch(...))`까지만 감싸고, 마지막 `json.dumps(result)`는 바깥에 있다. 주입된 `profile_comparison_handler` 또는 `impact_handler`가 `{"observed_at": datetime(...)}` 등 JSON 비호환 `dict`를 반환하면 `TypeError`가 호출자에게 이탈할 수 있다. 다만 **custom handler 주입 시에 한정**하며 기본 구현 결함이나 현재 데이터 mutation 위험으로 확대하지 않는다.

이 경계의 내구성이 필요해지면 serialization을 성공 판정 전에 수행하고 `tool_execution_failed` 레코드로 정규화하는 focused test를 추가한다. 본 PR의 병합 차단 finding이나 무관한 아키텍처 재설계로 승격하지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 검토 revision과 리뷰 이후 코드 변경 여부 | `860fbcae…8981c375` 비교에서 후속 커밋은 **리뷰 11·12 두 문서만 추가**했고 코드 변경이 없음을 GitHub commit diff에서 확인 |
| ✅ Pass | F1 소스·기존 safeguard 대조 | `provider.py` ID 검증, `investigation/service.py` fingerprint·dispatch·history와 기존 SDK malformed-call 회귀 테스트를 정적으로 확인 |
| ✅ Pass | F2 하위/상위 상태·영수증·테스트 대조 | `recovery/executor.py`의 divergence 발생 조건, `execution/service.py` 분류/receipt, 테스트 파라미터를 정적으로 확인 |
| ✅ Pass | 계약·범위 대조 | `openspec/specs/reliability-agentic-review/spec.md`의 matching tool history, typed failure, mutation/reconciliation reporting 요구사항을 확인 |
| ⚪ Not Verified | 문제 재현 및 수정 후 focused pytest | 원격 파일의 **정적 검토만 수행**했다. 로컬 패키지 테스트와 MockTransport 재현은 실행하지 않았다 |
| ⚪ Not Verified | 현재 head 기준 CI·독립 리뷰·모델 품질 | [기존 셀프 리뷰](../10-report-reliability-agentic-merge-readiness-self-review.md)의 CI 및 독립 리뷰 결과는 과거 revision 증거다. 이번 검토에서 재실행하거나 현재 문제의 부재를 확인한 것은 아니다 |

## Local Agent Handoff

1. **F1 우선** — 단일 응답 ID 충돌을 정규화 단계에서 원자적으로 거부하고 실제 SDK 회귀로 도구 미실행·원문 보존을 입증한다.
1. **F2 다음** — 상위 보고 상태 분류만 최소 수정하고, 원본 영수증·재검증/재승인 안내가 유지되는 회귀 테스트를 보강한다.
1. 수정한 코드 revision에서 focused pytest와 영향받는 정적·CI 검증을 실행한다. 결과와 exact head SHA를 남기고 PR [Review Readiness](../../../docs/development/vcs-git/pull-request.md#review-readiness)를 재판정한다.
1. **Non-blocking follow-up**은 handler JSON 반환 규약과 실제 소비자가 확인된 경우에만 별도 판단한다. 임의의 scope 확대, 데이터 변경, 승인·복구 권한 변경, 과거 기록 수정은 하지 않는다.

## Risks and Limits

- F1·F2는 현재 코드와 계약으로 확인한 **reasoned findings**다. 실제 실패 재현(`observed`)으로 과장하지 않는다.
- 이 문서는 기존 두 리뷰의 **후보 검증·우선순위 조정**이며 세 번째 독립 전수 리뷰가 아니다. VS Code 전용 다중 reviewer나 로컬 테스트 환경을 호출하지 않았으므로 독립 검증 게이트를 충족했다고 주장하지 않는다.
- [10번 셀프 리뷰](../10-report-reliability-agentic-merge-readiness-self-review.md)의 과거 `ready` 판단은 이후 새로 확인된 F1·F2를 반영하지 않는다. 변경 및 재검증 전에는 최신 merge readiness 근거로 사용하지 않는다.
- 이번 작업은 인박스 보고서만 작성한다. 코드·테스트 수정, PR Ready 전환, GitHub approval, merge는 수행하지 않는다.
