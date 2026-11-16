---
type: report
title: "Reliability AI Provider Tool-Call Contract Remediation Report"
description: "PR #284의 멀티 에이전트 아키텍처 리뷰에서 확인된 runtime_ai와 reliability_ai 간 비정상 도구 호출 누락 결함 보완, SDK 연결 회귀 검증 및 DualVantage 독립 리뷰 완료 근거를 정리한다."
tags:
  - reliability-ai
  - runtime-ai
  - architecture
  - testing
---

# Reliability AI Provider Tool-Call Contract Remediation Report

## Summary

**`runtime_ai`와 `reliability_ai` 경계에서 비정상 도구 호출이 조용히 버려져 성공 보고로 오인되던 공유 계약 결함을 수정하고, 2차 독립 리뷰(`mols-review-dualvantage`)에서 `clear`(확정 결함 0건, 미해결 항목 0건) 판정을 받았다.** 전체 non-resource 테스트는 1,196 passed / 1 skipped, AI·Runtime 스위트는 232 passed이며 정적 검사(`ruff`, `ty`, `tach`)와 wheel 빌드, OpenSpec Task 4 재검증(`7/7 all_done`)을 모두 통과했다.

이 문서는 [08 Work Completion Report](08-report-reliability-agentic-work-completion.md)(원격 HEAD `84b92c4a7e0abbecf1d1ecf5beeca54efad37c3a`) 이후 수행한 후속 아키텍처 평가와 공유 계약 보완 결과를 기록한 비정본 작업 보고서다. 보완 변경(8개 파일)과 이 보고서는 함께 서명 커밋으로 전달하며, 사람의 품질 평가·PR 상태 전환 판단은 별도로 남아 있다.

