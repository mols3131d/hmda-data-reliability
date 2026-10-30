---
title: "Review AI Prompt Management"
description: "한국어 Markdown seed, native composition과 실행별 prompt 고정·설정·대화 전달을 설명합니다."
categories:
  - artificial-intelligence
  - software-engineering
tags:
  - langfuse
  - modularity
  - prompt-engineering
  - review-ai
---

# Review AI Prompt Management

**실행 프롬프트의 정본은 Langfuse Prompt Management다.** Repository의 한국어 Markdown은 최초 등록용 seed다. 모델은 근거 검토 → 초안 비판 → 종합의 일반 텍스트로 답하고, 코드가 원입력 facts와 세 원문을 JSON으로 취합한다. Langfuse의 native version·label을 사용하며 v1/v2/v3 실행 모드나 로컬 fallback은 없다.

요구사항은 [Prompt Engineering Spec](../../openspec/specs/review-ai-prompt-engineering/spec.md)이, 실행은 [staged prompt module](../../src/hmda_reliability/review_ai/staged/prompt.py)이 소유한다. 최초 등록과 반복 실행은 [Evaluation Guide](review-ai-evaluation.md)를 따른다.

## Module Responsibilities

[한국어 seed](../../src/hmda_reliability/review_ai/prompt/)는 한 가지 책임을 가진 UTF-8 Markdown이다. 실제 초기 등록은 [setup module](../../src/hmda_reliability/review_ai/evaluation/setup.py)이 수행한다. Text prompt 이름은 `hmda-review-ai/`와 아래 경로에서 `.md`를 뺀 문자열이다.

| Module | Responsibility |
| --- | --- |
| [tasks/null_spike.md](../../src/hmda_reliability/review_ai/prompt/tasks/null_spike.md) | 사고 범위·검토 역할·입력 취급 |
| [policies/language.md](../../src/hmda_reliability/review_ai/prompt/policies/language.md) | 한국어 설명과 원본 식별자 보존 |
| [output/prose.md](../../src/hmda_reliability/review_ai/prompt/output/prose.md) | 일반 텍스트 출력·이전 답변 취급 |
| [guidance/numeric_fidelity.md](../../src/hmda_reliability/review_ai/prompt/guidance/numeric_fidelity.md) | 비율·변화량·threshold·기준값 0 |
| [guidance/evidence_review.md](../../src/hmda_reliability/review_ai/prompt/guidance/evidence_review.md) | 실제 근거·누락 맥락·초안 검토 |
| [policies/advisory.md](../../src/hmda_reliability/review_ai/prompt/policies/advisory.md) | 승인·실행 권한 경계 |
| [staged/](../../src/hmda_reliability/review_ai/prompt/staged/) | 세 단계의 개별 질문 |

같은 의미와 전제의 규칙은 하나의 text prompt를 공유한다. 다른 작업에 재사용할 때는 입력·출력·권한 전제가 맞는지 먼저 확인한다. 두 번째 실제 consumer가 생기기 전에 범용 agent framework를 만들지 않는다.

## Native Composition

Chat prompt는 `hmda-review-ai/evidence_review`, `hmda-review-ai/draft_critique`, `hmda-review-ai/synthesis` 세 개다. 공통 system text reference → `history` message placeholder → 현재 단계 질문 reference의 순서다. Setup은 text prompt의 실제 version을 reference에 넣으므로 공통 모듈을 수정한 뒤에는 해당 reference를 쓰는 chat prompt도 새 version으로 검토·발행한다.

Native reference 예시는 다음과 같다. `1`은 문법 예시이며 실제 등록된 version을 사용한다.

```text
@@@langfusePrompt:name=hmda-review-ai/policies/language|version=1@@@
```

