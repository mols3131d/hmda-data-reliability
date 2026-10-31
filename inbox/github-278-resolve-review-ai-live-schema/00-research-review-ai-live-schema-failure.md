---
type: research
title: Review AI live schema failure investigation and test design
description: 여러 로컬 모델의 Review AI live failure를 비교하고 원인 경계와 재현 가능한 검증 범위를 정하기 위한 조사
tags:
  - review-ai
  - runtime-ai
  - testing
---

# Review AI Live Schema Failure

> **Current answer:** `response_schema_invalid`는 Qwen3.5 이전의 `qwen2.5-coder:7b`에서도 기록됐다. Qwen3.5만의 문제로 볼 근거가 없다. 별도 Qwen3.5 진단 재생에서는 유효한 JSON이 출력 계약에서 거부됐다. 모델 출력만의 문제로도 단정할 수 없다. 현재 프롬프트의 타입 설명, provider 요청과 완료 상태 처리, 파싱 진단 및 로컬 실행 설정도 **코드 또는 통합 경계의 원인 후보**다. 같은 실패 코드가 같은 근본 원인을 뜻하는지는 아래의 독립적인 단계별 테스트와 새 revision의 opt-in live 실행으로 확인해야 한다.

## Question

RTX 3070에서 Qwen3.5를 재시도하는 과정에서 확인한 모델 간 `response_schema_invalid`는 어느 경계에서 발생하며, 출력 계약과 fail-closed 안전성을 유지하면서 어떻게 재현·수정·검증할 수 있는가?

## Scope

- 대상은 합성 `null_spike` 입력을 사용하는 Review AI의 입력 투영 → 프롬프트 → OpenAI 호환 호출 → 응답 파싱 → 결정론적 검증 → 증적 저장 경로다.
- Qwen3.5 호출과 일부 `qwen2.5-coder:7b` 호출은 `9f891e5f19137144f56d1857a8e438770e2a974c`에서 수행됐고, 더 이전의 `qwen2.5-coder:7b` 호출은 별도 revision에 속한다. 이 문서가 출발한 PR base는 `b47fe3b8fba21354a4f4686e881120d9df421410`이다. 과거 결과는 현재 base 또는 앞으로의 PR head에 대한 live 성공·실패 증거가 아니다.
- 로컬 `.env`, 원시 모델 응답 및 자격 증명은 PR에 포함하지 않는다. Langfuse 원격 수집과 사람의 utility 평가는 별도 증명 경계다.

## Findings

### Cross-model live failures and a narrower diagnostic replay

2026-10-28 확인한 로컬의 정제된 invocation evidence 9건 모두 `validation_failed`와 `response_schema_invalid`를 기록한다. 이 중 6건은 `qwen2.5-coder:7b`, 2건은 `qwen3.5:4b`, 1건은 같은 Qwen3.5 모델의 8k 로컬 변형이다. 아래는 revision 차이를 보여주는 대표 기록이다. JSON 파일은 무시된 로컬 artifact여서 PR 검토자가 원격 저장소에서 열 수 없다. 아래 값은 조사 출발점이며, 새 head에서 재확인이 필요하다.

| Local invocation ID | Model | Revision | Result / token usage | Interpretation |
| --- | --- | --- | --- | --- |
| `ar-20261002-975b6bdd2b7a` | `qwen2.5-coder:7b` | `2c3b61cd` | `response_schema_invalid`; prompt 1046, completion 519, total 1565 | Qwen3.5 이전에도 같은 실패 코드가 기록됐다. 정확한 출력 위반은 보존되지 않았다. |
| `ar-20261027-0e988cfdd006` | `qwen2.5-coder:7b` | `9f891e5f` | 같은 실패; prompt 1046, completion 519, total 1565 | Qwen3.5 실행과 같은 코드 revision에서도 실패했다. |
| `ar-20261027-6163df6c79fe` | `qwen3.5:4b` | `9f891e5f` | 같은 실패; prompt 1048, completion 3048, total 4096 | 4096 context 한계와 정확히 같아 잘림 가능성이 있다. 원인 확정은 아니다. |
| `ar-20261027-104158d626c5` | `qwen3.5:4b` | `9f891e5f` | 같은 실패; prompt 1048, completion 3048, total 4096 | Langfuse child 제출은 `submitted_unverified`였으며 원격 수집 증명은 아니다. |
| `ar-20261027-bb1996302865` | `qwen3.5:4b-8k-local` | `9f891e5f` | 같은 실패; prompt 4809, completion 625, total 5434 | 8192 context에서도 실패해 4096 한계만으로는 설명되지 않는다. |

이전 [`live failure report`](../2026-10-02/17-59-report-review-ai-live-run-failure.md)와 후속 [`response failure investigation`](../2026-10-02/18-06-research-review-ai-response-failure.md)도 `qwen2.5-coder:7b` 실패를 기록한다. 후속 조사는 원시 응답이 없어 JSON 구문 오류인지 계약 위반인지 특정하지 못했다고 명시한다. 따라서 **모델 간 같은 실패 코드가 같은 출력 형태나 같은 근본 원인임은 아직 검증되지 않았다.** 사용자는 Qwen3.5 이전의 다른 모델들에서도 같은 문제를 겪었다고 보고했다. 현재 남은 로컬 invocation에서 실행 ID와 이름이 확인되는 다른 기반 모델은 `qwen2.5-coder:7b` 한 종류이며, 그 밖의 모델명과 정확한 실패 단계는 미확인이다.

