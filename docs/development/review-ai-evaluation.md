---
title: "Review AI Evaluation"
description: "Review AI의 deterministic suite, live provider proof, human rubric 평가와 optional Langfuse projection을 실행하고 evidence를 해석할 때 사용하는 개발 가이드입니다."
categories:
  - software-engineering
tags:
  - evaluation
  - langfuse
  - llmops
  - review-ai
  - testing
---

# Review AI Evaluation

Review AI의 품질과 integration evidence를 검증할 때 사용한다. 이 문서는 deterministic test, live provider proof, human rubric 평가와 optional Langfuse projection의 실행 절차와 evidence boundary를 안내한다. 일반 pytest 선택과 CI 동작은 [Testing Guide](testing.md)를, Review AI의 책임과 safety boundary는 [Review AI](../domains/review-ai.md)를, normative behavior는 [`reliability-agentic-review`](../../openspec/specs/reliability-agentic-review/spec.md) Spec을 따른다.

## Offline Suite

Review AI의 기본 suite는 fake transport와 temporary artifact root만 사용하며 network provider를 호출하지 않는다. Runtime AI의 settings와 provider-neutral contract도 함께 검증한다.

```bash
uv run pytest tests/review_ai tests/runtime_ai
```

`tests/review_ai`는 다섯 human rubric criterion, test-only positive/restatement/hedging fixtures, evaluation identity와 baseline/candidate comparison도 검증한다. 이 deterministic suite는 실제 provider 실행이나 사람의 utility assessment를 대신하지 않는다.

## Live Provider Proof

실제 Ollama proof는 기본 suite와 분리해 명시적으로 실행한다. [`.env.example`](../../.env.example)의 `HMDA_AGENTIC_REVIEW_*` 값을 로컬 `.env`에 설정한다. `HMDA_AGENTIC_REVIEW_LIVE=true`와 비어 있지 않은 base URL, API key, model이 필요하다. API key는 OpenAI-compatible client에 전달하지만 invocation evidence에는 저장하지 않는다.

```bash
uv run --env-file .env python scripts/run_agentic_review_live.py
```

`HMDA_AGENTIC_REVIEW_PROJECT_REVISION=auto`는 현재 Git HEAD를 사용하며 tracked worktree가 깨끗해야 한다. 필요하면 비어 있지 않은 revision을 명시할 수 있다. 결과는 `accepted` 또는 typed failure다. Provider 호출이 시작되면 `HMDA_RELIABILITY_ARTIFACTS_DIR/agentic-review/invocations/`에 sanitized evidence를 남긴다. Live proof는 approval, recovery 또는 data mutation을 수행하지 않는다.

Live harness는 출력의 타입과 `priority` 조건을 명시한 `v2` prompt를 기본으로 사용한다. `HMDA_AGENTIC_REVIEW_PROMPT_VERSION=v1`은 과거 동작 비교용이고, `v3`는 수치 단위와 evidence/draft 충실성을 비교하기 위한 선택 가능한 후보다. 세 version 모두 저장된 `prompt_identity`와 canonical input으로 재생할 수 있다. Python API의 `PromptIdentity()` 기본은 과거 caller와의 호환성을 위해 `v1`이며 caller는 원하는 version을 명시적으로 전달한다. v3 지원은 실제 출력 개선이나 채택을 의미하지 않는다.

### Output Quality Cases

[`output_quality_v1.json`](../../tests/review_ai/evaluation/fixtures/output_quality_v1.json)은 provider 출력에서 정답을 추출하지 않은 합성 입력·독립 oracle·negative control이다. 다음 세 조건을 구별한다.

| Case | Independent numeric oracle | Context / draft |
| --- | --- | --- |
| Existing regression | 1% → 21%, 20 percentage points 증가, threshold 10 percentage points, 상대 증가율 2000% | 추가 evidence 없음, backfill 없음 |
| Zero baseline | 0% → 12%, 12 percentage points 증가, threshold 5 percentage points, 상대 증가율 정의 불가 | 추가 evidence 없음, backfill 없음 |
| Supplied context | 1% → 21%, 20 percentage points 증가, threshold 10 percentage points | metadata/catalog/dbt evidence와 backfill 제안 있음; 원인 확정과 구별 |

알려진 wrong-number, copied-example, restatement, unsupported-cause와 nonexistent-draft-action control도 identity/facts/references가 올바르면 현재 structured validator를 통과한다. 이 테스트는 탐지 경계를 드러낸다. Corpus의 문구와 질문은 검토 보조 자료이며 사람 점수나 실제 모델 품질의 증거가 아니다. Exact example match는 제한된 복사 신호이고 임의 prose의 의미적 정답 판정기가 아니다.

