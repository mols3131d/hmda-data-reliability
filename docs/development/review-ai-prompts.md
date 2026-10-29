---
title: "Review AI Prompt Composition"
description: "Review AI 프롬프트를 책임별 모듈로 나누고 재사용하거나, 조립한 system/user 메시지가 모델에 전달되는 경로를 확인할 때 사용하는 개발 가이드입니다."
categories:
  - artificial-intelligence
  - software-engineering
tags:
  - prompt-engineering
  - review-ai
  - modularity
---

# Review AI Prompt Composition

**프롬프트는 역할이 분명한 Markdown 모듈로 관리하고 사례 데이터는 별도 user 메시지에 넣는다.** 기본 live 경로는 같은 사례의 세 단계에서 한국어 텍스트를 수집하고 코드가 결과 JSON을 만든다. 명시적 structured 경로의 `v1~v3`는 한 번의 JSON 응답을 요청하는 기존 조합이다.

이 문서는 분할 이유와 편집·확인 절차를 설명한다. 불변 조건은 [Prompt Engineering Spec](../../openspec/specs/review-ai-prompt-engineering/spec.md)이, 실제 모듈 선택·순서는 [`_PROMPT_PARTS`](../../src/hmda_reliability/review_ai/prompt/__init__.py)가 소유한다. 모델 출력의 비교·채택 절차는 [Review AI Evaluation](review-ai-evaluation.md)을 따른다.

## Staged Text Workflow

[`review_null_spike_staged()`](../../src/hmda_reliability/review_ai/staged/service.py)는 같은 canonical input을 유지하며 근거 검토 → 초안 비판 → 종합 순서로 호출한다. 이전 단계의 고정 질문은 system 자료로, 이전 모델 답변은 assistant 자료로 유지하고 현재 질문을 마지막 system 메시지에 둔다. 매 호출 직전 누적 메시지 전체의 byte 한도와 digest를 확인한다.

| Module | Role |
| --- | --- |
| [output/prose.md](../../src/hmda_reliability/review_ai/prompt/output/prose.md) | 한국어 일반 텍스트 출력과 식별자·수치 보존, 이전 답변의 취급 |
| [staged/](../../src/hmda_reliability/review_ai/prompt/staged/) | 근거 검토·초안 비판·종합의 고정 질문 |
| [staged/prompt.py](../../src/hmda_reliability/review_ai/staged/prompt.py) | 단계별 명시적 모듈 조합과 대화 이력 구성 |

공유 작업·자문 정책과 호환되는 수치·근거 지침을 재사용한다. JSON 필드 전용 언어 정책과 전체 JSON 출력 설명·배열 지시는 이 조합에 넣지 않는다. 모델에게 JSON 생성을 요구하지 않고 Runtime의 text 모드를 명시한다.

코드가 원입력의 식별자·수치와 `stages[{stage_id,text}]`를 [StagedReviewOutput](../../src/hmda_reliability/review_ai/staged/contracts.py)으로 직렬화한다. 답변의 공백·개행을 보존하고 prose에서 기존 structured finding·priority·근거 참조를 추출하지 않는다. `completed`는 세 답변의 수집·저장 완료이며 사실성 검증이나 사람의 승인을 뜻하지 않는다.

