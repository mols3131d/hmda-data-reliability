---
title: "Reliability AI Evaluation"
description: "Bounded investigation의 명시적 등록·Dataset 실행·실패 감사와 실제 baseline/candidate의 native 사람 평가 절차입니다."
categories:
  - software-engineering
tags:
  - evaluation
  - langfuse
  - llmops
  - review-ai
  - testing
---

# Reliability AI Evaluation

**Prompt Management·Dataset 실험·관측·사람 평가는 Langfuse가 소유한다.** 프로젝트의 native Dataset task는 일반 API와 같은 bounded investigation을 호출한다. 합성 사건 snapshot과 허용된 read-only 조회를 사용하며 실제 HMDA 적재·dbt 실행·복구를 시작하지 않는다.

정본은 [reliability-agentic-review](../../openspec/specs/reliability-agentic-review/spec.md), 프롬프트는 [Prompt Guide](review-ai-prompts.md), 일반 검증은 [Testing Guide](testing.md)를 따른다. SDK는 `langfuse==4.15.6`이다. 대상 서버 호환성을 확인하지 않고 v5 예제로 바꾸지 않는다.

## Offline Suite

```bash
uv sync
uv run pytest tests/reliability_ai tests/runtime_ai
```

기본 suite는 fake transport·고정 native Prompt·실제 SDK의 메모리 exporter와 임시 artifact root를 사용한다. 입력·조회 범위·history·예산·원문·canonical facts·실제 호출 구간 관측·항목 완전성을 검사한다. 원격 서버·모델은 호출하지 않으며 통과는 모델 품질이나 사람 평가의 증거가 아니다.

## Configure Connections

PR을 시험할 때는 해당 PR checkout의 repository root를 사용한다. [환경 예제](../../.env.example)를 참고해 `.env`에 `LANGFUSE_BASE_URL`, public/secret key와 `OPENAI_BASE_URL`, `OPENAI_API_KEY`를 설정한다. 사용 중인 파일을 예제로 덮어쓰지 않고 자격 증명을 Git·로그·문서에 복사하지 않는다.

표준 `LANGFUSE_*`는 SDK가 읽는다. 별도 Langfuse opt-in·기존 live 환경·SDK extra 설치는 없다. 아래 명령의 명시적 실행이 원격 등록과 모델 호출을 시작한다. Import와 기본 테스트는 실행하지 않는다.

