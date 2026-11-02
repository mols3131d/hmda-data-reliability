---
type: research
title: Review AI Response Failure Investigation
description: 저장된 live invocation과 응답 처리 코드를 대조해 실패 원인의 식별 가능성과 다음 진단 범위를 판단한다.
tags:
  - domain:review-ai
  - capability:live-proof
---

# Review AI Response Failure Investigation

> [!NOTE]
> 이번 실패는 provider 응답 수신 후 JSON 파싱 또는 응답 계약 검증에서 발생했다. 원시 응답과 상세 오류가 보존되지 않았으므로 정확한 위반 필드는 복원할 수 없다. 확인된 문제는 서로 다른 오류를 하나의 코드로 합치고 진단 정보를 남기지 않는 경로이며, 특정 모델 응답 결함은 아직 확인되지 않았다.

## Question

Invocation `ar-20261002-975b6bdd2b7a`의 `response_schema_invalid`는 무엇을 증명하며, 정확한 응답 실패 원인을 기존 근거에서 특정할 수 있는가?

## Scope

- [기존 실행 보고서](17-59-report-review-ai-live-run-failure.md), 로컬 invocation evidence(`.local/artifacts/agentic-review/invocations/ar-20261002-975b6bdd2b7a.json`), Review AI 파서·계약·프롬프트, Runtime AI 요청 형식을 조사했다.
- 실행 기록의 리비전 `2c3b61cd021267649f1cbc76f1c149abf93598f9`의 파서와 provider 요청 코드도 대조했다.
- 외부 호출 없는 로컬 파서 확인만 실행했다. 모델 재호출, 키 조회, Langfuse 전송, 애플리케이션·테스트·설정 수정은 하지 않았다.
- 키 교체 완료는 2026-10-02 사용자 확인에 따른 사실이다. 새 키 인증이나 Cloud ingestion 성공을 뜻하지 않는다.

## Findings

### Failure Occurred Before Deterministic Review Validation

저장된 결과는 `validation_failed`, failure code는 `response_schema_invalid`이며 `parsed_output`과 `validation`은 모두 `null`이다. Provider 응답 메타데이터에는 약 17.5초의 지연, prompt 1,046개·completion 519개 토큰, attempt 1회가 기록돼 있다.

[service.py](../../src/hmda_reliability/review_ai/service.py)의 `review_null_spike`는 provider 호출 후 `_parse_output`이 `None`이면 해당 실패를 저장하고 즉시 반환한다. 따라서 사실 대조·근거 참조 검증을 담당하는 `validate_agentic_review`에 도달하지 않았다. 이것은 timeout, 연결 실패 또는 출력 바이트 초과로 기록된 실행이 아니다.

### Failure Code Does Not Identify The Error Category

같은 파일의 `_parse_output`은 `json.loads(content)`와 `AgenticReviewOutput.model_validate(payload)`를 연속 실행하고 `JSONDecodeError`, `TypeError`, `ValidationError`를 모두 `None`으로 바꾼다. 실행 리비전의 코드에서도 같은 처리를 확인했다.

로컬 Python 3.13 환경에서 실제 파서를 호출해 다음을 확인했다. 아래 입력은 진단용 구성 예시이며 실패한 모델의 실제 응답이 아니다.

| Diagnostic Input | Observation |
| --- | --- |
| `not-json` | `_parse_output`이 `None` 반환 |
| `{}` | 유효한 JSON이지만 `_parse_output`이 `None` 반환 |
| `{}`를 계약에 직접 검증 | Pydantic 오류 유형은 `missing` |

따라서 failure code만으로 JSON 구문 문제와 필수 필드·타입·enum·제약 위반을 구분할 수 없다. [기존 서비스 테스트](../../tests/review_ai/test_service.py)의 `test_schema_and_guard_failures_are_persisted_without_exposing_output`도 비JSON 응답을 같은 코드로 처리하는 사례를 포함한다. 이번 조사에서 해당 pytest는 실행하지 않았다.

### Original Response Cannot Be Recovered From The Invocation

