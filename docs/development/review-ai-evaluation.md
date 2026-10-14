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
