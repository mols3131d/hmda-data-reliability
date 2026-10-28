---
type: proposal
title: Review AI diagnostic mode options and adoption gates
description: response_schema_invalid 조사에 필요한 로컬 진단 기능을 선별하고 안전·효용·구현 비용에 따라 채택 여부를 결정하기 위한 비정본 제안서
tags:
  - review-ai
  - runtime-ai
  - diagnostics
  - testing
---

# Review AI Diagnostic Mode Proposal

> **현재 제안:** PR #278의 근본 원인은 아직 확정되지 않았다. 모델이나 프롬프트를 먼저 교체하기보다 **실패 응답이 어디에서, 왜 거부되었는지 판별할 최소한의 진단 능력**을 검토한다. 첫 후보는 *원문 없는 단계별 오류 분류 + 제한된 완료/응답 메타데이터*다. 실제 응답 열람은 추가적인 보안·정본 계약 검토가 필요하다.
>
> **수용 원칙 — 무조건 수용 금지:** 이 문서의 기능 목록은 구현 요구사항이나 사전 승인 목록이 아니다. 후속 작업자는 **각 후보의 문제 해결 기여도, 재현 근거, 기존 기능과의 중복, 정본 Spec 적합성, 정보 노출 위험, 유지보수 비용을 독립적으로 재검토**해야 한다. 근거가 약하거나 과도한 제안은 **명시적 이유와 함께 드랍**하고, 필요하지 않은 항목을 P0·P1이라는 이유만으로 구현해서는 안 된다. 검토 결과가 모든 후보를 보류/기각하는 것이어도 허용한다.

## Decision Needed

PR #278의 [기존 원인 조사](00-research-review-ai-live-schema-failure.md)는 `response_schema_invalid`가 이전 Qwen2.5 및 Qwen3.5 계열에서 기록됐다고 설명한다. 하지만 원시 응답과 당시 종료 이유를 충분히 보존하지 않았고, 현재 `review_ai/service.py`는 서로 다른 JSON 구문 오류와 Pydantic 계약 오류를 같은 결과 코드로 합친다. 따라서 성공률 개선책을 평가하기 전에 **최소한의 판별 증거**가 필요하다.

이 문서에서는 (1) 무엇을 새로 관찰해야 하는가, (2) 그 증거 없이도 가능한 진단은 무엇인가, (3) 기존 정본 계약을 해치지 않는 최소 도입 범위가 무엇인가를 선택한다. 연구·의사결정 지원용 Inbox artifact이며 정본 Spec, OpenSpec proposal, 실제 구현 승인 또는 해결 증명이 아니다.

## Current Boundaries

- [Review AI 정본 Spec](../../openspec/specs/reliability-agentic-review/spec.md)은 **fail-closed**, schema/guard 실패 시 재시도 금지, invocation provenance에 **raw provider response·raw prompt·raw exception 미기록**, 실패한 Langfuse projection의 identity/status-only 표시를 요구한다. 진단 가능성을 이유로 acceptance, retry, export policy를 묵시적으로 변경하지 않는다.
- `runtime_ai/provider.py`는 `response_format={"type":"json_object"}`를 SDK 전송에서 하드코딩하고 `finish_reason`을 `TransportResponse`/ `ProviderResponse`에 전달하지 않는다. `choices=[]` 또는 `message.content=None`은 빈 문자열로 정규화될 수 있다.
- `review_ai/service.py::_parse_output`은 JSON 파싱 실패와 Pydantic 검증 실패를 `None`으로 묶어 `response_schema_invalid`로 처리한다. `review_ai/evidence.py`와 `review_ai/store.py`는 sanitized evidence를 create-only로 저장한다. 이미 저장된 9건은 원문 복원에 사용할 수 없다.
- `scripts/run_agentic_review_live.py`는 opt-in 합성 실행 harness이며 결과·선택적 Langfuse projection이 분리되어 있다. Langfuse projection 확대는 이 제안의 기본 scope가 아니다.
- PR #278은 현재 Draft 조사 단계다. 새 GPU 실험 결과나 현재 head의 해결된 상태를 가정하지 않는다.

## Candidate Assessment