Reference 해석·version 관리·cache는 Langfuse가 수행한다. 별도 include engine·자동 디렉터리 탐색·양방향 Git 동기화·자체 registry를 두지 않는다. [공식 Composability](https://langfuse.com/docs/prompt-management/features/composability)와 [Message Placeholders](https://langfuse.com/docs/prompt-management/features/message-placeholders)가 native 동작을 설명한다.

`history`의 첫 user 메시지는 불변 canonical JSON이다. 후속 단계에서는 완료된 이전 system 질문과 assistant 원문을 덧붙인다. 이전 답변은 검토 자료이며 새로운 Evidence나 확정 사실이 아니다. 모델 응답을 다시 template로 해석해 내용이 달라지지 않도록 전달 bytes를 보존한다. 사례 값과 답변이 prompt 이름·단계·system 조합을 선택하지 않는다.

각 호출 전에 system·user·assistant 전체 메시지 배열을 canonical UTF-8로 직렬화해 byte cap과 digest를 계산한다. 전체 구조와 원문이 한도를 넘으면 해당 호출 전에 거부하며 이미 완료된 raw·checkpoint는 보존한다.

## Prompt Versions And Configuration

일반 service는 시작 시 기본 `production` label의 세 chat prompt 객체를 읽고 끝까지 고정한다. 실험 CLI의 `--prompt-label`은 같은 경로의 label을 선택한다. 실험이 미리 읽은 객체를 task에 전달하면 그 experiment 안의 여러 workflow도 같은 prompt set을 공유한다. 세 remote 조회는 서버의 원자적 snapshot transaction은 아니므로 label 이동은 실행 사이에 수행한다.

각 stage record에 실제 `prompt_name`·`prompt_version`과 compiled digest를 남긴다. 같은 코드 revision이어도 remote prompt는 달라질 수 있으므로 코드 SHA만으로 프롬프트 동일성을 주장하지 않는다. 과거 실행 기록은 수정하지 않는다.

실험은 `hmda-review-ai/evidence_review`의 config를 세 단계의 공통 모델 설정으로 사용한다. 나머지 두 prompt의 config로 다른 모델을 선택하지 않는다.

| Config key | Initial value | Application |
| --- | --- | --- |
| `model` | `qwen3.5:4b-8k-local` | 실제 서버에 설치한 모델 태그. Setup `--model`로 지정 |
| `max_tokens` | `1024` | Runtime의 `max_output_tokens` |
| `timeout` | `300` | Runtime 읽기 대기 초 |

Langfuse config는 versioned JSON이며 임의의 모든 필드를 LLM 호출에 자동 적용하지 않는다. 작은 runner가 위 허용 필드만 명시적으로 Runtime 설정에 전달한다. 일반 Python API는 기존처럼 명시적인 Runtime·단계 설정을 받으며 credential은 config에 넣지 않는다.

## Timeouts And Execution Budgets

| Setting | Experiment default / owner |
| --- | --- |
| Provider endpoint·credential | `OPENAI_BASE_URL`·`OPENAI_API_KEY` |
| 연결 대기 | 10초 |
| 읽기 대기 | 첫 prompt config `timeout`, 미지정 300초 |
| 쓰기·pool 대기 | Runtime 공통 timeout 기본 30초 |
| Runtime retry | 0회 |
| 단계·workflow 예산 | 360초·1,200초 |
| 누적 prompt·반환 text byte cap | 65,536·32,768 bytes |
| Langfuse HTTP timeout | SDK의 `LANGFUSE_TIMEOUT`; 모델 설정과 별개 |

HTTP timeout은 각 네트워크 작업의 대기 한도다. 단계·workflow 예산은 monotonic clock으로 후속 시작과 응답 채택을 제한한다. 진행 중 동기 호출·원격 추론·SDK flush를 강제 종료하지 않는다. 늦게 반환된 bounded 원문도 먼저 저장한 뒤 예산 실패로 처리한다. SDK hidden retry는 0이고 Runtime이 configured retry를 소유한다. 물리 호출 상한은 `3 * (max_retries + 1)`이다.

SDK의 내부 queue 대기로 종료가 늦어질 수 있으며 별도 worker·watchdog는 없다. 실행 환경의 강제 job timeout이 필요하면 core 예산과 구분해 설정한다. 예시 값은 검증한 최적값이나 완료 보장이 아니다. 기존 `HMDA_AGENTIC_REVIEW_*`·`HMDA_LANGFUSE_*` 운영 설정은 읽지 않는다.

## Inspect And Edit

1. 최초 등록 전에는 Markdown seed의 한 책임을 편집하고 UTF-8 공백·개행을 유지한다. Setup을 반복 실험마다 재실행하지 않는다.
1. 등록 이후 운영 편집은 Prompt Management에서 수행한다. 공통 text version 변경과 이를 참조하는 chat version을 함께 검토한다.
1. Chat prompt의 Preview에서 공통 지시문·history 위치·현재 질문을 확인한다. 실제 이전 모델 답변을 다음 단계에 전달하는 것은 UI placeholder 자체가 아니라 작은 세 단계 task다.
1. 실제 generation input에서 canonical JSON·이전 원문·전체 system 지시와 실제 prompt version을 확인한다. 로컬 stage record의 digest와 출처를 연결한다.
1. [관련 테스트](../../tests/review_ai/test_staged_prompt.py)를 실행하고 배포 seed 변경 시 wheel 리소스를 확인한다. Offline 검사는 한국어 준수나 설명의 유용성을 입증하지 않는다.
1. 모델 출력의 품질 변화는 같은 Dataset snapshot·실행 조건에서 [native compare와 사람 평가](review-ai-evaluation.md#baseline-and-candidate-comparison)로 판단한다.

Prompt 조회가 실패하면 `unavailable / prompt_unavailable`이며 모델 호출을 시작하지 않는다. SDK cache가 비어 있는 새 프로세스는 서버에 연결할 수 있어야 한다. 로컬 seed를 조용히 실행하거나 자체 fallback version을 고르지 않는다.
