---
type: review
title: "PR #284 Adversarial Code Review"
description: "PR #284의 위임형 조사, provider/tool 경계, 복구 권한 및 근거 보존을 실패 중심으로 검토한 코드 리뷰다."
tags:
  - reliability-ai
  - runtime-ai
  - pull-request
  - code-review
---

# PR #284 Adversarial Code Review

> [!WARNING]
> **Revise (changes_required)** — 정적 코드 추적에서 비정상 provider 도구 호출의 ID 충돌을 허용하는 결함(F1)을 확인했다. 추가로 주입형 도구 handler가 직렬화 불가능한 결과를 반환하면 조사 실패가 정상적으로 기록되지 않는 경로(F2)가 있다. 기존 CI와 셀프 리뷰의 통과 기록만으로 이 두 실패 경로를 배제할 수 없으므로 수정과 회귀 검증 후 재평가한다.

- **Target** — [PR #284: refactor: evolve reliability into agentic domains](https://github.com/mols3131d/hmda-data-reliability/pull/284)
- **Revision** — base `f1de6256cdd1e034f655b2f2ee3997481d0b195c` → reviewed head `860fbcaeb45f40d9803c20a7e14ad43c7e0920f3`
- **Scope** — 변경 파일 166개 중 provider 응답 정규화, 도구 실행·조사 이력, 위임 복구 게이트, 출력 투영, 근거 저장 및 직접 대응 테스트·OpenSpec 계약을 우선 추적했다. 전체 파일의 동작을 실행하거나 전수 검증한 결과는 아니다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 Major | 한 provider 응답의 도구 호출 ID 중복을 허용해 assistant 호출과 도구 응답의 대응 관계가 모호해진다. | 정규화 단계에서 중복 ID를 일괄 거부하고 SDK→조사 회귀 테스트 추가 |
| F2 | 🟡 Minor | 주입형 도구 handler가 JSON으로 표현할 수 없는 결과를 반환하면 예외가 기록 경계를 벗어난다. | 도구 결과의 직렬화 가능성을 검증하고 실패를 오류 레코드로 정규화 |

## Details

### F1 · Duplicate Provider Tool-Call IDs Are Accepted

#### Locations

- [`runtime_ai/provider.py`](../../src/hmda_reliability/runtime_ai/provider.py)
  - `_normalize_tool_calls`, `_OpenAIChatCompletionTransport.create`
- [`runtime_ai/contracts.py`](../../src/hmda_reliability/runtime_ai/contracts.py)
  - `ToolCall.id`, `ChatMessage.tool_call_id`
- [`reliability_ai/investigation/service.py`](../../src/hmda_reliability/reliability_ai/investigation/service.py)
  - assistant `history` 및 tool result 추가 루프
- [`reliability-agentic-review/spec.md`](../../openspec/specs/reliability-agentic-review/spec.md)
  - `Provider-compatible bounded invocation`

#### Evidence

`_normalize_tool_calls`는 각 호출의 `type`, `id`, 함수명, 인자 형식을 확인하지만 **같은 batch의 ID 유일성을 확인하지 않는다**. 따라서 예를 들어 서로 다른 인자를 가진 두 호출에 동일한 `id="call_1"`이 있어도 각각 `ToolCall`로 승인된다. 조사 루프의 중복 탐지 키는 `function.name + arguments`이므로 이 경우를 차단하지 못한다. 이어서 이력에 같은 `tool_call_id="call_1"`을 가진 두 개의 tool message가 기록된다. 이는 명세의 assistant call–matching tool result 대응 관계를 모호하게 만든다.

기존 SDK 비정상 호출 테스트는 빈·공백 ID, 잘못된 이름·인자·타입을 검증하지만, **서로 다른 두 호출의 동일 ID**를 검증하는 사례는 확인하지 못했다.

#### Impact

잘못된 provider 응답을 `invalid_provider_tool_calls`로 거부하지 못하고, 도구를 실행한 다음 모호한 이력을 후속 모델 호출에 전달할 수 있다. 제공자의 후속 이력 검증 실패뿐 아니라 어떤 결과가 어떤 요청에 대응했는지 provenance가 불명확해진다. 승인 없는 mutation으로 이어지는 경로를 확인한 것은 아니다.

#### Action

한 응답에서 도구 호출 ID가 중복되면 실행 전에 **batch 전체를 실패로 처리**하고 기존 `raw_tool_calls`·원문·실패 manifest 보존 경로를 재사용한다. 실제 OpenAI SDK + `httpx.MockTransport`로 중복 ID/상이한 인자를 반환하는 사례를 추가해 도구 실행 0회, `invalid_provider_tool_calls` 및 회수 가능한 근거를 검증한다.

### F2 · Non-JSON Tool Results Escape Error Normalization

#### Locations

- [`reliability_ai/investigation/tools.py`](../../src/hmda_reliability/reliability_ai/investigation/tools.py)
  - `ToolRegistry.__init__`, `ToolRegistry.execute`
- [`reliability_ai/context.py`](../../src/hmda_reliability/reliability_ai/context.py)
  - `project_remote_output`, `_project_public_value`
- [`reliability_ai/investigation/service.py`](../../src/hmda_reliability/reliability_ai/investigation/service.py)
  - `record, tool_output = registry.execute(call)`

#### Evidence

`ToolRegistry`는 trusted caller가 제공하는 `profile_comparison_handler`와 `impact_handler`의 반환값을 `dict[str, Any]`로 받는다. 투영 함수는 문자열·dict·list 이외 객체를 그대로 통과시키고, `ToolCallRecord.result`도 `Any` 값을 허용한다. 예를 들어 handler가 `{"observed_at": datetime.now(UTC)}`를 반환하면 `ToolRegistry.execute`의 `try/except Exception`을 **성공으로 통과한 뒤**, 그 바깥의 `json.dumps(result, ensure_ascii=False)`에서 `TypeError`가 발생한다. 조사 루프는 이 예외를 정규화하지 않아 `finish()` 및 최종 manifest 기록에 도달하지 못한다.

이 경로는 **명시적으로 주입한 custom handler**에만 해당한다. 현재 기본 `from_review_input` handler의 정상 출력에서 같은 결함이 발생한다고 확인한 것은 아니다.

#### Impact

호출자에게 구조화된 `InvestigationResult(error)`가 아니라 예외가 이탈한다. 이미 저장한 provider 응답 파일이 있더라도 tool 실패 정보와 최종 manifest가 누락되어 failure provenance와 후속 진단이 어려워진다.

#### Action

handler 결과를 **success로 표시하기 전에** JSON 직렬화 가능 여부를 확인하고, 실패 시 `tool_execution_failed` 형식의 오류 결과·`ToolCallRecord(status="error")`로 전환한다. `datetime` 등 직렬화 불가능한 값을 반환하는 custom handler 경로에 focused 회귀 테스트를 추가한다. 신뢰된 handler라는 전제는 권한에 관한 것이며 반환값 직렬화 성공을 보장하지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 현재 head 및 base 식별 | GitHub PR 메타데이터에서 base `f1de6256`, head `860fbcae`, 변경 파일 166개를 확인 |
| ✅ Pass | 코드 경로·계약 대조 | `runtime_ai/provider.py`, `reliability_ai/investigation/{service,tools}.py`, `context.py`, `execution/service.py`, OpenSpec의 도구 대응·실패 기록 계약을 정적 추적 |
| ✅ Pass | 승인/복구 경계 한정 확인 | `execute_delegated_task`가 별도의 approved request·Task allowlist·사건 binding 이후 기존 deterministic executor를 호출함을 확인; 이 범위에서 무승인 복구 경로는 확인되지 않음 |
| ✅ Pass | 기존 회귀 테스트와 반례 대조 | `tests/runtime_ai/test_provider_tools.py`, `tests/reliability_ai/test_investigation_agent.py`, `test_investigation_tools.py`에서 관련 기존 safeguard를 검토 |
| ⚪ Not Verified | 재현 테스트 실행 | 원격 저장소 소스만 정적으로 검토했다. SDK 실제 응답 모킹·pytest·ruff·tach를 이번 리뷰에서 실행하지 않음 |
| ⚪ Not Verified | 전체 PR 전수 검토와 별도 독립 리뷰 | 166개 파일의 모든 실행 경로를 전수 검증하지 않았으며, 이 실행 환경에서 VS Code 전용 DualVantage 독립 서브에이전트를 호출하지 못함 |
| ⚪ Not Verified | 최신 실제 모델 품질·인간 평가 | 기존 [self-review](10-report-reliability-agentic-merge-readiness-self-review.md)에 보고된 CI(1,196 passed / 1 skipped)·기존 독립 리뷰를 참고했지만 직접 재실행하거나 인간 평가를 대신하지 않음 |

## Risks and Limits

- **Disposition** — F1은 PR이 새로 추가한 provider/tool 역사 계약에 직접 연결된 `current_required` (`contract_dependency`), F2는 선택적 주입형 handler의 실패 기록 계약에 연결된 `current_required` (`direct_regression`)로 판단한다. F1 해결 전에는 merge 승인 근거로 이 리뷰를 사용할 수 없다.
- **Evidence strength** — 두 finding 모두 실제 repo 코드를 통한 **정적·논리적 경로 추적(reasoned)**이다. 이번 세션에서 테스트를 재현한 `observed` 결과로 표현하지 않는다. 반례 테스트가 기존 guard를 입증하면 finding을 재판정한다.
- **Review boundary** — 초기 모델 조사 결과의 `completed`는 구조·로컬 기록 완료일 뿐 사실성·유용성·복구 승인으로 해석하지 않는다. 정본 명세와 별도로 인간 평가가 남아 있으며, 이 문서는 GitHub 승인·merge 결정이 아니다.
- **Re-review trigger** — F1/F2 수정 후 provider→조사→manifest의 실패 테스트와 관련 CI를 새 코드 revision에서 확인하고, 이 리뷰의 판단을 갱신해야 한다.
