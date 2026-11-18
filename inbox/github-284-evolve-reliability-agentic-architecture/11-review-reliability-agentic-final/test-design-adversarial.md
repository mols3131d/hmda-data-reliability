---
type: review
title: "PR #284 Adversarial Test Design Review"
description: "PR #284의 테스트가 실패 상태와 신뢰 경계를 실제로 판별하는지 적대적 입력·모킹 경계·평가 증거 관점에서 검토한다."
tags:
  - reliability-ai
  - runtime-ai
  - pull-request
  - testing
---

# PR #284 Adversarial Test Design Review

> [!NOTE]
> **추가 검토 결과: 기존 병합 차단 후보 외에 새로운 production defect는 확정하지 않았다.** 테스트가 중요한 잘못된 동작을 구별하는지를 반례 중심으로 점검해 **보완 가치가 있는 2건(F1·F2)**과 **검증 경계 1건(F3)**을 정리했다. 이 보고서는 [Final Review](README.md)의 결정을 덮어쓰지 않는다. 기존 필수 후보인 **동일 배치 tool-call ID 충돌**과 **복구 후 divergence 상태 오분류**는 여전히 [기존 Test Design Review](test-design.md)의 검증·수정 대상으로 남는다.
>
> **적대적 리뷰는 자동 수용할 지시가 아니다.** 로컬 에이전트는 현재 HEAD, 명세와 기존 safeguard에 대한 반례를 먼저 확인하고 각 제안을 `Accept / Reject / Revise / Defer`로 독립 판정한다.