| Item | Verified State |
| --- | --- |
| PR | [#284: refactor: evolve reliability into agentic domains](https://github.com/mols3131d/hmda-data-reliability/pull/284), Open / Draft |
| Owning branch | `agent/refactor/evolve-reliability-agentic-architecture` |
| Baseline HEAD | `84b92c4a7e0abbecf1d1ecf5beeca54efad37c3a` |
| Change scope | 코드 5개, 테스트 2개, OpenSpec Tasks 1개, 본 작업 보고서 1개 |
| OpenSpec tracking | [Migration Tasks](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/tasks.md) Task 4 재개 후 완료 재확인 (`7/7 all_done`) |
| Independent review | 2차 `mols-review-dualvantage` 판정 `clear` (Verifier·Challenger 병렬 검증 완료, 확정 후보 0건, 미해결 후보 0건) |

## Confirmed Defect and Root Cause

`84b92c4a` 기준의 멀티 에이전트 아키텍처 독립 리뷰에서 `runtime_ai`(생산자)와 `reliability_ai.investigation`(소비자) 사이의 도구 호출 정규화 계약 불일치 1건이 확인·재현되었다.

- **조용한 도구 호출 누락 및 성공 오인**: [`_normalize_tool_calls`](../../src/hmda_reliability/runtime_ai/provider.py)가 빈 `id` 또는 빈 `function.name`을 가진 호출을 예외나 오류 상태 없이 건너뛰고 빈 튜플(`()`)을 반환했다. 응답 본문에 유효한 보고서 JSON이 함께 있으면 [`investigate_incident`](../../src/hmda_reliability/reliability_ai/investigation/service.py)는 도구 호출이 없었던 정상 최종 응답으로 해석해 `status="completed"`를 반환하고 구조화된 비정상 호출 근거를 유실했다.
- **비정제 검증 예외 유출**: 공백 문자열(`" "`) ID나 이름은 빈 문자열 검사를 통과한 뒤 Pydantic `NonEmptyStr` 검증에서 잡히지 않은 `ValidationError`를 발생시켜 로컬 응답 본문 저장 전에 호출을 중단시켰다.
- **종료 사유와 호출 목록 모순 허용**: `finish_reason == "tool_calls"`이면서 `tool_calls`가 `None`이거나 빈 배열(`[]`)인 응답도 본문 JSON만 유효하면 `completed`로 채택되었다.

## Implemented Remediation

기존 아키텍처 경계와 외부 결정론적 Approval·Recovery 권한은 그대로 유지하고, 공유 응답 계약과 조사 소비 경로만 최소 범위로 보완했다.

| Surface | File | Contract and Behavior Change |
| --- | --- | --- |
| Runtime 응답 계약 | [`src/hmda_reliability/runtime_ai/contracts.py`](../../src/hmda_reliability/runtime_ai/contracts.py) | `ProviderResponseMetadata.content_state`에 `"invalid_tool_calls"`를 추가하고 `TransportResponse`·`ProviderResponse`에 선택적 `raw_tool_calls: str \| None = None` 필드를 추가했다. |
| SDK 정규화·원문 보존·바이트 상한 | [`src/hmda_reliability/runtime_ai/provider.py`](../../src/hmda_reliability/runtime_ai/provider.py) | `_normalize_tool_calls`가 `type != "function"`, 비문자열 `id`/`name`/`arguments`, 빈·공백 식별자를 모두 `ValueError`로 거부한다. `finish_reason == "tool_calls"`인데 정규화된 호출이 없는 경우도 동일하게 거부한다. 배치 중 하나라도 비정상이면 전체 배치를 거부하고, `completions.with_raw_response.create` 및 `raw_response.parse(to=ChatCompletion)`을 통해 동일 HTTP 응답의 `raw_response.http_response.json()`에서 원래 `tool_calls` JSON 문자열을 추출해 보존한다. `raw_tool_calls` 바이트는 `max_output_bytes` 상한 검사에 합산하며 재시도는 수행하지 않는다. |
| 조사 턴 계약·실패 종결 | [`src/hmda_reliability/reliability_ai/investigation/contracts.py`](../../src/hmda_reliability/reliability_ai/investigation/contracts.py), [`src/hmda_reliability/reliability_ai/investigation/service.py`](../../src/hmda_reliability/reliability_ai/investigation/service.py) | `InvestigationTurnRecord`에 `raw_tool_calls`를 기록한다. 비정상 도구 호출 응답은 로컬 응답 원문 파일(`store.write`)과 실패 manifest를 먼저 저장하고 세대 관측을 `ERROR`(`invalid_provider_tool_calls`)로 갱신한 뒤, 도구 실행이나 보고서 파싱으로 진입하지 않고 즉시 `finish("error", "invalid_provider_tool_calls")`로 종료한다. |
| 원격 출력 정제 | [`src/hmda_reliability/reliability_ai/context.py`](../../src/hmda_reliability/reliability_ai/context.py) | `_PRIVATE_FIELDS`에 `"raw_tool_calls"`를 추가해 `project_remote_output` 경유 시 원격 관측·실험 출력에서 비정상 호출 원문을 재귀적으로 제외한다. |

### Resolution of First Review Candidate (C1)

1차 독립 리뷰에서는 초기 수정안이 `choice.message.model_dump(mode="json", warnings=False)`로 비정상 호출 원문을 재직렬화할 때, 약 300단계 깊이의 비문자열 `function.arguments`에서 Pydantic serializer 깊이 한도(`ValueError: Circular reference detected (depth exceeded)`)로 인해 로컬 본문 저장 전에 예외가 이탈할 수 있다는 미확인 후보(C1)를 제기했다.

이를 실제 SDK + `httpx.MockTransport` 테스트로 재현해 RED를 확인한 뒤, SDK 모델 재직렬화 대신 이미 수신된 HTTP 응답 본문(`raw_response.http_response.json()`)에서 `tool_calls`를 직접 추출하도록 수정해 깊이 300 중첩 인자에서도 본문과 호출 원문이 손실 없이 보존됨을 검증했다.

## Verification and Independent Review

| Check | Command / Scope | Result |
| --- | --- | --- |
| SDK→조사 경계 회귀 | [`tests/reliability_ai/test_investigation_agent.py`](../../tests/reliability_ai/test_investigation_agent.py) (`test_invalid_sdk_tool_calls_fail_without_losing_response`, `test_sdk_tool_completion_requires_calls_before_accepting_report`) | **18 passed**. 빈·공백 ID/이름, `None`/`{}`/깊이 300 배열 인자, 미지원 타입의 단독·혼합 배치 16건과 `None`/`[]` 호출 종료 2건에서 RED → GREEN 확인. 요청 1회, 도구 실행 0회, 로컬 본문·`raw_tool_calls` 보존 및 원격 제외 검증. |
| 출력 바이트 상한 회귀 | [`tests/runtime_ai/test_provider_tools.py`](../../tests/runtime_ai/test_provider_tools.py) (`test_invalid_raw_tool_calls_count_toward_output_byte_cap`) | **1 passed**. `content` + `raw_tool_calls` 합산 바이트가 `max_output_bytes`를 초과할 때 재시도 없이 `ProviderResponseTooLargeError` 발생 확인. |
| AI·Runtime 전체 스위트 | `uv run --no-sync pytest tests/reliability_ai tests/runtime_ai -n auto -q --tb=short` | **232 passed** (8.40s). |
| 전체 non-resource 스위트 | `env TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" uv run --no-sync pytest -n auto -q --tb=short` | **1,196 passed, 1 skipped** (Windows 전용 경계 1건 skip, 실패·오류 0건). |
| 정적 분석·경계·빌드 | `ruff check`, `ruff format --check`, `ty check`, `tach check`, `uv build --no-sources --wheel` | 모두 통과. `parse(to=ChatCompletion)` 명시로 프로젝트 전체 `ty check` 진단 0건 확인. |
| OpenSpec·Markdown | `openspec validate reliability-agentic-review-enable-bounded-tools --strict`, `rumdl check` | 통과. Task 4 완료 조건 보강 및 `7/7 all_done` 상태 확인. |
| 2차 독립 리뷰 | `mols-review-dualvantage` (Verifier + Challenger 병렬 실행) | **`clear`**. 확정 후보 0건, 미해결 항목 0건. Verifier가 격리 환경에서 관련 테스트 107건과 `ruff`·`ty`·`tach` 통과를 독립 확인했다. |

## Remaining Actions and Boundaries

1. **PR #284 본문 갱신 및 상태 전환**: 원격 PR 본문은 초기 문서 단계 설명이 남아 있으므로 최신 구현·검증 상태로 갱신이 필요하다. Ready 전환과 병합은 원격 CI 통과 및 사람 검토 후 별도 지시에 따라 수행한다.
1. **제품 모델 품질 및 인간 평가**: 이번 수정은 오프라인 단위·통합 테스트(`httpx.MockTransport` + 실제 `OpenAI` SDK)와 정적 검증으로 증명했다. 라이브 LLM 재실행과 [Human Evaluation](../../docs/development/review-ai-evaluation.md#human-evaluation)의 5개 기준 인간 평가는 별도 운영 절차로 남아 있다.
