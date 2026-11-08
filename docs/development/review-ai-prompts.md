---
title: "Reliability AI Prompt Management"
description: "한국어 조사 seed를 native Prompt로 등록하고 실제 version·history·도구 메시지와 실행 설정을 추적하는 방법입니다."
categories:
  - artificial-intelligence
  - software-engineering
tags:
  - langfuse
  - modularity
  - prompt-engineering
  - review-ai
---

# Reliability AI Prompt Management

**실행 프롬프트의 정본은 Langfuse Prompt Management다.** 한국어 Markdown은 명시적 등록용 seed다. 조사 API·위임·Dataset task는 같은 native Prompt를 사용하며 고정 3단계 renderer나 local fallback은 없다. 요구사항은 [Prompt Spec](../../openspec/specs/review-ai-prompt-engineering/spec.md), 실행은 [investigation service](../../src/hmda_reliability/reliability_ai/investigation/service.py)가 소유한다.

## Modules And Composition

[Setup](../../src/hmda_reliability/reliability_ai/evaluation/setup.py)은 아래 다섯 [seed](../../src/hmda_reliability/reliability_ai/prompt/)를 `hmda-reliability-ai/components/` 아래 text prompt로 등록한다. 이름의 나머지는 상대 경로에서 `.md`를 뺀 값이다.

| Seed | Responsibility |
| --- | --- |
| `investigation.md` | 조사·도구 선택·종료·최종 JSON 보고 |
| `guidance/numeric_fidelity.md` | rate·percentage-point·delta·baseline zero |
| `guidance/evidence_review.md` | 실제 근거·누락 맥락·초안 대조 |
| `policies/language.md` | 한국어 narrative·원본 식별자 보존 |
| `policies/advisory.md` | 승인·mutation 권한과 자문 경계 |

Chat prompt `hmda-reliability-ai/investigation`은 version-pinned system references → `{{canonical_input}}` user 메시지 → `history` message placeholder 순서다. 실제 등록 version을 사용하는 reference 예시는 다음과 같다.

```text
@@@langfusePrompt:name=hmda-reliability-ai/components/policies/language|version=1@@@
```

공통 text를 바꾸면 이를 참조하는 chat도 새 version으로 검토·발행한다. Reference 해석·cache·version은 Langfuse가 소유한다. 별도 include engine·자체 registry·자동 Git 동기화는 없다. [Composability](https://langfuse.com/docs/prompt-management/features/composability)와 [Message Placeholders](https://langfuse.com/docs/prompt-management/features/message-placeholders)를 참고한다.

## Invocation Lifecycle

각 invocation은 시작에 필요한 chat 객체를 한 번 읽고 실제 name/version을 모든 turn에 고정한다. 기본 label은 `production`이다. CLI의 `--prompt-version`은 version을 직접 선택하며 지정하면 label 대신 사용한다. Label만 선택한 Dataset 실행은 항목 사이 label 이동의 원자적 snapshot을 보장하지 않으므로 비교 실험에서는 version을 고정한다.

Canonical input은 불변 사건의 bounded projection이다. 후속 history는 실제 assistant tool call·matching tool result와 최종 보고 요청을 유지한다. 이전 답변·도구 결과는 자료이며 system instruction·도구 범위·승인을 선택하지 않는다. 모델의 최종 JSON에서 narrative를 검증하고 canonical facts는 입력에서 유지한다. 잘못된 출력의 자동 재생성은 없다.

전체 compiled 메시지를 canonical UTF-8로 직렬화해 호출 전 byte cap·digest를 계산하고 로컬 manifest에 남긴다. 크기를 넘으면 `error / prompt_too_large`로 해당 호출을 시작하지 않는다. Prompt 조회 실패는 `error / prompt_unavailable`이며 local seed로 전환하지 않는다. SDK cache가 비어 있는 프로세스는 서버 가용성이 필요하다.

## Settings And Budgets

Prompt config의 임의 필드를 실행 설정으로 자동 적용하지 않는다. Python caller는 `RuntimeAISettings`와 `ReliabilityAISettings`, CLI는 명시적 인자를 사용한다. Credential은 환경의 `OPENAI_API_KEY`에 두며 Prompt에 저장하지 않는다.

| Concern | Owner / CLI |
| --- | --- |
| endpoint·credential | `OPENAI_BASE_URL`, `OPENAI_API_KEY` |
| model·출력 상한 | `--model`, `--max-output-tokens` |
| Prompt 선택 | `--prompt-name`, `--prompt-label`, `--prompt-version` |
| 조사 예산 | `--max-tool-calls`, `--workflow-budget-seconds`, `--max-prompt-bytes` |
| transport timeout·retry | [Runtime settings](../../src/hmda_reliability/runtime_ai/settings.py); CLI의 적용값은 [runner](../../src/hmda_reliability/reliability_ai/evaluation/experiment.py) |
| Langfuse HTTP·flush | SDK의 표준 `LANGFUSE_*`; core 예산과 별개 |

시간 예산은 monotonic clock으로 provider·tool의 후속 시작과 응답 채택을 제한한다. 늦은 bounded 원문은 보존하되 완료로 채택하지 않는다. 동기 호출·원격 추론·SDK flush·프로세스 종료의 강제 wall-clock 상한이 아니다. SDK hidden retry는 끄고 Runtime의 configured retry만 사용한다. 별도 worker·watchdog는 없다.

## Change And Compare

1. 등록 전 remote inventory와 새 이름·label의 영향을 확인한다. Setup은 반복 실험마다 실행하지 않는다.
1. 한 책임의 seed 또는 native text를 수정하고 이를 참조하는 chat version을 발행한다. Candidate label과 pinned version으로 시험하며 production 이동은 별도 채택 판단이다.
1. [조사 회귀](../../tests/reliability_ai/test_investigation_agent.py)와 [setup·실험 회귀](../../tests/reliability_ai/test_experiment_runner.py)를 실행하고 wheel의 필수 seed를 확인한다.
1. 같은 Dataset snapshot·model·예산에서 실제 baseline/candidate를 실행한다. Generation의 실제 Prompt version·system·history·tool result·usage를 manifest와 대조한다.
1. 실패도 포함해 [native compare와 사람 평가](review-ai-evaluation.md#baseline-and-candidate-comparison)로 판단한다. Offline 통과나 구조적 completed만으로 품질을 채택하지 않는다.
