---
title: "Review AI Evaluation"
description: "Langfuse native 등록·실험·관측과 실제 모델 출력의 사람 평가 절차를 안내합니다."
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

**Prompt Management·Dataset 실험·관측·사람 평가는 Langfuse가 소유한다.** 프로젝트에는 세 단계 대화 task와 Runtime 호출, 실패 원문 보존·checkpoint·코드 JSON 취합만 남긴다. 실제 HMDA 적재나 dbt 실행 없이 합성 컨텍스트를 모델에 전달한다.

정본은 [reliability-agentic-review](../../openspec/specs/reliability-agentic-review/spec.md), 프롬프트는 [Prompt Guide](review-ai-prompts.md), 일반 검증은 [Testing Guide](testing.md)를 따른다. SDK는 `langfuse==4.15.6`이다. 대상 서버 호환성을 확인하지 않고 v5 예제로 바꾸지 않는다.

## Offline Suite

```bash
uv sync
uv run pytest tests/review_ai tests/runtime_ai
```

기본 suite는 fake SDK·transport와 임시 artifact root를 사용한다. 원격 prompt 고정·history·입력 한도·원문 보존·기계적 JSON·예산·호출 구간 관측을 검사하며 실제 원격 등록이나 모델을 호출하지 않는다. Fixture 통과는 모델 품질이나 사람의 평가 증거가 아니다.

## Configure Connections

PR을 시험할 때는 해당 PR checkout의 repository root를 사용한다. [환경 예제](../../.env.example)를 참고해 `.env`에 `LANGFUSE_BASE_URL`, public/secret key와 `OPENAI_BASE_URL`, `OPENAI_API_KEY`를 설정한다. 사용 중인 파일을 예제로 덮어쓰지 않고 자격 증명을 Git·로그·문서에 복사하지 않는다.

표준 `LANGFUSE_*`는 SDK가 읽는다. 별도 Langfuse opt-in·기존 live 환경·SDK extra 설치는 없다. 아래 명령의 명시적 실행이 원격 등록과 모델 호출을 시작한다. Import와 기본 테스트는 실행하지 않는다.