- **Target** — [PR #284: Evolve Reliability Agentic Architecture](https://github.com/mols3131d/hmda-data-reliability/pull/284)
- **Revision** — base `f1de6256cdd1e034f655b2f2ee3997481d0b195c` → reviewed head `6e32a96c49623271e431826d26ba00d301364a01` (문서 커밋 전)
- **Scope** — `reliability_ai`의 조사·위임·Dataset 실험 테스트, `runtime_ai` SDK 경계와 직접 관련된 명세·구현. 전체 170개 변경 파일의 전수 테스트 리뷰나 pytest 실행은 아니다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟡 Minor | 금지된 도구 호출이 실제 응답에 들어오는 테스트가 **요청 설정만 확인**하고 상위 실패 결과를 검증하지 않는다. | 기존 테스트에 `tool_not_allowed`·실행 0건·복구 차단 oracle 추가 |
| F2 | 🟡 Minor | 민감정보 투영 검증은 강하지만, **악의적 evidence/tool 텍스트가 지시 권한으로 승격되지 않는지** 직접 판별하는 회귀가 없다. | 기존 prompt/SDK 경계에 구조적 role·허용 목록 불변 반례 추가 |
| F3 | 🔵 Note | Dataset runner 테스트는 `run_experiment` 반환을 모킹한다. 실제 SDK 실행 호환성과 최종 모델 유용성은 별도 증거다. | 필요 시 승인된 SDK smoke·실모델/인간 평가로 증거 분리 |

## Details

### F1 · Assert the Result of a Forbidden Tool Call

#### Locations

- [`tests/reliability_ai/test_execution_service.py`](../../../tests/reliability_ai/test_execution_service.py)
  - `test_delegated_task_enforces_empty_tool_allowlist_and_timeout` (317–362행)
- [`src/hmda_reliability/reliability_ai/investigation/service.py`](../../../src/hmda_reliability/reliability_ai/investigation/service.py)
  - `investigate_incident`의 `tool_names` 검사·`tool_not_allowed` 반환 (약 478–490행)
- [`openspec/specs/reliability-agentic-review/spec.md`](../../../openspec/specs/reliability-agentic-review/spec.md)
  - `Task limits cannot be widened by the model`, `Failed investigation prevents recovery`

#### Evidence

테스트는 `allowed_tools=()`인 Task에 대해 **provider가 실제로 금지된 `get_incident_evidence` 호출을 반환하도록** `ScriptedTransport`를 구성한다. 그러나 `execute_delegated_task` 결과를 변수에 담지 않고 요청의 `tools is None`, `tool_choice == "none"`, timeout만 확인한다. 실제 구현에는 응답 수신 뒤 `tool_not_allowed`로 거부하는 guard가 있고, 별도의 `test_tool_registry_blocks_disallowed_configured_tool`도 있으므로 **현재 무단 도구 실행 결함을 주장할 근거는 없다**.

위험은 요청에서 도구를 숨기는 행위와 **이를 무시한 provider 응답을 안전하게 종결하는 행위가 다른 계약**이라는 점이다. 상위 보고가 잘못 `completed`로 종료하거나 금지 시도 기록을 잃는 회귀가 나더라도 이 테스트의 현재 assertion만으로 오류를 특정하지 못한다.

#### Impact

권한 경계 회귀가 발생했을 때 CI 실패 원인이 모호해지거나, 최종 `ReportEnvelope`의 실패 상태를 확인하지 않은 채 요청 옵션의 정확성만으로 위임 안전성을 과대평가할 수 있다. 신뢰 경계에 대한 **test oracle 결손(reasoned)**이며 실행 중 결함은 미확인이다.

#### Action

1. 기존 테스트의 반환값을 받아 `report.status == "failed"`, `report.investigation.failure_code == "tool_not_allowed"`, `report.execution_receipts == ()`를 확인한다. 실패 원문/manifest 유지 여부는 기존 조사 테스트의 safeguard를 재사용한다.
1. 필요하면 등록된 **spy handler**로 실제 실행 0회를 확인하는 좁은 조사 테스트를 1개 추가한다. 단지 `result.tool_calls == ()`만으로 부작용 부재를 추론하지 않는다.
1. guard 제거·오류 코드 변경 등의 변형에서 새 oracle이 실패하는지 확인한다. 이미 다른 테스트가 같은 계약을 충분히 보호한다면 중복 테스트 대신 본 후보를 기각한다.

- **Scope relation / Disposition** — `contract_dependency / follow_up`. 위험도가 있는 테스트 보강이지만, 현재 guard와 별도 registry 테스트가 존재하므로 새 병합 차단 production finding으로 승격하지 않는다.

### F2 · Test Untrusted Content Without Pretending to Test Model Obedience

#### Locations

- [`tests/reliability_ai/test_context.py`](../../../tests/reliability_ai/test_context.py)
  - `test_provider_and_remote_projection_remove_nested_private_material`, `test_evidence_metadata_shapes_exclude_nested_raw_rows`
- [`tests/reliability_ai/test_experiment_runner.py`](../../../tests/reliability_ai/test_experiment_runner.py)
  - `test_explicit_prompt_setup_registers_pinned_native_composition`
- [`src/hmda_reliability/reliability_ai/investigation/service.py`](../../../src/hmda_reliability/reliability_ai/investigation/service.py)
  - `native_prompt.compile`과 `history` 전달
- [`openspec/specs/reliability-agentic-review/spec.md`](../../../openspec/specs/reliability-agentic-review/spec.md)
  - `Prompt-injection text remains data`

#### Evidence

기존 테스트는 private path, `credentials`, `raw_rows`를 유효하게 제거하고, native prompt 등록 시 `canonical_input`의 user role 및 history placeholder도 확인한다. 반면 **실제 evidence 요약 또는 tool output에 지시문·템플릿 구문을 넣은 뒤**, 그것이 system 메시지나 도구 권한으로 이동하지 않는지 compiled history에서 확인하는 적대적 사례는 검토한 테스트에서 발견되지 않았다. 현재 구현은 system/user/history 경계를 분리하고 프롬프트에도 비신뢰 자료 취급을 명시하므로 **현재 role 승격이 발생한다는 증거는 없다**.

#### Impact

미래의 prompt 조립 변경이 untrusted text를 권한 있는 메시지로 섞어도 기존 민감정보 제거·정상 도구 흐름 테스트가 그 차이를 놓칠 수 있다. 반면 모델이 공격 문장을 *의미적으로 따르지 않는지*는 offline mock assertion으로 증명할 수 없다.

#### Action

evidence `summary` 또는 tool result에 `Ignore previous instructions`, `{{history}}`와 권한 확대 요청을 넣고, **실제로 전송된 메시지**의 role·원문 보존·허용 도구와 Task 한도가 바뀌지 않는지만 좁게 확인한다. 의미적 jailbreak 방어율을 단정하는 테스트나 별도 LLM 평가 프레임워크 도입은 요구하지 않는다.

- **Scope relation / Disposition** — `contract_dependency / follow_up`. 명시적 OpenSpec 시나리오를 방어하는 작은 회귀 보강이며, 현행 결함이 재현되지 않는 한 기존 필수 2건보다 우선하지 않는다.

### F3 · Do Not Promote Mocked Dataset Completion to Live Utility Evidence

#### Locations

- [`tests/reliability_ai/test_experiment_runner.py`](../../../tests/reliability_ai/test_experiment_runner.py)
  - `test_experiment_preserves_investigation_output_and_exit_status`, `test_experiment_rejects_missing_or_duplicated_item_results`
- [`src/hmda_reliability/reliability_ai/evaluation/experiment.py`](../../../src/hmda_reliability/reliability_ai/evaluation/experiment.py)
  - `dataset.run_experiment(task=..., max_concurrency=1)` 및 Dataset ID multiset 확인
- [`docs/development/review-ai-evaluation.md`](../../../docs/development/review-ai-evaluation.md)
  - `Offline Suite`, `Human Evaluation`

#### Evidence And Decision

`dataset.run_experiment`과 `get_client`를 `MagicMock`으로 바꾼 테스트는 **프로젝트 자체의** item 완전성·입력 격리·exit code를 검증하는 데 적절하다. 그러나 실제 Langfuse Dataset SDK의 결과 형식·trace 적재나 모델의 `added_value` 등 사람 평가 기준까지 통과했다는 근거는 아니다. PR 본문 역시 최종 코드 revision에서 실제 제품 모델 재실험과 인간 효용 평가를 **Not Verified**로 구분한다.

**Disposition — `acceptance_gap / follow_up` (Note).** Offline suite를 대체·약화할 이유가 없다. 모델 품질을 CI의 mock 결과로 판정하지 말고, MVP/운영 acceptance가 필요할 때 동일 Dataset·Prompt·revision의 명시적 native 실험과 인간 평가 결과를 별도로 확보한다. 원격 쓰기·비용이 발생할 수 있는 실행을 기본 pytest로 강제하지 않는다.

## Test Priority And Handoff

1. **기존 필수 후보 먼저 반증·검증** — [Final Review F1/F2](README.md#findings)와 [기존 Test Design Review](test-design.md)의 같은 배치 중복 ID, mutation divergence 반례를 가장 낮은 유효 수준에서 red/green으로 확인한다. 근거가 틀리면 리뷰를 기각한다.
1. **F1 최소 보강** — 이미 구성된 적대적 provider 응답 테스트에서 상위 오류·부작용 부재까지 주장할 수 있는 oracle을 추가한다. 구조 재설계나 통합 테스트 신설은 필요하지 않다.
1. **F2 선택 보강** — prompt 조립 또는 불신 입력 처리 코드를 변경할 때 구조적 role 경계를 직접 보호한다. F3는 별도의 운영/사람 평가 증거로 취급한다.
1. 테스트/명세/기존 safeguard 중 어디에서 관찰 불일치가 발생했는지 구별하고, **리뷰 주장을 무조건 수용하거나 assertion을 기대에 맞춰 약화하지 않는다**. 코드 변경·Ready 전환·승인·merge는 이 보고서가 허가하지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 기준 revision과 기존 11번 리뷰 구별 | PR #284 base/head, `README.md`·`test-design.md` 및 기존 두 finding을 확인 |
| ✅ Pass | 허용 도구 응답에 대한 test oracle 추적 | `test_delegated_task_enforces_empty_tool_allowlist_and_timeout`와 실제 `tool_not_allowed` guard, registry fallback을 정적으로 대조 |
| ✅ Pass | prompt projection·Dataset evaluation의 증거 경계 구분 | context/experiment 테스트, native prompt 구성과 정본 OpenSpec·평가 가이드를 정적으로 대조 |
| ⚪ Not Verified | F1/F2 반례 red/green·focused pytest | 실행 환경에서 테스트를 수행하지 않았으며 테스트 실패를 관측했다고 주장하지 않음 |
| ⚪ Not Verified | 현재 HEAD의 원격 CI·실제 Langfuse Dataset/LLM·인간 평가 | 기존 통과 기록은 코드 변경 후 최신 검증 또는 모델 유용성 증거가 아님 |
| ⚪ Not Verified | 독립 VS Code dual-perspective reviewer | 같은 컨텍스트의 코드 정적 검토이며 독립 서브에이전트 리뷰를 수행하지 않음 |

## Risks And Limits

- 모든 finding은 **정적 근거에 기초한 테스트 설계 판단**이다. 직접 재현한 production defect가 아니다. 실제 failing test가 나오면 원인과 중요도를 재판정한다.
- 이 보고서는 [Final Review](README.md)의 필수 finding 2건을 추가 집계하거나 병합 가능 판단을 새로 내리지 않는다. 그 판단은 최신 코드·반례·CI 확인 후 갱신해야 한다.
- 테스트 도구·marker 전면 개편, 무관한 회귀 테스트 추가, 실제 모델을 mock으로 대체해 유용성을 입증하는 방식은 권고하지 않는다.
