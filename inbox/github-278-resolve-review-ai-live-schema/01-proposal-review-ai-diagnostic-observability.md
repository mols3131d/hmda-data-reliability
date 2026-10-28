---
type: proposal
title: Review AI failure diagnosis options
description: response_schema_invalid 원인을 식별하기 위한 최소 진단 기능을 비교하고 채택·보류·기각 기준을 제안한다.
tags:
  - review-ai
  - runtime-ai
  - diagnostics
---

# Review AI Failure Diagnostics

> **Proposal only — not approved for implementation.** 현재 `response_schema_invalid`의 근본 원인은 미확정이다. 실패 응답을 재현·분류할 수 있는 최소 진단 기능을 우선 검토하되, 이 문서의 옵션을 **무조건 수용하거나 모두 구현해서는 안 된다.** 담당자는 각각을 기존 기능·정본 Spec·보안 경계·실제 판별력·유지보수 비용과 대조해 **채택 / 축소 수용 / 보류 / 기각**하고, 특히 드랍한 이유를 짧게 기록한다. 근거가 약한 지적이나 과한 기능은 구현하지 않는다.

## Problem

[PR #278](https://github.com/mols3131d/hmda-data-reliability/pull/278)의 실패 증적은 `validation_failed / response_schema_invalid`를 기록하지만, 실제 모델 출력이 빈 응답인지, 깨진 JSON인지, 유효한 JSON의 필드 위반인지 구별하기 어렵다.

- `review_ai/service.py::_parse_output`은 JSON 문법 오류와 Pydantic 출력 계약 오류를 모두 `None`으로 처리한다.
- `runtime_ai/provider.py`는 `finish_reason`을 내부 결과에 전달하지 않고 `choices=[]` 또는 `content=None`을 빈 문자열로 취급한다.
- 기존 정제 invocation evidence에는 실패 응답 원문이 없다. 과거 실패 9건의 원문을 복원할 수 있다는 주장을 해서는 안 된다.
- 정본 Spec은 raw provider response, raw prompt, credential 등을 **영속 증적에 남기지 않을 것**과 schema/guard failure의 fail-closed·no-retry를 요구한다.

따라서 목표는 성공률을 임의로 높이는 것이 아니라 **실패 단계를 구별하고 원인을 검증할 수 있게 하는 것**이다. 관련 분석은 기존 [원인 조사](00-research-review-ai-live-schema-failure.md) 및 [Notion 연구 노트](https://app.notion.com/p/40613d7e58b9817bbe55c25f18e4c7bf)를 따른다.

## Options

| 후보 | 얻는 답 | 권고 수준 | 도입 판단 조건 |
| --- | --- | --- | --- |
| A. Bounded validation diagnosis | JSON 구문 실패인가, Pydantic 타입·조건부 제약 실패인가? | **우선 검토** | 기존 외부 failure code와 accepted/guard 동작을 유지하며 정보 유출 없이 분류 가능한가 |
| B. Response completion metadata | `stop`/`length`, 누락된 본문·빈 `choices`, 실제 content 크기는? | **우선 검토** | SDK에 해당 값이 존재하는지 확인하고 최소한의 metadata만 경계를 통과시킬 수 있는가 |
| C. Local response inspection | 실제 모델 응답에 어떤 필드·값이 들어왔는가? | **조건부·opt-in** | synthetic fixture로 한정한 실행에서 명시적 승인, redaction·노출 범위·출력 목적지 통제가 가능한가 |
| D. Request wire inspection | 실제 HTTP 요청의 format·token cap·model·runtime 설정은? | **보조 후보** | 기존 DTO/wire 테스트와 중복하지 않고 새로운 판별 근거가 있는가 |
| E. Validation replay | 캡처된 실패 응답을 GPU 호출 없이 재검증할 수 있는가? | **후속 후보** | 수집 경계와 fixture 보안·생명주기 확정, 기존 replay와 책임 구분이 가능한가 |
| F. Failure fingerprint/cohort | 모델·revision·digest별로 어떤 실패가 반복되는가? | **증적이 있을 때만** | 전체 invocation 분모와 독립 집계 단위가 확보되는가 |
| G. Langfuse raw trace 확대 | UI에서 원시 응답과 전송 흐름을 볼 수 있는가? | **현재 보류** | 로컬에서 불가능한 구체적 요구가 있고 외부 전송·정본 Spec 충돌을 해결했는가 |

**선택 원칙:** A와 B가 이미 필요한 정보를 제공하면 C~G를 구현하지 않아도 된다. 이미 존재하는 로그·SDK trace·테스트·기록만으로 식별 가능한 문제에는 새 프레임워크나 저장소를 만들지 않는다. P0/P1/P2는 **검토 순서**이지 구현 승인이나 필수 roadmap이 아니다.

## Recommended Minimal Experiment

1. **관찰값 정의:** 같은 synthetic `null_spike` 입력으로 정상 JSON, 유효 JSON이지만 `uncertainties` 타입 오류, 조건부 `priority` 위반, 잘린 JSON, `content=null`, `choices=[]`를 준비한다. 현재 테스트가 이미 보호하는 케이스는 중복 추가하지 않는다.
2. **가장 작은 경계에서 분류:** JSON parse / Pydantic 검증 / deterministic guard를 분리한다. Pydantic `ValidationError.errors()`는 입력값·URL 등 원문을 포함할 수 있으므로 **무가공 직렬화하지 않는다**. 필요한 경우 안정적인 오류 code와 allowlisted field path만 추출한다.
3. **SDK response 확인:** fake HTTP/실제 SDK로 `finish_reason=stop|length`, content 유무, 사용량을 확인한다. `length`를 단독 거부하는 새 정책을 테스트로 확정하지 않는다.
4. **증거 부족할 때에만 opt-in 본문 확인:** 로컬 synthetic-only 실행의 메모리/터미널에서 크기 제한된 원문을 직접 관찰하는 방안을 검토한다. **터미널/CI 출력도 로그가 될 수 있으므로 기본 출력 금지**. 일반 실행·CI·Langfuse projection에서 노출하지 않는다. 출력 저장·복사·보존은 별도 결정 대상이다.
5. **수정 판단:** 관찰된 오류의 직접 원인을 확인한 뒤에만 prompt, context, SDK transport 또는 validator 변경을 별도로 제안한다. 진단 기능 자체로 근본 원인이 해결되었다고 쓰지 않는다.

실행 인터페이스(`--diagnose`, `--show-response` 등)는 **가칭 예시**다. 기존 `scripts/run_agentic_review_live.py`의 인자·환경변수 계약과 정본 Spec을 확인한 뒤 최소 방식으로 결정한다. 실제 구현된 CLI라고 소개하거나 사용법에 넣지 않는다.

## Acceptance / Rejection Criteria

**선택한 최소 기능의 검증 기준 (구현 제안, 미확정):**

- 합성 응답에 대해 `json_syntax_invalid`, `schema_field_type_invalid`, `schema_conditional_invalid`, `response_content_empty` 같은 **예시 분류** 중 실제 필요한 것만 서로 구별할 수 있다. 기존 공개 `response_schema_invalid`를 바꿔야 한다는 요구는 아니다.
- 실패 응답은 계속 `validation_failed`이며 `accepted`로 승격되지 않는다. deterministic guard와 영속 provenance가 그대로 유지된다.
- 진단이 꺼진 일반 실행에서는 raw 응답·prompt·secret 및 상세 Pydantic 입력값이 콘솔, logger, 저장된 evidence, Langfuse 등으로 누출되지 않는다.
- 원문 관찰을 택하더라도 synthetic-only, opt-in, bounded, local, 비영속 원칙에 맞는 실제 출력 경계를 검증한다. 정본에서 허용되지 않는 보존·전송이 필요해지면 **먼저 해당 정책 소유자의 명시적 결정**을 받는다.
- 분류 성공은 **관측성 개선**의 증거다. 근본 원인 해결은 현 PR head의 재현과 별도 opt-in live 결과로만 주장한다.

**수용하지 말아야 할 경우:** 중복되는 기존 기능, 정본 Spec과 충돌, 에러 상세가 실제 원인 판별에 보탬이 안 됨, raw data 위험이 이점보다 큼, 새 API/상태/의존성이 증가하는데 현재 요구가 없음, 근거 없는 모델 성능 추정, 비용만 늘리는 통합 플랫폼. `dict[str,str]` 및 JSON-mode 하드코딩 문제를 고친다는 명목으로 schema-constrained 기능까지 한 번에 확대하는 것도 이 제안의 필수 범위가 아니다.

## Review Decision Required

각 옵션에 대해 **채택 / 축소 수용 / 보류 / 기각**과 이유를 남긴 후, 채택한 최소 경계에서만 구현·검증한다. 제안자가 우선순위를 높게 표시했다는 이유만으로 수용하지 않는다. 이미 정본에서 충족한 항목은 **추가 구현 없이 충족**으로 처리한다. 사용자가 제안한 '실제 출력 보기'도 보안과 필요성 검토 결과 기각할 수 있어야 한다.

| Option | Decision | Evidence / reason |
| --- | --- | --- |
| A–G | **Pending independent review** | 이 문서는 승인·구현 완료·시험 통과 기록이 아님 |

## References

- [PR #278](https://github.com/mols3131d/hmda-data-reliability/pull/278)
- [Review AI canonical Spec](../../openspec/specs/reliability-agentic-review/spec.md)
- [Review AI service](../../src/hmda_reliability/review_ai/service.py), [Runtime AI provider](../../src/hmda_reliability/runtime_ai/provider.py), [Invocation evidence](../../src/hmda_reliability/review_ai/evidence.py)
- [Existing PR investigation](00-research-review-ai-live-schema-failure.md)

**Validation:** 제안서 작성만 수행했다. 원문 출력 캡처, GPU/live, 프로젝트 테스트, 기능 구현은 수행하지 않았다.