### Baseline and Candidate Comparison

1. 호출 전에 case/version, 모델·양자화, active context, Thinking 상태, output cap, timeout, retry, 반복 횟수 및 최대 총 호출 수를 정한다. Context/Thinking 실험은 prompt 비교와 분리하고 Ollama의 실제 적재 상태를 확인한다.
1. Tracked tree가 깨끗한 하나의 candidate HEAD에서 각 case의 `review_input`을 `AgenticReviewInput.model_validate()`로 읽는다. Fixture의 `project_revision`은 live revision이 아니므로 실제 HEAD를 [`review_null_spike()`](../../src/hmda_reliability/review_ai/service.py)에 별도로 전달한다. 동일 incident/evidence/draft와 runtime 조건에서 `PromptIdentity(version="v2")` baseline과 `PromptIdentity(version="v3")` candidate를 실행한다. 기본 live script의 입력은 기존 한 사례이므로 나머지 사례는 이 API에 명시적으로 전달한다.
1. 시작 전에 attempt 목록을 만들고 실패·exclusion도 남긴다. 각 attempt의 case/version/role/repeat, 실제 revision, invocation identity, status/failure, prompt/output digest, latency/usage와 provider context/Thinking 조건을 연결한다. 원문 response나 credential은 보존하지 않는다. Retry를 사용할 경우 물리 호출 수도 예산에 포함한다.
1. Accepted output의 설명을 독립 oracle 및 실제 제공된 evidence/draft와 대조한다. 숫자·threshold 단위가 맞는지, baseline-zero의 상대 증가율을 만들지 않는지, 원인·완료된 검증을 지어내지 않는지, 실제 draft에 없는 action을 비판하지 않는지 확인한다. 무엇을 먼저 확인하고 결과별 사람 판단이 어떻게 달라지는지 기록한다.
1. 사람이 다섯 criterion 각각에 0–2점과 rationale을 제공한 뒤 기존 `ReviewValueAssessment`와 `compare_review_value()`를 사용한다. `case_id/version`, role, 실제 revision, invocation, exact output digest를 연결하고 같은 case끼리 비교한다. API는 caller가 제공한 점수·decision을 검증하며 의미적 채점을 대신하지 않는다. 동일 role/repeat의 identity를 임의로 바꾸거나 좋은 출력만 고르지 않는다.
1. 전체 시도의 실패·정확성·utility를 함께 보고 실제 사람이 `accept`, `reject` 또는 `no_change`와 이유를 결정한다. 조건이 다르면 `blocked`/`inconclusive`, 사람 평가가 없으면 미검증이다. 과거 호출이나 offline fixture 성공으로 후보를 기본값으로 전환하지 않는다.

### Diagnose a Failed Response

`response_schema_invalid`이면 결과의 `invocation_path`에 있는 정제된 record에서 다음 필드를 확인한다. Raw response와 Pydantic 입력값은 보존하지 않는다.

| Evidence field | Meaning / next action |
| --- | --- |
| `response_diagnostics.kind=response_content_empty` | 본문이 비었다. `response_metadata.content_state`로 `content_missing`, `choices_empty`, 빈 text를 구분한다. |
| `response_diagnostics.kind=json_syntax_invalid` | JSON으로 파싱할 수 없다. `finish_reason=length`이면 token cap과 provider의 실제 context 설정을 함께 확인한다. |
| `response_diagnostics.kind=schema_validation_failed` | 유효 JSON이 출력 계약을 위반했다. 최대 8개의 allowlisted `field_path`와 `code`로 타입·누락·조건부 오류를 조사한다. |
| `response_metadata` | SDK가 제공한 완료 이유, 본문 상태와 UTF-8 byte 수다. 알 수 없는 완료 이유는 `unknown`이며 과거 record나 custom transport에서는 metadata가 없을 수 있다. |

`length`는 단독 거부 사유가 아니며 schema·guard·provenance 검증이 최종 결과를 결정한다. `max_output_tokens`는 실제 모델의 context window와 별개다. 모델 이름만으로 context 크기를 추정하거나 무조건 재시도하지 말고, provider 설정을 확인한 뒤 같은 synthetic 입력과 명시적 모델·prompt version으로 비교한다. 오류를 재현하는 작은 응답 fixture를 offline suite에 추가하고 현재의 깨끗한 revision에서 live 결과를 다시 확인한다. 진단 분류의 성공만으로 모델 실패나 utility 문제가 해결됐다고 판단하지 않는다.

## Optional Langfuse Projection

Synthetic live proof를 Langfuse에도 표시하려면 provider 설정과 별도로 projection을 켜야 한다. Provider opt-in만으로는 전송하지 않는다.

### Setup