동일한 canonical prompt를 사용한 별도 진단 재생에서는 JSON 문법이 유효하고 최상위 키가 존재하며 provider의 `finish_reason`이 `stop`이었다. 그러나 `uncertainties`가 배열이 아닌 문자열이었고, `evidence_gap`과 `remediation_critique`에 허용되지 않는 `priority`가 붙어 `AgenticReviewOutput` 검증에서 실패했다. 이 재생의 원시 응답은 저장하지 않았으므로, 필드별 관찰은 재현 대상으로 취급한다. 정제된 invocation evidence에는 이 세부 타입 오류가 남지 않는다.

### Current code can contribute to the failure

- [`output/compact.md`](../../src/hmda_reliability/review_ai/prompt/output/compact.md)는 `uncertainties`의 배열 형태를 명시하지 않고 `priority when applicable`이라고만 적는다. 반면 [`contracts.py`](../../src/hmda_reliability/review_ai/contracts.py)의 출력 계약은 `uncertainties`를 문자열 배열로 제한하고 `priority`를 `investigation_priority`에만 허용한다. **프롬프트와 계약 사이의 설명 부족은 코드 원인 후보**이며, 모델 준수 실패와 구분해야 한다.
- [`provider.py`](../../src/hmda_reliability/runtime_ai/provider.py)는 `response_format={"type":"json_object"}`를 보내고 SDK 응답의 `finish_reason`은 내부 응답으로 전달하지 않는다. JSON 객체 요청은 도메인 필드 타입과 조건부 `priority`를 검증하지 않는다. 완료 길이 초과 여부도 현재 증적에서 직접 판별할 수 없다. Provider-specific schema 강제가 필요한지는 호환성과 기존 계약을 함께 검토해야 한다.
- [`service.py`](../../src/hmda_reliability/review_ai/service.py)의 `_parse_output`은 JSON 문법 오류와 Pydantic 스키마 오류를 모두 `None`으로 돌려주어 동일한 `response_schema_invalid`로 기록한다. 실패를 안전하게 거부하지만, 원인 위치를 알아내기 어렵다. 상세 진단을 추가한다면 raw response나 민감 정보 없이 제한된 오류 분류만 남겨야 한다.
- [`settings.py`](../../src/hmda_reliability/runtime_ai/settings.py)의 토큰 한도와 [`review_ai/settings.py`](../../src/hmda_reliability/review_ai/settings.py)의 프롬프트 바이트 한도는 모델 context window의 토큰 예산과 별개다. 현재 설정·사전 검사가 모델별 context 부족을 미리 식별하는지는 확인되지 않았다.
- 로컬 `.env`의 기본 Review AI 모델 이름은 이전 모델로 남아 있어 Qwen3.5 재현에 명시적 모델 선택이 필요하다. 별개로 Langfuse timeout 로컬 값은 코드의 허용 상한을 초과한다. 둘 다 비밀 설정 파일에만 있는 로컬 상태이며 이 PR의 출력 스키마 원인으로 단정하지 않는다.

### Contract and existing coverage constrain the fix

정본 [`reliability-agentic-review` Spec](../../openspec/specs/reliability-agentic-review/spec.md)은 출력의 닫힌 구조, `investigation_priority`만의 `priority`, 구조적 실패의 거부, raw provider response 미저장 및 읽기 전용 경계를 요구한다. 따라서 문자열을 조용히 배열로 바꾸거나 잘못된 `priority`를 삭제해 accepted로 만드는 방식은 계약·품질 판단 없이 적용할 수 없다.

현재 [`test_prompt_provider.py`](../../tests/review_ai/test_prompt_provider.py)는 투영과 재생 가능성을, [`test_service.py`](../../tests/review_ai/test_service.py)는 비 JSON 실패와 guard 거부를, [`test_runtime_integration.py`](../../tests/review_ai/test_runtime_integration.py)는 SDK를 통한 정상 경로를 다룬다. 별도 진단 재생에서 관찰된 **유효 JSON이지만 잘못된 배열·조건부 필드**, 모델 완료 상태, 각 경계의 구별 가능한 결과는 독립적으로 검증할 필요가 있다. 이전 모델의 실패도 같은 경계별 분류로 비교해야 한다.

## Test Design

아래 시나리오는 구현 후 실제 테스트로 연결할 설계다. 각 테스트는 provider 출력을 정답으로 삼지 않고, Spec·계약에서 직접 만든 작은 고정 입력과 독립적인 기대값을 사용한다. 먼저 가장 낮은 유효 경계에서 실패를 위치시키고, 마지막에 하나의 opt-in live 경로를 확인한다.