| 후보 | 잠정 판단 | 정보 가치 / 검토·드랍 기준 |
| --- | --- | --- |
| **A. 단계별 오류 분류**: empty body, JSON syntax, schema field/type/conditional, deterministic guard | **조건부 우선 검토** | 하나의 실패 코드를 유지하면서도 실제 차이를 확인할 수 있다면 유효. 기존 반환·증적 contract를 깨거나 Pydantic의 raw `input`/ `ctx`를 흘려보내야만 구현된다면 방법 재설계 또는 드랍 |
| **B. 완료·응답 형상 메타데이터**: `finish_reason`, content 존재 여부/바이트 크기, usage | **조건부 우선 검토** | context·잘림·빈 답변 가설 판별에 도움. 실제 SDK/Provider가 제공하는 값만 기록하고 unsupported/unknown을 허위 값으로 대체하지 않는다. 공통 Runtime AI DTO 확장이 불필요하면 하지 않는다 |
| **C. 요청 설정 점검**: 실제 wire의 model, `max_tokens`, `response_format` 등 allowlist | **조건부 검토** | DTO와 SDK/HTTP body 불일치 검출에 가치. 기존 fake HTTP 테스트만으로 확인되면 별도 runtime 기능·CLI 출력은 드랍. full prompt, key, Authorization 헤더, URL credential을 노출하지 않는다 |
| **D. 실제 provider 응답 열람** (사용자 제안) | **보류 — 안전성 판단 선행** | 합성 입력·명시적 opt-in·로컬의 짧은 세션에서만 원문을 일시 열람하는 대안은 검토할 가치가 있다. 그러나 stdout/파일/IDE/CI 수집은 영속 로그가 될 수 있고 Spec의 raw 미기록 경계와 충돌할 수 있다. 별도 승인/정본 해석 없이 `--show-response` 같은 기능을 구현하지 않는다 |
| **E. Validation replay** | **후순위 조건부** | 신규 synthetic fixture나 일시 확보한 실제 응답을 모델 재호출 없이 재검증하면 유용. 과거 실패 원문이 없는데 '완전 replay'라고 주장하거나 원문을 상시 저장해야만 가능하다면 드랍 |
| **F. 실패 fingerprint·cohort 집계** | **후순위** | 분모를 포함한 실행 inventory가 있을 때만 실효성. 9개 실패만으로 모델별 실패율을 만드는 방식, transport retry를 독립 표본으로 집계하는 방식은 기각 |
| **G. Langfuse 원문/Trace 확대** | **현 단계 드랍** | 현재 문제는 export 이전 경계에서 판별 가능. 외부 전송·새 의존성과 민감정보 부담이 크고 실패 output 표시 정책과 충돌하므로 독립적인 요구/승인 없이 도입하지 않는다 |
| **H. 자동 schema repair/재생성** | **현 단계 드랍** | 실패 원인을 숨기고 현재 no-retry Spec을 변경해야 하므로 진단 목적에 부적합. 별도 정책 결정 전 제안하지 않는다 |

표의 **조건부 검토**는 구현 채택이 아니다. 최소한의 코드 수정 없이 SDK fake HTTP + 기존 Pydantic 오류 보고만으로 원하는 판별이 가능하면 그 방법을 먼저 선택한다.

## Minimal Investigation Slice

**1. 진단 목표를 실패 유형으로 고정한다.** 적어도 다음 네 가지 질문에 답할 수 있으면 1차 목적이 달성된다.

1. 실제 응답은 빈 본문인가, JSON 문법이 깨졌는가, 아니면 유효한 JSON의 필드가 틀렸는가?
2. 스키마 실패라면 어떤 **제한된 field path와 error category**에서 실패했는가? 실제 값과 자유형 예외 메시지는 포함하지 않아도 되는가?
3. 모델의 종료 이유(`stop`/`length`/기타/미확인)와 실제 token 설정·사용량은 무엇인가?
4. 요청의 `response_format`과 `max_tokens` 값은 설정→DTO→SDK→HTTP body에서 유지됐는가?

**2. 가능한 한 먼저 오프라인 실험한다.**

- 현재 정본 모델에서 작성한 작은 fixture로 정상 JSON, broken JSON, `uncertainties`의 문자열 타입, 조건부 `priority`, `content=null`, `choices=[]`를 각각 분리한다. 기존 테스트와 중복되는 것은 새로 만들지 않는다.
- 실제 SDK와 fake HTTP를 사용해 `finish_reason=stop/length`를 주입하고, 각 단계에서 실제로 전달/소실된 metadata를 확인한다. `length` 단독 자동 거부는 현 Spec에서 요구하지 않으므로 판별값으로만 다룬다.
- `ValidationError.errors()` 계열의 구조화 오류에서 **`type`, 제한된 `loc`만 allowlist**로 사용 가능한지 검증한다. 입력 값·`ctx`·메시지에 민감정보가 들어갈 가능성을 먼저 확인한다.
- sanitized 결과의 비교 oracle은 **독립적인 fixture와 expected category**로 둔다. 같은 parser의 반환을 예상값으로 복사해서 false green을 만들지 않는다.