[evidence.py](../../src/hmda_reliability/review_ai/evidence.py)의 `AgenticInvocationEvidence`에는 원시 응답이나 파싱 예외 상세를 저장하는 필드가 없다. 서비스의 스키마 실패 분기도 응답 내용과 오류 위치를 기록하지 않는다. Artifact 모델 검증은 통과했으므로 `null`은 artifact 자체의 형식 손상 증거가 아니라 이 실패 경로와 일치하는 저장 결과다.

따라서 기존 보고서의 “`parsed_output`을 스키마와 대조” 조치는 이 invocation에 적용할 수 없다. 원시 응답이 별도 위치에 보존됐는지는 이번 범위에서 확인하지 않았으며, 기존 artifact만으로 특정 필드 누락이나 잘못된 enum을 주장할 수 없다.

### JSON Object Mode Does Not Enforce The Review Contract

[provider.py](../../src/hmda_reliability/runtime_ai/provider.py)의 `_OpenAIChatCompletionTransport.create`는 `response_format={"type": "json_object"}`, `temperature=0`, `max_tokens=1024`로 요청한다. 실행 리비전에서도 JSON object 설정을 확인했다. 요청에는 `AgenticReviewOutput`의 JSON Schema가 전달되지 않는다.

[prompt/](../../src/hmda_reliability/review_ai/prompt/)는 응답 필드와 enum을 자연어로 지시하고, [contracts.py](../../src/hmda_reliability/review_ai/contracts.py)는 필수 필드·문자열·배열 한도와 `investigation_priority`의 priority 조건 등을 검증한다. JSON object를 요청했다는 사실만으로 이 계약 준수를 증명할 수 없다.

저장된 `canonical_input`과 prompt identity를 현재 렌더러에 넣어 재계산한 `prompt_digest`는 원본과 일치했다. 현재 프롬프트로 실행 입력을 재구성할 근거는 있지만, 동일 모델을 다시 호출해 동일 응답이 나온다고 보장하지는 않는다. 토큰 부족, 코드 fence, 필드 누락, enum 오류 등은 가능한 가설일 뿐 관찰된 원인이 아니다. Transport는 `finish_reason`도 보존하지 않아 종료 사유를 사후 확인할 수 없다.

### Failed Invocation Supports Metadata-Only Projection

[langfuse.py](../../src/hmda_reliability/review_ai/evaluation/langfuse.py)의 `project_invocation`은 `validation_failed`와 `unavailable`에 invocation ID·revision·status만 담는 projection을 허용한다. `accepted`일 때만 입력·출력과 상세 메타데이터를 추가한다.

따라서 실패 invocation 전체가 projection 대상이 아니라는 기존 설명은 부정확하다. 이번 실행의 미전송 이유는 `HMDA_LANGFUSE_EXPORT=false`이며, accepted output이 없어 전체 입출력 projection을 만들 수 없다는 것은 별개의 사실이다. 기존 보고서도 이에 맞게 정정했다.

## Implications

다음 진단은 실패 응답을 계약과 비교할 수 있는 최소 정보부터 확보해야 한다. JSON 파싱 오류와 계약 검증 오류를 구분하고, 입력 값 없이 오류 유형과 필드 경로를 제한적으로 남기는 방법이 원시 응답 전문 저장보다 정보 노출을 줄일 수 있다. JSON Schema 전달이나 프롬프트 수정은 실제 위반 유형을 확인한 뒤 판단하는 것이 타당하다. 이는 구현 확정안이 아니라 후속 판단을 위한 제안이다.

재실행 시 provider 경로만 먼저 확인하고, 성공 판단은 `accepted` 및 결정론적 검증 결과로 한다. 이후 별도 Cloud 검증에서 실패 메타데이터 전송과 accepted 입출력 전송을 구분해야 한다. 절차의 정본은 [Review AI Evaluation guide](../../docs/development/review-ai-evaluation.md)를 따른다.

## Open Questions

- 실제 응답은 JSON 구문 오류였는가, 계약 위반이었는가? 다음 제한된 진단 실행의 오류 분류가 필요하다.
- JSON Schema 기반 요청을 이 provider·모델 조합에서 지원하며 계약 준수에 도움이 되는가? 이번에는 provider 기능 확인이나 비교 실행을 하지 않았다.
- 새로운 키로 Cloud 저장이 성공하는가? 사용자 확인은 키 교체까지이며 외부 검증은 수행하지 않았다.