| Boundary / level | Scenario and observable oracle | Current or proposed check |
| --- | --- | --- |
| 입력·설정 / unit | 합성 `null_spike`의 식별자·수치·Evidence ID가 고정 입력과 일치한다. 모델·출력 토큰 한도·실제 context 예산이 모순되면 호출 전에 식별하거나 명시적으로 종료한다. | 기존 입력 계약을 기준으로 모델별 예산 처리 여부를 조사하고 필요한 경우 별도 회귀 테스트 추가. |
| 프롬프트 / unit | 렌더링된 system instruction이 `uncertainties` 배열, `evidence_used`/`findings`/`utility_contributions` 배열, `investigation_priority`의 필수 `priority`와 다른 kind의 금지를 정확히 전달한다. 같은 canonical input의 digest는 재현된다. | 관찰된 세 필드 오류를 각각 겨냥한 프롬프트 계약 테스트 추가. 프롬프트 수정 시 버전별 재생 테스트 필요. |
| 전송·완료 / component | 실제 SDK와 fake HTTP 응답으로 wire의 `response_format`, 토큰 한도, `finish_reason=stop`과 `length`를 주입한다. 길이 종료가 성공 응답처럼 파싱되지 않는지, 요청·응답 진단에 secret/raw content가 없는지 확인한다. | [`test_runtime_integration.py`](../../tests/review_ai/test_runtime_integration.py)와 [`test_provider.py`](../../tests/runtime_ai/test_provider.py) 범위로 경계 테스트 설계. JSON schema 옵션은 provider 호환성 확인 후 결정. |
| JSON·출력 계약 / unit | 사람이 작성한 네 JSON fixture: 정상 배열, 문자열 `uncertainties`, 비우선 kind의 `priority`, 필수 `investigation_priority`의 `priority` 누락. 앞의 정상값만 typed output이 되고 나머지는 각각 거부된다. | 현재 [`contracts.py`](../../src/hmda_reliability/review_ai/contracts.py) 계약을 독립 oracle로 사용. 구현 자체를 호출해 기대값을 만들지 않는다. |
| 서비스·증적 / integration | 위 fixture와 잘린 JSON을 fake provider로 전달한다. status/failure와 sanitized invocation record가 일치하고 invalid 응답 본문은 노출·저장되지 않는다. 분류를 추가한다면 타입·경로만 bounded 값으로 남긴다. | [`test_service.py`](../../tests/review_ai/test_service.py)에 구조 오류와 문법 오류를 분리한 시나리오 추가. |
| 결정론적 guard / integration | 형태가 맞아도 fabricated Evidence·수치 모순은 `deterministic_guard_failed`로 남고 원래 Incident/Draft/데이터를 바꾸지 않는다. | 기존 [`test_validator.py`](../../tests/review_ai/test_validator.py)와 서비스 테스트를 새 경로에서 재확인. |
| 모델 간 opt-in live / integration | 최신 PR head에서 Langfuse를 끄고 동일한 합성 입력을 `qwen3.5:4b`와 과거 실패 모델 `qwen2.5-coder:7b`에 각각 명시적 context 설정으로 전달한다. 각 모델의 출력 계약·guard·증적 결과와 실패 단계를 따로 판정하고 invocation ID, revision, 설정, usage를 남긴다. | [`run_agentic_review_live.py`](../../scripts/run_agentic_review_live.py) 경로. 한 모델의 `accepted`나 두 모델의 같은 실패 코드만으로 공통 원인 또는 전체 해결을 주장하지 않는다. |

테스트 작성 순서는 관찰된 출력 구조를 고정 fixture로 재현 → 요청·완료 경계와 파서의 원인 분리 → 필요한 최소 코드 변경 → 전체 Review AI/Runtime AI suite → 현재 head의 opt-in live 증명이다. 테스트는 실제 network나 GPU를 기본 suite에 넣지 않는다. 라이브 결과의 유용성은 별도 사람 평가가 필요하다.

## Implications

1. 첫 구현 단계에서 같은 failure를 경계별 독립 oracle로 재현하고, 주된 원인이 프롬프트 명세 부족인지 context/완료 처리인지, 파서 진단 부족인지 분리한다. 복수 원인일 수 있다.
1. 프롬프트 문구를 바꾸면 [`PromptIdentity`](../../src/hmda_reliability/review_ai/contracts.py) `v1`의 replay digest가 달라질 수 있다. 역사적 v1 렌더링을 보존하고 새 버전 및 Spec 변경이 필요한지 결정한 뒤 수정한다.
1. fail-closed 출력 계약과 안전 경계를 유지한 수정·테스트를 같은 PR에서 이어간다. 현재 artifact 자체는 구현 완료나 새 head의 live 성공 증거가 아니다.

## Open Questions

- `finish_reason`/context 부족의 최소 provider-neutral 표현은 무엇이며, 어떤 모델별 설정 정보가 실제로 필요한가?
- 새 프롬프트 버전 또는 provider-specific JSON schema 요청이 Qwen3.5에서 충분한가? 기존 OpenAI 호환 provider의 동작도 유지되는가?
- 현재 head에서 이전 모델과 Qwen3.5의 실패가 각각 다시 재현되는가? 코드 수정 후에도 독립적으로 작성한 구조 fixture와 모델별 opt-in live 호출을 모두 통과하는가?