세 단계 외의 자동 수정 대화는 없다. 각 호출에는 기존 Runtime의 timeout·retry·출력 상한을 적용하므로 물리 호출 상한은 `3 * (max_retries + 1)`이다. 빈 답변·알려진 잘림·provider 실패·누적 입력 초과·저장 실패는 후속 단계를 멈춘다. 반환된 원문과 이미 저장한 checkpoint는 유지한다. 실행 및 결과 경로는 [평가 가이드](review-ai-evaluation.md#staged-text-review)를 따른다.

## Timeouts And Execution Budgets

HTTP timeout과 실행 예산은 다른 제한이다. Connect/read/write/pool timeout은 각 네트워크 작업의 비활동 대기를 제한한다. 특히 read timeout은 읽기 대기 한도이며 응답 전체의 생성 시간이나 workflow 전체 시간의 상한이 아니다. 기존 `TIMEOUT_SECONDS`는 세부값을 지정하지 않은 HTTP phase의 fallback으로 유지한다.

단계 예산은 한 단계의 호출·retry·backoff에, workflow 예산은 세 단계 전체에 적용한다. Monotonic clock으로 다음 단계·시도·backoff의 시작 가능 여부와 반환된 응답의 채택 여부를 확인한다. 이 예산은 진행 중인 HTTP 요청이나 파일 저장을 강제로 취소하는 hard deadline이 아니다. 예산이 지난 뒤 반환된 원문도 먼저 저장하고 실패 기록을 남기며, 후속 단계를 진행하거나 `completed`로 채택하지 않는다. Runtime이 본문을 반환하기 전에 timeout이 발생하면 해당 단계의 원문 파일은 없다. 이미 완료한 단계의 원문과 checkpoint는 유지한다.

Live CLI는 환경 변수를 해석해 [Runtime 설정](../../src/hmda_reliability/runtime_ai/settings.py)과 [단계 실행 설정](../../src/hmda_reliability/review_ai/staged/settings.py)에 명시적으로 전달한다. Python API의 설정 객체는 환경 변수를 직접 읽지 않는다.

| Environment | CLI 선택 규칙 |
| --- | --- |
| `HMDA_AGENTIC_REVIEW_TIMEOUT_SECONDS` | 기존 HTTP fallback. 미지정 시 30초 |
| `HMDA_AGENTIC_REVIEW_CONNECT_TIMEOUT_SECONDS` | 명시값 우선. 미지정 시 staged 10초 / structured는 기존 HTTP fallback |
| `HMDA_AGENTIC_REVIEW_READ_TIMEOUT_SECONDS` | 명시값 우선. 미지정 시 staged는 명시한 기존 `TIMEOUT_SECONDS` → 300초, structured는 기존 HTTP fallback |
| `HMDA_AGENTIC_REVIEW_MAX_RETRIES` | 명시값 우선. 미지정 시 staged 0 / structured 1 |
| `HMDA_AGENTIC_REVIEW_STAGE_BUDGET_SECONDS` | staged 전용. 기본 360초 |
| `HMDA_AGENTIC_REVIEW_WORKFLOW_BUDGET_SECONDS` | staged 전용. 기본 1,200초 |

[`.env.example`](../../.env.example)은 connect 10초·read 300초·단계 360초·workflow 1,200초·retry 0의 로컬 운영 예제다. 현재 모델에서 검증한 최적값이나 세 단계 완료 보장은 아니다. 파일의 명시값은 모드를 structured로 바꿔도 유지되므로 모드 기본값을 사용하려면 해당 값을 제거한다. SDK의 숨겨진 retry는 0으로 유지하고 Runtime만 retry를 소유한다. 세 단계의 최대 물리 호출 수는 `3 * (max_retries + 1)`이며, 시간 예산이 먼저 끝나면 실제 호출 수는 더 적다.

Structured 모드에서 세부 timeout을 명시하지 않으면 설정의 세부 필드는 `None`으로 두고 기존 `timeout_seconds`를 그대로 적용한다. 이 fallback은 명시한 `TIMEOUT_SECONDS`, 없으면 30초다. 따라서 과거 structured 호출의 설정 의미를 바꾸지 않는다.

출처 기록에는 자격 증명을 제외한 설정, 실제 시도 횟수와 지연시간을 남긴다. 과거 기록에 없는 세부 timeout이나 실행 예산은 미기록으로 취급하며 현재 기본값으로 보충하지 않는다. 네트워크 timeout, 연결 실패와 실행 예산 소진을 구분해 조사하고, 제한을 늘린 것만으로 모델 응답이나 검토 품질이 검증됐다고 판단하지 않는다.

단계의 `elapsed_ms`는 렌더링·호출·반환된 원문 보존까지 측정하며, 해당 단계의 checkpoint를 쓰기 전에 확정한다. Workflow의 `elapsed_ms`는 최종 manifest를 쓰기 직전까지 측정한다. 최종 진단 metadata의 저장·flush를 강제로 종료하지 않으므로 기록된 시간은 CLI process 종료까지의 전체 소요 시간과 다를 수 있다.

## Module Responsibilities

이하의 version별 설명과 최종 메시지 예제는 기존 structured 조합을 편집·비교할 때 사용한다.

아래 경로는 [prompt/](../../src/hmda_reliability/review_ai/prompt/) 기준이다. 각 모듈은 지시문을 제공하며 사례별 값을 받거나 다른 모듈을 로드하지 않는다. 필드 이름과 전제는 module 작성·재사용 시 확인할 의존 관계다.

| Module | Owns | Reuse assumptions |
| --- | --- | --- |
| [tasks/null_spike.md](../../src/hmda_reliability/review_ai/prompt/tasks/null_spike.md) | HMDA 검토 역할, `null_spike` 범위, 입력을 데이터로 취급하는 규칙 | 같은 사고 유형과 Incident·Evidence·Draft를 검토하는 조합 |
| [policies/language.md](../../src/hmda_reliability/review_ai/prompt/policies/language.md) | 한국어 설명, 식별자·수치 원문 보존 | 현재 Review AI의 네 종류 설명 필드를 사용하는 조합 |
| [policies/advisory.md](../../src/hmda_reliability/review_ai/prompt/policies/advisory.md) | 자문과 실행·승인 권한의 경계 | 같은 자문 경계를 갖는 Review AI 조합 |
| [output/](../../src/hmda_reliability/review_ai/prompt/output/) | 출력 필드·타입·열거값과 JSON 응답 방식 설명 | 같은 [typed output 계약](../../src/hmda_reliability/review_ai/contracts.py). 간략/상세 설명 중 하나를 선택 |
| [guidance/numeric_fidelity.md](../../src/hmda_reliability/review_ai/prompt/guidance/numeric_fidelity.md) | 비율·증감·threshold의 수치 해석 | 같은 deterministic facts와 단위를 사용하는 작업 |
| [guidance/evidence_review.md](../../src/hmda_reliability/review_ai/prompt/guidance/evidence_review.md) | 근거 충실성, 누락·미확정 맥락과 실제 초안 검토 | 제공된 근거 ID, `review_context.gaps`와 Draft가 있는 작업 |
| [guidance/review_value.md](../../src/hmda_reliability/review_ai/prompt/guidance/review_value.md) | 사람 판단에 도움이 되는 검토 기여 | 같은 `utility_contributions` 계약을 사용하는 작업 |
| [examples/utility_contributions.md](../../src/hmda_reliability/review_ai/prompt/examples/utility_contributions.md) | 검토 기여의 형식 예시 | 선택한 출력 필드·열거값과 호환되는 조합. 실제 사례의 사실을 제공하지 않음 |
| [titles/](../../src/hmda_reliability/review_ai/prompt/titles/) | 조합의 표시 제목 | 해당 조합에만 사용 |

정책 모듈도 현재는 **Review AI 안에서 공유**한다. 특히 한국어 정책은 Review AI 출력 필드를 알고 있으므로 다른 agent에 재사용할 때 그 계약을 먼저 확인한다. 출력 설명은 [contracts.py](../../src/hmda_reliability/review_ai/contracts.py)와 [validator.py](../../src/hmda_reliability/review_ai/validator.py)에 맞춰 유지한다. 프롬프트 지시만으로 schema 검증이나 권한 경계가 강제되지는 않는다.

## Choosing A Boundary

**따로 수정하거나 조합에서 따로 선택할 이유가 있을 때 나눈다.** 한 모듈은 인접 파일을 모두 읽지 않아도 목적과 전제를 이해할 수 있는 하나의 책임을 맡는다. 같은 목적의 짧은 규칙은 함께 둔다. 예를 들어 근거와 초안의 충실성을 함께 다루는 현재 검토 지침을 문장마다 파일로 나누지 않는다.

동일한 의미와 전제를 가진 규칙은 기존 파일을 그대로 참조한다. 적용 범위나 의미가 다르면 별도 모듈을 만들고 이름에 차이를 드러낸다. 새 사고 유형이 생기면 작업 모듈부터 분리하고, 출력·정책·수치 지침은 계약이 맞는 것만 재사용한다. 두 번째 실제 consumer의 요구가 생기기 전에는 범용 agent package로 이동하지 않는다.

모듈의 제목·설명에 사례 ID, 현재 관측 수치, 특정 실행의 원인 추정이나 기대 답변을 넣지 않는다. 사례와 정답 oracle은 입력 fixture와 평가 영역에서 관리한다. 형식 예시는 출력 계약을 설명하며 모델이 그대로 복사할 실제 답변을 제공하지 않는다.

## Composition And Delivery

조합은 **표시 제목 → 검토 작업 → 언어 정책 → 출력 설명 → 선택한 검토 지침·예시 → 자문 정책** 순서다. 현재 `v1`은 간략 출력 설명, `v2`는 상세 출력 설명과 형식 예시, `v3`는 상세 출력 설명과 수치·근거·검토 가치 지침을 선택한다. 정확한 파일 목록은 [조합 정의](../../src/hmda_reliability/review_ai/prompt/__init__.py)에서 확인한다.

출력 설명은 조합마다 하나를 선택하고 각 모듈은 한 번만 포함한다. 지침과 예시는 선택한 출력 계약에 맞춘다. 규칙이 충돌하면 작성 단계에서 해결한다. 뒤에 배치했다는 이유로 앞의 규칙을 덮어쓰도록 설계하지 않는다.

```mermaid
flowchart TD
    profile["선택한 version의 고정 조합"] --> modules["Markdown 모듈을 순서대로 조립"]
    modules --> system["system: 완성된 지시문"]
    input["사례별 Incident · Evidence · Draft"] --> context["bounded context와 canonical projection"]
    context --> user["user: UNTRUSTED_CANONICAL_INPUT_JSON"]
    system --> messages["두 메시지 전체의 byte cap · digest"]
    user --> messages
    messages --> service["review_null_spike → provider.invoke"]
    service --> runtime["Runtime AI → 모델 provider"]
```

[`render_review_prompt()`](../../src/hmda_reliability/review_ai/prompt/__init__.py)는 사례별 입력으로 bounded context와 canonical JSON을 만들고 다음 두 메시지를 반환한다.

| Message | Content |
| --- | --- |
| `system` | 선택한 조합의 Markdown 본문 전체 |
| `user` | `UNTRUSTED_CANONICAL_INPUT_JSON\n` 뒤에 canonical JSON |

[`review_null_spike()`](../../src/hmda_reliability/review_ai/service.py)는 이 `rendered.messages`를 `review_provider.invoke()`에 그대로 전달한다. [Runtime AI adapter](../../src/hmda_reliability/runtime_ai/provider.py)는 같은 메시지로 JSON 객체 응답을 요청한다. 모델은 조립된 텍스트를 받는다. 파일 경로, 이 안내서와 README를 모델이 직접 읽을 필요가 없다.

모듈 선택은 코드의 고정된 조합에서만 수행한다. 원본 데이터 안의 경로·지시문·include 문자열은 user 데이터로 남는다. 모듈 안의 include, 디렉터리 자동 탐색, 사례 값의 system 치환이나 동적 템플릿 엔진은 사용하지 않는다.

## Inspect The Final Messages

Repository root에서 다음 예제를 실행하면 기존 합성 사례 하나에 `v3`를 적용한 최종 지시문, 주입 데이터와 digest를 확인할 수 있다. 모델 호출과 데이터 적재는 수행하지 않는다.

```bash
uv run python - <<'PY'
import json
from pathlib import Path

from hmda_reliability.review_ai.contracts import AgenticReviewInput
from hmda_reliability.review_ai.prompt import render_review_prompt

corpus = json.loads(
    Path("tests/review_ai/evaluation/fixtures/output_quality_v1.json")
    .read_text(encoding="utf-8")
)
case = corpus["cases"][0]
review_input = AgenticReviewInput.model_validate(
    case["review_input"] | {"prompt_identity": {"version": "v3"}}
)
rendered = render_review_prompt(review_input, max_prompt_bytes=65_536)

for message in rendered.messages:
    print(f"=== {message.role} ===")
    print(message.content)
print(rendered.prompt_digest, rendered.prompt_bytes)
PY
```

이 예제의 fixture revision은 로컬 메시지 확인용이다. 실제 모델 실행과 사람 평가에는 [평가 가이드](review-ai-evaluation.md)의 동일 조건·revision 연결 절차를 사용한다. 저장된 실행에 주입된 데이터는 invocation의 `canonical_input`에서 확인하고, 과거 프롬프트는 기록된 `project_revision`의 renderer와 모듈로 재현한다.

## Editing And Reusing A Module

1. 변경 목적에 해당하는 모듈을 고른다. 한국어 규칙은 정책, 검토 판단은 지침, 필드 설명은 출력, 예시 수정은 예시 모듈을 편집한다.
1. [조합 정의](../../src/hmda_reliability/review_ai/prompt/__init__.py)에서 해당 파일을 참조하는 조합을 확인한다. 공통 파일 수정은 모든 참조 조합에 영향을 준다. 일부 후보에만 다른 의미를 실험하면 별도 모듈을 선택한다.
1. 모듈은 UTF-8 Markdown으로 작성하고 마지막 LF 하나를 유지한다. 로더는 조각 사이에 LF 하나만 추가하며 `strip()`하거나 Markdown을 변환하지 않는다. 현재 import 시 리소스를 읽으므로 편집 후 새 process에서 확인한다.
1. 위 예제로 system/user 메시지를 확인한다. `prompt_bytes`와 `prompt_digest`는 **system 본문과 user JSON을 포함한 전체 메시지 배열**의 canonical UTF-8 직렬화를 기준으로 한다.
1. [프롬프트·전달 회귀](../../tests/review_ai/test_prompt_provider.py)를 실행한다. 구조만 바꿨으면 본문과 기존 digest를 보존한다. 내용이 바뀌면 변경 근거와 새 digest를 기록하고 공유 조합 전체의 영향, 출력 계약과 예시의 호환성을 확인한다. 리소스를 이동·추가했다면 checkout 밖에서 wheel의 리소스 로딩도 확인한다.
1. 실제 출력이 달라지는 변경은 [평가 절차](review-ai-evaluation.md#baseline-and-candidate-comparison)에 따라 비교한다. 조립 성공과 offline 회귀 통과는 모델의 검토 품질을 증명하지 않는다.

검증·채택 후 일반 실행의 기본 조합은 하나로 통일한다. 기본값의 전환과 과거 조합의 비교·재현은 [lifecycle 정본](../../openspec/specs/review-ai-prompt-engineering/spec.md#requirement-prompt-lifecycle-and-active-default)을 따른다.