로컬 `.env`에서 `HMDA_LANGFUSE_EXPORT=true`로 설정하고, 전송을 허용한 프로젝트의 `LANGFUSE_BASE_URL`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`를 채운다. Key는 commit하거나 log에 복사하지 않는다. `HMDA_LANGFUSE_TIMEOUT_SECONDS`는 전체 연동 대기 시간이며 기본 5초, 최대 60초다. 위의 `HMDA_AGENTIC_REVIEW_*` 설정도 필요하다.

선택 dependency를 설치한 뒤 live script를 실행한다.

```bash
uv sync --extra langfuse
uv run --extra langfuse --env-file .env python scripts/run_agentic_review_live.py
```

### Check the Projection

Script는 projection 상태를 stderr에 출력한다. `invalid_config`, `timeout`, `export_failed`, `projection_failed`, `skipped_*`는 전송 또는 전송 대상 준비가 완료되지 않았음을 나타낸다. 이 상태가 발생해도 확정된 Review AI 결과와 종료 코드는 바뀌지 않는다. Script 종료 코드 0만으로 export 성공을 판단하지 않는다.

`submitted_unverified`는 SDK child가 오류 없이 끝났다는 뜻일 뿐 원격 저장의 증거는 아니다. Langfuse 프로젝트에서 `review-ai-post-hoc-projection` observation을 찾고 invocation, revision, output digest와 input/output을 대조한다. Span duration은 projection 시간이고 model 실행 시간은 `recorded_latency_ms`다. 동일 payload를 다시 보내면 같은 trace에 observation이 추가될 수 있으므로 채점할 observation 하나를 정확히 고른다.

Harness는 local provenance를 검증한 뒤 현재 합성 사례와 일치하는 record만 전송한다. Provider URL/trace ID, rendered prompt, raw error와 전체 환경 변수는 전송하지 않는다. Accepted input/output도 허용된 필드만 보내며 크기 상한을 넘으면 자르지 않고 생략한다. SDK는 단기 child에서만 초기화하고 [`LANGFUSE_MEDIA_UPLOAD_ENABLED`](https://github.com/langfuse/langfuse-python/blob/v4.15.6/langfuse/_client/environment_variables.py)를 `false`로 고정한다. 이는 SDK가 base64 data URI를 media로 바꾸고 별도 업로드를 시도하지 않게 해 structured output과 digest가 같은 문자열을 가리키도록 한다.

### Human Annotation

원격 observation을 확인한 다음 사람의 평가가 필요하면 다음 순서로 진행한다.

1. `rubric_v1`의 다섯 criterion(`added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`)마다 score config를 만든다. Categorical option은 0/1/2만 사용하고 이름·설명에 rubric과 criterion을 식별한다.
1. Accepted observation의 input, draft, evidence/context gaps와 output을 읽고 다섯 score 각각에 근거 comment를 남긴다. 실패 observation은 채점하지 않는다.
1. `invocation_id + output_digest + rubric_v1`이 일치하는지 확인한다. 항목 누락·중복, 0/1/2 밖의 값 또는 빈 comment는 incomplete다. UI의 완료 표시는 repository completeness를 보장하지 않는다.
1. 필요하면 `review_ai.evaluation.langfuse.annotation_complete()`에 수동 score snapshot을 넘겨 accepted structured output의 canonical JSON 값/타입, metadata digest, `rubric_v1` target과 score shape의 일치를 검사한다. 각 score는 `criterion`, integer `score`, `rationale`다. 이 helper는 human authorship나 판단 품질을 증명하지 않으며 evaluation을 저장하거나 import하지 않는다.

### SDK-Only Test

Langfuse project 없이 data URI media 변환 차단만 확인하려면 다음 network-free test를 실행한다.

```bash
uv run --extra langfuse pytest tests/review_ai/evaluation/test_langfuse_projection.py::test_pinned_langfuse_media_processor_keeps_data_uri_when_disabled
```

점수 판단은 사람이 수행한다. Annotation queue는 수동 setup으로 충분하며 importer, automatic judge, prompt 관리와 candidate/recovery 승인은 포함하지 않는다. Offline tests와 SDK smoke는 실제 ingestion, 배포 UI와 사람의 utility 판단을 증명하지 않는다. 실제 proof가 필요하면 동일 implementation revision에서 원격 observation 확인과 다섯 항목 채점을 수행하고 별도 evidence로 기록한다.

## Related Guides

- [Testing Guide](testing.md): 일반 pytest 실행, marker, PR CI와 test result 해석
- [Review AI](../domains/review-ai.md): Review AI의 domain 책임, 공개 surface와 safety boundary
- [Runtime AI](../domains/runtime-ai.md): provider-neutral runtime 설정과 transport boundary