**3. 가장 작은 실제 변경만 검토한다.** Stage A/B/C에서 필요한 판별을 못 하는 부분만 기존 `runtime_ai` 또는 `review_ai` 경계의 적절한 owner에 추가한다. 합성 harness 출력으로 충분하면 새로운 범용 trace framework, public DTO, 영속 evidence schema, 외부 dashboard를 만들지 않는다. 각 추가 기능은 현재 acceptance 및 evidence 계약 유지 여부를 증명한 후 다음 기능을 검토한다.

**4. 필요할 때만 opt-in live로 검증한다.** 로컬 ignored invocation evidence의 `prompt_digest`·설정·usage 비교와 `/api/show`·`ollama ps` 확인 후, 동일 synthetic case를 명시적으로 지정한 모델로 재실행한다. 이때에도 새로운 live 실패가 원인 확정이라는 뜻은 아니다.

## Safety and Acceptance Gates

기능을 수용할 때는 **한 가지 실제 실패 시나리오의 판별력이 증가했는지**와 다음 조건을 모두 확인한다.

- 기본 실행/CLI/CI에는 raw provider output, raw rendered prompt, secret, 원시 validation exception이 **노출·저장·원격 투영되지 않는다**. 출력이 필요하면 정책상 허용 여부, 합성 데이터 한정, 터미널 캡처 위험, opt-in 경계를 먼저 검토한다.
- `validation_failed`는 계속 fail-closed이며 schema-invalid 결과가 `accepted`가 되지 않는다. 자동 coercion·재시도·후속 recovery를 추가하지 않는다.
- 기존 `failure_code`와 immutable evidence, replay identity, Langfuse export, read-only boundary를 불필요하게 변경하지 않는다. 새로운 field/계약이 필요하면 정본 Spec의 owner와 변경 절차를 먼저 확인한다.
- 정보 미제공/지원되지 않은 `finish_reason`·token usage·요청 metadata는 **unknown으로 표기**한다. 없는 측정값을 `stop`이나 0으로 채워 원인을 단정하지 않는다.
- 최소 테스트는 fake HTTP의 정상/빈/잘림/잘못된 필드, sanitize 검증, flag off, 기존 정상 경로 회귀를 포함한다. 실제 수행한 테스트·미수행 테스트를 구분한다.
- 모델별 성공률·원인 분포는 같은 revision/prompt/model/config 조건의 **전체 논리적 invocation 분모**가 있을 때만 계산한다.

## Review Decision and Next Action

**후속 담당자가 내려야 할 판단:** A/B만으로 충분한가? C는 기존 테스트 강화로 해결되는가? D의 원문 열람이 그 이상의 새 증거를 주는가? E/F는 실제 수요가 있는가? 모든 후보에서 **채택/부분 채택/보류/기각과 한 줄짜리 증거·드랍 사유**를 기록한 뒤에만 구현 scope를 확정한다. 부적절하거나 비용 대비 효과가 낮은 리뷰·기능 요청은 과감히 제외한다.

현재 제안의 최소 실행 단위는 **A + 필요성이 입증된 B의 부분집합**이다. C는 fake HTTP 테스트로 우선 검증하고, D~H를 PR의 필수 구현 범위로 묶지 않는다. 원문 직접 열람이 꼭 필요한 것으로 확인되면 **그때 별도의 보안·정본 정책 판단**을 요청한다.

**검증 상태:** 이 문서는 코드/정본 계약에 대한 설계 제안이다. 신규 코드, CLI flag, GPU/live 호출, 테스트 실행은 수행하지 않았다. 실제 실패 원인은 여전히 미확정이다.

## References

- [PR #278](https://github.com/mols3131d/hmda-data-reliability/pull/278) / [기존 조사](00-research-review-ai-live-schema-failure.md)
- [정본 Review AI Spec](../../openspec/specs/reliability-agentic-review/spec.md)
- [Review AI service](../../src/hmda_reliability/review_ai/service.py), [evidence](../../src/hmda_reliability/review_ai/evidence.py), [store](../../src/hmda_reliability/review_ai/store.py)
- [Runtime AI provider](../../src/hmda_reliability/runtime_ai/provider.py), [contracts](../../src/hmda_reliability/runtime_ai/contracts.py)
- [Synthetic live harness](../../scripts/run_agentic_review_live.py)
- [기존 Notion 원인 분석](https://app.notion.com/p/40613d7e58b9817bbe55c25f18e4c7bf)