`OPENAI_BASE_URL=http://localhost:11434/v1`은 SDK task 실행 머신의 Ollama를 가리킨다. Langfuse Cloud UI의 모델 호출은 서버에서 수행하므로 이 localhost 설정을 그대로 쓸 수 없다. Cloud UI에는 접근 가능한 HTTPS 제공자 연결을 별도로 설정한다. 이 구분은 [공식 LLM Connection 안내](https://langfuse.com/docs/administration/llm-connection)를 따른다.

## Initial Setup

[setup module](../../src/hmda_reliability/review_ai/evaluation/setup.py)은 최초 Prompt·합성 Dataset을 등록하는 명시적인 원격 쓰기다. 실행할 모델 태그가 서버에 설치되어 있는지 먼저 확인한다.

```bash
uv run --env-file .env python -m hmda_reliability.review_ai.evaluation.setup \
  --model qwen3.5:4b-8k-local
```

한국어 Markdown 모듈은 text prompt로, 세 단계는 composition reference·history placeholder를 갖는 chat prompt로 등록한다. 기본 label은 `production`이다. 실행 모델·`max_tokens=1024`·읽기 `timeout=300` 시작값은 `hmda-review-ai/evidence_review`의 versioned config에 둔다. 이후 운영 편집과 label 이동은 Prompt Management에서 수행한다. 재실행은 새로운 prompt version과 중복 Dataset item을 만들 수 있으므로 반복 실험 전마다 setup을 실행하지 않는다.

합성 corpus는 패키지의 [cases.json](../../src/hmda_reliability/review_ai/evaluation/cases.json)에 있다. Dataset의 `input`에는 실행용 사례를, `expected_output`에는 독립 oracle을 등록한다. Oracle은 검토자 자료이며 task는 `item.input`만 provider 입력으로 사용한다. Score Config·Annotation Queue는 setup이 만들지 않는다.

## Run An Experiment

[experiment module](../../src/hmda_reliability/review_ai/evaluation/experiment.py)은 공식 SDK 예제처럼 `get_client()` → `get_dataset()` → `dataset.run_experiment(task=...)` → 결과 `format()`을 사용한다. 이 두 작은 module을 기존 도메인 안에 둔 것은 프로젝트의 구성 선택이며 Langfuse가 강제하는 디렉터리 표준은 아니다. [공식 SDK 실험 안내](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)를 참고한다.

```bash
git rev-parse HEAD
uv run --env-file .env python -m hmda_reliability.review_ai.evaluation.experiment \
  --dataset hmda-review-ai-staged-v1 \
  --name staged-review \
  --prompt-label production
```

필요하면 `--dataset-version`에 서버에 존재하는 UTC snapshot 시각을 전달한다. 미지정 실행과 고정 snapshot 실행은 서로 구분해 기록한다. 비교에는 같은 Dataset version을 사용하고 각 run의 실제 prompt version·model·project revision을 확인한다. 의도한 코드 변경 비교에는 서로 다른 실제 revision을 사용할 수 있다.

사례는 `max_concurrency=1`로 직렬 실행한다. 기본 세 사례가 모두 성공하면 총 아홉 단계다. Workflow마다 세 remote prompt를 먼저 읽고 해당 객체를 끝까지 유지한다. Label이 움직여도 진행 중인 workflow가 prompt를 다시 읽지 않으며, 새 실험 실행은 새 version을 받을 수 있다. 모델 호출 전에 prompt 조회가 실패하면 `unavailable / prompt_unavailable`로 끝난다. 로컬 Markdown fallback은 없다.

실험은 Dataset item·Score Config·Queue를 자동 생성하지 않고 별도 점수 조회·완비 판정기를 실행하지 않는다. 자동 evaluator도 없다. SDK가 task와 run·비교 연결을 관리하고 결과를 표시한다. 단계 시작·종료는 stderr에 간단히 표시하며 별도 heartbeat나 모델 진행률을 추정하지 않는다.

## Inspect Results And Failures

Langfuse experiment에서 사례 output과 실제 generation을 연다. Generation은 실제 호출 구간에 생성되며 native prompt·model·usage와 합성 compiled message·반환 텍스트를 연결한다. System 지시문과 이전 history도 input에서 확인할 수 있다. 로컬 원문은 원격 output을 갱신하기 전에 저장한다. Metadata에는 본문·credential·예외 원문·개인 절대 경로를 넣지 않는다.

| Local evidence | Content |
| --- | --- |
| `agentic-review/staged/<workflow_id>/workflow.json` | 실제 revision·canonical input·설정·prompt name/version·단계 상태와 digest |
| `agentic-review/responses/<workflow_id>-<stage_id>.txt` | Runtime이 반환한 exact UTF-8 원문 |
| 단계별 `record_path` | 원문 없는 checkpoint·상태·종료 이유·시도와 시간 |
| 같은 workflow의 `output.json` | 입력 facts와 고정 순서의 `stages[{stage_id,text}]`를 코드로 취합한 JSON |

저장 루트는 `HMDA_RELIABILITY_ARTIFACTS_DIR`다. 공백·개행을 그대로 보존하며 실패 응답도 Runtime이 반환한 bounded 범위에서 남는다. 전체 HTTP 응답이나 내부 추론을 보존한다는 뜻이 아니다. 본문을 반환하기 전 실패에는 raw 파일이 없다.

### Diagnose A Failed Stage

| Failure | Check |
| --- | --- |
| `prompt_unavailable` | SDK 연결·인증·prompt 이름·label을 확인한다. 로컬 seed로 자동 전환하지 않는다. |
| `provider_timeout` / `provider_connection_error` | 모델 서버와 실제 적용된 transport 설정을 확인한다. 본문이 없으면 raw도 없다. |
| `stage_budget_exhausted` / `workflow_budget_exhausted` | 늦게 반환된 raw와 checkpoint를 읽는다. 경로 존재는 완료를 뜻하지 않는다. |
| `stage_response_empty` / `stage_response_incomplete` | 저장된 원문과 length·filter·tool 종료 이유를 확인한다. |
| `response_too_large` / `prompt_too_large` | Byte cap과 모델 context 한도를 따로 확인한다. |
| `provenance_failed` | 남은 원문·단계·output·manifest 중 어떤 저장이 실패했는지 확인한다. |

`completed`는 세 답변의 수집·저장 완료다. 언어·사실성·유용성·사람 승인과 다르다. SDK 반환·flush도 실제 원격 적재·UI 표시·사람 점수의 확인을 대신하지 않는다. 관측 전송이 실패해도 모델을 다시 호출하지 않고 이미 보존한 core 결과를 유지한다.

## Timeouts And Availability

실험의 공통 model·token·읽기 timeout은 첫 prompt의 config를 사용한다. 연결 10초·retry 0회·HTTP fallback 30초·단계 360초·workflow 1,200초와 byte cap은 현재 도메인 기본값이다. 일반 Python API는 명시적인 Runtime·단계 설정을 받는다. 세부 의미는 [Prompt Guide](review-ai-prompts.md#timeouts-and-execution-budgets)를 따른다.

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