`OPENAI_BASE_URL=http://localhost:11434/v1`은 SDK task 실행 머신의 Ollama를 가리킨다. Langfuse Cloud UI의 모델 호출은 서버에서 수행하므로 이 localhost 설정을 그대로 쓸 수 없다. Cloud UI에는 접근 가능한 HTTPS 제공자 연결을 별도로 설정한다. 이 구분은 [공식 LLM Connection 안내](https://langfuse.com/docs/administration/llm-connection)를 따른다.

## Initial Setup

[setup module](../../src/hmda_reliability/reliability_ai/evaluation/setup.py)은 Prompt·합성 Dataset을 등록하는 명시적 원격 쓰기다. 먼저 remote inventory와 이름·version·label을 읽고 기존 실행 자산을 덮어쓰지 않을지 확인한다.

```bash
uv run --env-file .env python -m hmda_reliability.reliability_ai.evaluation.setup \
  --dataset hmda-reliability-ai-v1
```

다섯 한국어 seed는 text prompt로, 조사 지시는 pinned composition·canonical input·history placeholder를 갖는 chat prompt로 등록한다. 기본 label은 `production`이다. `--prompts-only`는 Dataset을 생성하지 않지만 새 Prompt version과 production label 변경을 만들 수 있다. 반복 setup은 중복 Dataset item도 만들 수 있으므로 실험 전마다 실행하지 않는다. 후보 발행은 Prompt Management에서 별도 label·version으로 수행하고 production 이동과 구분한다.

합성 corpus는 [cases.json](../../src/hmda_reliability/reliability_ai/evaluation/cases.json)에 있다. `input`에는 실행용 사례, `expected_output`에는 독립 oracle을 등록한다. Task는 `item.input`만 실행 자료로 사용하고 oracle·검토자 질문을 모델에 보내지 않는다. Score Config·Annotation Queue는 setup이 만들지 않는다.

## Run An Experiment

[experiment module](../../src/hmda_reliability/reliability_ai/evaluation/experiment.py)은 `get_client()` → versioned `get_dataset()` → 직렬 `dataset.run_experiment(task=...)` → `format()`을 사용한다. [공식 SDK 실험 안내](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)를 참고한다.

```bash
git rev-parse HEAD
uv run --env-file .env python -m hmda_reliability.reliability_ai.evaluation.experiment \
  --dataset hmda-reliability-ai-v1 \
  --dataset-version 2026-11-07T12:58:25+00:00 \
  --name bounded-investigation \
  --model qwen3.5:4b-16k-local \
  --prompt-version 1 \
  --max-tool-calls 5 \
  --workflow-budget-seconds 300 \
  --max-output-tokens 4096
```

예시의 model 태그·Prompt version·timezone-aware Dataset snapshot은 실제 서버에 존재해야 한다. Dataset version을 생략하면 시작 시각으로 고정하고 run metadata에 남긴다. 비교에는 같은 version·사례·rubric을 사용하며 실제 Prompt version·model·revision·예산을 확인한다. `-dirty` revision은 exact content identity가 아니므로 코드 비교에는 commit 또는 별도 보존한 diff가 필요하다.

사례는 `max_concurrency=1`로 직렬 실행하며 호출 횟수는 조사 선택·예산에 따라 달라진다. 각 invocation은 같은 Prompt 객체를 끝까지 사용한다. 비교에는 `--prompt-version`을 고정하고 label 이동의 영향을 배제한다. 시작의 Prompt 조회 실패는 provider 없이 `error / prompt_unavailable`로 끝난다.

모든 Dataset 항목은 metadata에 boolean `synthetic: true`가 있어야 한다. 하나라도 없거나 다른 값이면 native experiment·모델 호출 전에 exit 2로 끝난다. SDK가 task 입력·출력을 자동 기록하므로 내부 generation 관측만 끄는 것은 비합성 자료의 보호 경계가 아니다. 이 표식은 자료 소유자가 합성 입력임을 확인한 뒤 설정해야 한다.

Trusted caller는 `--dbt-manifest`와 `--dbt-run-results`를 함께 지정해 current impact 조회를 연결할 수 있다. 모델은 경로를 선택하지 않는다. 두 artifact는 같은 projection directory에 있어야 하며 shared reader lock·기존 impact API를 사용한다.

반복 실행은 Prompt·Dataset item·Score Config·Queue를 생성·수정하지 않는다. 자동 evaluator나 별도 사람 점수 완비 판정기도 없다. 전체 조사 output과 항목 ID multiset을 대조해 모든 항목이 completed일 때만 exit 0이다. 누락·중복·실패는 exit 1, 실행 자체의 실패는 exit 2다. SDK가 실패 task를 반환 결과에서 제외해도 성공으로 간주하지 않는다.

## Inspect Results And Failures

Langfuse experiment에서 항목 output과 실제 generation·tool을 연다. 두 종류는 같은 조사 아래 sibling이며 실제 호출 구간·Prompt version·model·usage·상태를 기록한다. 합성 metadata가 명시된 항목만 정제된 compiled system·history·tool IO를 원격에 보낸다. 원문은 원격 output 갱신 전에 로컬에 저장한다. Metadata에는 본문·credential·예외 원문·개인 절대 경로를 넣지 않는다.

| Local evidence | Content |
| --- | --- |
| `reliability-ai/investigations/<invocation_id>.json` | canonical input·revision·설정·실제 Prompt·메시지/digest·turn·tool·결과·trace ID |
| `reliability-ai/responses/<invocation_id>-<turn>.txt` | Runtime이 반환한 exact UTF-8 본문; tool-only 응답의 빈 bytes도 보존 |
| `reliability-ai/investigations/<invocation_id>-observations.json` | core manifest와 분리한 관측 오류; 완료 후 SDK 오류 포함 |

저장 루트는 `HMDA_RELIABILITY_ARTIFACTS_DIR`다. 공백·개행을 그대로 보존하며 실패 응답도 Runtime이 반환한 bounded 범위에서 남는다. 전체 HTTP 응답이나 내부 추론을 보존한다는 뜻이 아니다. 본문을 반환하기 전 실패에는 raw 파일이 없다.

### Diagnose A Failed Investigation

| Failure | Check |
| --- | --- |
| `prompt_unavailable` | SDK 연결·인증·prompt 이름·label을 확인한다. 로컬 seed로 자동 전환하지 않는다. |
| `provider_timeout` / `provider_connection_error` | 모델 서버와 실제 적용된 transport 설정을 확인한다. 본문이 없으면 raw도 없다. |
| `workflow_budget_exhausted` / `tool_call_budget_exhausted` | 실제 turn·시간·dispatch 수를 확인한다. 늦은 raw의 존재는 완료가 아니다. |
| `duplicate_tool_call_cycle` | 같은 도구·canonical 인자 반복과 이미 실행한 도구 결과를 읽는다. |
| `invalid_investigation_output` / `incomplete_provider_response` | 빈·invalid JSON·구조와 length/filter 종료 이유를 확인한다. |
| `invalid_review_context` | 입력 identity가 bounded context의 길이·형식 제약에 맞는지 확인한다. 원본 식별자를 잘라 대체하지 않는다. |
| `context_too_large` / `prompt_too_large` / `provider_response_too_large` | Context·누적 메시지·반환 byte cap과 모델 token context를 구분한다. |
| `response_persistence_failed` / `manifest_persistence_failed` | 보존한 partial 경로를 확인하고 필수 근거 없는 완료를 주장하지 않는다. |

`completed`는 유효한 최종 구조와 필수 로컬 근거 저장이다. 언어·사실성·유용성·사람 승인은 아니다. SDK 반환·flush와 실제 원격 적재는 다르다. Trace ID로 observation을 다시 조회해 실제 parent·Prompt version·IO·usage·실패 상태를 대조한다. 관측 장애는 core 결과 변경이나 모델 재호출을 유발하지 않는다.

## Timeouts And Availability

실험의 model·출력 token·조사 예산은 명시적 CLI 인자이며 Prompt config에서 자동 선택하지 않는다. Python API는 명시적인 Runtime·AI 설정을 받는다. [Prompt Guide](review-ai-prompts.md#settings-and-budgets)와 runner의 `--help`에서 현재 surface를 확인한다.

`LANGFUSE_TIMEOUT`은 Langfuse HTTP 대기 설정이다. 모델 timeout·core 예산·SDK flush·프로세스 종료를 하나의 wall-clock 상한으로 만들지 않는다. SDK 4.15.6의 flush에는 내부 queue 대기가 있을 수 있다. 별도 worker·watchdog·강제 외부 deadline은 제공하지 않으며 강제 종료가 필요하면 실행 환경의 job timeout을 둔다.

Native prompt cache는 SDK가 소유한다. 새 프로세스의 cache가 비어 있고 서버를 읽지 못하면 시작할 수 없다. 원격 Prompt Management가 실행 정본이라는 선택에 따른 가용성 조건이며 자체 cache·로컬 fallback을 추가하지 않는다.

## Human Evaluation

사람이 UI에서 다음 다섯 categorical 기준의 0·1·2와 의미를 설정하고 Annotation Queue에 평가할 실제 trace를 넣는다. 점수와 사유를 사례·실행에 연결하며 native compare에서 양쪽 입력·답변을 함께 읽는다. [Annotation Queues](https://langfuse.com/docs/evaluation/evaluation-methods/annotation-queues)와 [Compare Experiments](https://langfuse.com/docs/evaluation/experiments/compare-experiments)가 운영 절차를 소유한다.

| Criterion | 0 | 1 | 2 |
| --- | --- | --- | --- |
| `added_value` | 입력·초안 반복 | 유용한 누락·관찰 하나 | 추가 분석이 다음 판단을 바꿈 |
| `actionability` | 막연한 확인 요청 | 확인 대상을 특정 | 방법과 결과별 다음 행동 연결 |
| `evidence_awareness` | 없는 근거·원인 단정 | 제공 근거와 한계 인정 | 실제 근거 활용·부족한 근거 구분 |
| `uncertainty_handling` | 미확정 내용을 사실로 표현 | 불확실성 표시 | 사실·가설·판단 영향 구분 |
| `prioritization` | 순서 없는 나열 | 먼저 볼 항목 지정 | 이유와 확인 결과별 분기 설명 |

점수·comment는 사람이 입력한다. Native UI의 comment는 선택 기능이며 프로젝트가 모든 항목·동일 작성자·non-empty comment를 API로 재조회해 별도 완비 판정을 하지 않는다. 판단을 설명할 사유는 사람이 남기는 평가 근거다. Queue 완료·합계·평균은 candidate 채택이나 GitHub 승인·병합·recovery 권한이 아니다.

### Baseline And Candidate Comparison

같은 Dataset snapshot과 평가 기준을 사용하고 실제 prompt version·model·실행 조건을 고정하거나 의도한 차이로 명시한다. 실패·미평가 사례도 포함해 native compare로 읽는다. 상대 변화율·없는 근거·초안 오독·한국어 위반을 실제 문장과 대조하고 사람이 채택·거절·유지 의견과 이유를 기록한다. 로컬 `--check`·receipt·baseline 연결 gate는 제공하지 않는다.
