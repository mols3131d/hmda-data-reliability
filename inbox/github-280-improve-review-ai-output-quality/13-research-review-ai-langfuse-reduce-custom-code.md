---
type: research
title: Langfuse Adoption And Custom Code Reduction
description: Langfuse 공식 기능과 현재 구현을 대조해 직접 구현을 줄일 수 있는 책임, 남겨야 할 최소 로직과 전환 조건을 조사합니다.
tags:
  - review-ai
  - langfuse
  - prompt-management
  - evaluation
---

# Langfuse Adoption And Custom Code Reduction

> [!NOTE]
> 현재 구현은 Langfuse native API를 사용하지만 자체 평가 운영 계층도 크게 남아 있다. 사용자의 목표에는 **프롬프트 관리·조합, 실험, 관측, 사람 평가·비교를 Langfuse에 맡기고, 프로젝트에는 세 단계 순서·history 전달·원문 보존·코드 JSON 조립을 남기는 방향**이 더 적합하다. 실제 세 단계 실행을 UI만으로 대체하거나 SDK timeout만으로 현재의 강제 종료 보장을 유지할 수 있다는 근거는 확인하지 못했다.

## Question

가상 컨텍스트로 한국어 세 단계 검토를 수행하는 현재 동작을 유지하면서, Langfuse 기본 기능을 최대한 사용해 어떤 자체 구현을 제거하거나 축소할 수 있는가?

## Scope

- 조사일: 2026-10-30. 공식 문서·공식 SDK 소스와 저장소 코드를 대조했다.
- 코드 기준: `ffdc9467b7cd0d283c9022c18212a681c8064854`, PR [#280](https://github.com/mols3131d/hmda-data-reliability/pull/280).
- 현재 SDK: [pyproject.toml](https://github.com/mols3131d/hmda-data-reliability/blob/ffdc9467b7cd0d283c9022c18212a681c8064854/pyproject.toml)의 `langfuse==4.15.6`. 실제 대상 서버의 버전·요금제·접속 상태는 미확인이다.
- 이전 [조사](10-research-review-ai-langfuse-evaluation.md)와 [계획](11-plan-review-ai-langfuse-evaluation.md)은 프롬프트의 저장소 관리와 기존 실행 경계를 유지했다. 이번에는 사용자의 추가 요청에 따라 **그 경계 자체도 축소 대상으로 재검토**한다.
- 이 문서는 조사·권고다. 구현·설정·정본 Spec을 변경하거나 실제 서버·모델을 실행한 결과가 아니다.

## Findings

### Native APIs Do Not Yet Mean Minimal Custom Code

현재 통합용 여섯 파일은 총 **1,142줄**이다. 공백·주석을 포함한 코드 규모이며, 줄 수 자체를 결함이나 삭제 가능량으로 해석하지 않는다. 축소 근거는 플랫폼이 제공하는 기능과 현재 코드의 책임 중복이다.

| File | Lines | 현재 자체 책임 |
| --- | ---: | --- |
| [experiment.py](https://github.com/mols3131d/hmda-data-reliability/blob/ffdc9467b7cd0d283c9022c18212a681c8064854/src/hmda_reliability/review_ai/evaluation/experiment.py) | 276 | 설정·CLI·receipt·subprocess·IPC·watchdog |
| [experiment_worker.py](https://github.com/mols3131d/hmda-data-reliability/blob/ffdc9467b7cd0d283c9022c18212a681c8064854/src/hmda_reliability/review_ai/evaluation/experiment_worker.py) | 106 | SDK lifecycle·로그 차단·부모 protocol·도메인 호출 |
| [native_sdk.py](https://github.com/mols3131d/hmda-data-reliability/blob/ffdc9467b7cd0d283c9022c18212a681c8064854/src/hmda_reliability/review_ai/evaluation/native_sdk.py) | 491 | Dataset·Config·Queue 관리, 사후 관측, 사람 점수 조회 |
| [artifacts.py](https://github.com/mols3131d/hmda-data-reliability/blob/ffdc9467b7cd0d283c9022c18212a681c8064854/src/hmda_reliability/review_ai/evaluation/artifacts.py) | 106 | 보존 파일 전체 재검증 |
| [annotations.py](https://github.com/mols3131d/hmda-data-reliability/blob/ffdc9467b7cd0d283c9022c18212a681c8064854/src/hmda_reliability/review_ai/evaluation/annotations.py) | 102 | 다섯 점수·사유·작성자·대상 완비 검사 |
| [identity.py](https://github.com/mols3131d/hmda-data-reliability/blob/ffdc9467b7cd0d283c9022c18212a681c8064854/src/hmda_reliability/review_ai/evaluation/identity.py) | 61 | 자체 대상 모델·digest·비교 규칙 |

재현 명령은 저장소 root에서 `wc -l src/hmda_reliability/review_ai/evaluation/{experiment.py,experiment_worker.py,native_sdk.py,artifacts.py,annotations.py,identity.py}`다. 위 합계에는 별도의 단일 실행 CLI·진행 표시·기존 staged/Runtime 구현이 포함되지 않는다.

현재 관측에는 중요한 한계가 있다. `native_sdk.py`의 `task()`는 모델 실행이 끝난 뒤 로컬 기록을 읽어 빈 관측 context를 생성한다. 실제 latency·usage는 metadata로 보내지만 native generation의 model·usage 필드에 연결하지 않는다. 관측 input도 `canonical_input`과 이전 답변이며 실제 system 지침·단계 질문 전체가 아니다. 따라서 현재 UI를 실제 provider 실행 시간·비용·전체 프롬프트를 보여주는 계측으로 설명하면 부정확하다. 근거는 같은 파일의 `review_case()` 호출과 `start_as_current_observation()` 구간, [실제 메시지 조립](https://github.com/mols3131d/hmda-data-reliability/blob/ffdc9467b7cd0d283c9022c18212a681c8064854/src/hmda_reliability/review_ai/staged/prompt.py)이다.

### Prompt Management Can Replace The Custom Composition Layer

Langfuse는 공통 **text prompt 참조**로 프롬프트를 조합하고, chat prompt의 message placeholder에 role/content 배열을 삽입한다. 공통 한국어 지침을 모듈로 유지하면서 저장소의 자체 문자열 조립을 대체할 수 있다. 참조할 version 또는 label도 지정한다. 고정 reference는 조건 분기 실행기가 아니므로 사례 데이터가 지침을 고르게 만들 필요는 없다. [Prompt Composability](https://langfuse.com/docs/prompt-management/features/composability), [Message Placeholders](https://langfuse.com/docs/prompt-management/features/message-placeholders)

모델과 생성 파라미터는 prompt의 versioned `config`로 관리할 수 있다. 실행 코드는 허용된 값을 읽어 모델 호출에 전달해야 하며, Config에 임의 JSON을 넣었다고 모든 timeout·환경 설정이 자동 적용되지는 않는다. Credential·endpoint 연결과 생성 파라미터의 소유권도 구분해야 한다. [Prompt Config](https://langfuse.com/docs/prompt-management/features/config)

프롬프트를 각 generation에 직접 연결하면 prompt version별 결과를 UI에서 볼 수 있다. 현재의 digest만 저장하는 방식보다 프롬프트 엔지니어링 목적에 잘 맞는다. 같은 실험에서는 가져온 prompt와 하위 참조의 version을 기록·고정해 label 변경으로 조건이 섞이지 않게 하는 것이 적절하다. 이는 재현성을 위한 권고이며 native label을 새 자체 버전 시스템으로 감쌀 필요는 없다. [Link Prompts to Traces](https://langfuse.com/docs/prompt-management/features/link-to-traces)

실행 정본을 원격으로 옮기면 시작 시의 가용성 경계도 달라진다. SDK cache가 비어 있는 새 프로세스에서 API 조회까지 실패하면 `get_prompt()`는 실패할 수 있다. 개발 실험은 시작 시 필요한 prompt를 미리 조회하고 실패를 명시하는 작은 경계로 처리할 수 있다. Fallback이 필요하다면 SDK의 기본 기능과 명시적 정책을 사용하고, 예전 prompt로 조용히 돌아가는 별도 cache·레거시 경로를 만들지 않는 방향을 권고한다. [Guaranteed Availability](https://langfuse.com/docs/prompt-management/features/guaranteed-availability)

### Experiments Can Own Execution Management But The Task Still Owns Three Calls

SDK experiment runner는 사례 순회·동시성 제한·task 추적·개별 실패 격리·결과 연결을 제공한다. 프로젝트는 기존 범용 평가 실행기를 확대하기보다 작은 `task`를 제공하면 된다. 이 task의 본질은 세 번의 질문 순서, 실제 이전 응답의 history 추가와 최종 결과 반환이다. [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)

UI Prompt Experiments는 Dataset의 변수·주어진 message history와 prompt/model을 실행한다. 공식 문서는 전체 애플리케이션·agent 로직은 SDK 실험으로 실행하라고 안내한다. **미리 주어진 history를 넣는 기능과 첫 번째 생성 결과를 두 번째 호출에 자동 전달하는 기능은 다르다.** 현재 요구를 단일 prompt UI 실험으로 바꾸면 같은 실행을 시험하는 것이 아니다. [Experiments via UI](https://langfuse.com/docs/evaluation/experiments/experiments-via-ui), [공식 Evals 이전 안내](https://langfuse.com/resources/engineering/migrate-from-openai-evals)

Langfuse의 `session_id`도 관측을 묶고 재생하는 식별자다. ID를 붙이는 것만으로 모델이 이전 질의응답을 기억하는 것은 아니며, 실제 messages/history 전달은 task가 해야 한다는 것이 위 기능 구분에서 도출되는 판단이다. [Sessions](https://langfuse.com/docs/observability/features/sessions)

UI에서 SDK 실험을 시작하는 Remote Experiment Trigger도 있다. 다만 외부 HTTP endpoint와 비동기 실행 코드가 필요하다. 로컬 Ollama 개발 단계에서는 이를 새로 운영하는 비용이 간단한 실행 명령보다 클 수 있어 즉시 필수로 도입할 기능은 아니다. [UI에서 SDK 실험 시작](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk#optional-trigger-sdk-experiment-from-ui)

### Native Instrumentation Can Replace Post-Hoc Generations

Langfuse의 OpenAI wrapper는 입력·출력·usage·latency·오류 관측을 제공하고, 공식 Ollama 예제도 OpenAI-compatible endpoint와 이 wrapper를 사용한다. 모델 호출 지점에 native 계측을 붙이면 완료 후 별도 generation을 재구성하는 코드를 줄일 수 있다. Langfuse는 모델 실행 자체를 대신하지 않으며 호출은 모델 SDK가 담당한다. [OpenAI integration](https://langfuse.com/integrations/model-providers/openai-py), [Ollama integration](https://langfuse.com/integrations/model-providers/ollama)

원문을 로컬에 저장한 뒤에만 원격 본문을 내보내야 하는 현재 정책까지 유지한다면 wrapper를 그대로 교체해 같은 순서라고 주장하면 안 된다. Native context를 실제 호출 주변에 열고 **원문 저장 후 허용된 input/output·usage를 갱신**하는 방식도 있다. 필요 없는 함수 인자·설정·예외 자동 캡처를 끄거나 제한해야 한다. 사후 파일 재생성과 실제 호출 계측은 서로 다른 설계다. [Instrumentation](https://langfuse.com/docs/observability/sdk/instrumentation)

현재의 [Runtime AI](https://github.com/mols3131d/hmda-data-reliability/blob/ffdc9467b7cd0d283c9022c18212a681c8064854/src/hmda_reliability/runtime_ai/provider.py)는 이미 OpenAI SDK를 사용하면서 retry·오류 정규화·한도를 추가한다. 이를 줄이는 경우 대체 제공자는 **OpenAI 표준 SDK**이고, Langfuse는 계측을 맡는다. 세 단계만을 위해 새 agent framework까지 도입하는 것은 이번 최소화 목표의 필수 조건이 아니다.

### Evaluation Operations Can Move To The Native UI

다음 표는 현재 기능과 공식 기능의 대응을 바탕으로 한 **축소 권고**다. 파일 전체의 무조건 삭제나 동등 보장 검증 결과가 아니다.

| Current responsibility | Native replacement | 축소 방향 |
| --- | --- | --- |
| 매 실행 Dataset 생성·item 업로드·전체 비교 | Dataset UI·CSV import·version 선택 | 최초 등록과 실험 실행을 분리하고 매번 upsert하지 않기. [Datasets](https://langfuse.com/docs/evaluation/experiments/datasets) |
| 매 실행 Score Config·Queue 열거·생성·중복 검사 | UI에서 Config·Queue 설정 | 운영 초기 설정을 옮기고 실행 경로의 bootstrap 축소. [Scores via UI](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-ui) |
| 대기열 연결과 별도 평가 CLI | UI bulk/single `Add to queue`·annotation | 적은 수의 개발 사례는 UI에서 평가. 자동 배정이 실제 필요해질 때 API 사용. [Annotation Queues](https://langfuse.com/docs/evaluation/evaluation-methods/annotation-queues) |
| 자체 비교·채택 자료 취합 | experiment compare·사람 annotation | 원문과 점수·사유를 화면에서 함께 검토. 별도 비교 저장 모델을 다시 만들지 않기. [Compare Experiments](https://langfuse.com/docs/evaluation/experiments/compare-experiments) |
| 일반적인 출력 형식·키워드 검사 | native Code Evaluators | 실제 필요한 결정론적 평가만 등록. 새 실행 인프라 비용과 runtime 제한 먼저 확인. [Code Evaluators](https://langfuse.com/docs/evaluation/evaluation-methods/code-evaluators) |

특히 `--check`의 전체 사람 평가 완비 판정은 Langfuse 사용에 필수인 기능이 아니라 현재 프로젝트가 정한 정책이다. UI에서 사람이 검토하고 판단하는 운영이면 해당 CLI와 광범위한 조회·파일 재검증을 없애거나, 제출 시의 작은 검사로 제한할 수 있다.

반대로 UI의 comment는 선택 사항이다. **다섯 점수 각각의 사유 필수·동일 작성자·중복 금지까지 네이티브가 보장한다고 가정해서는 안 된다.** 이 조건을 자동 gate로 계속 요구하면 작은 자체 검사가 남고, 제거하려면 해당 운영 정책도 바꿔야 한다. [사람 점수 입력 계약](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-ui)

Code Evaluator도 직접 작성한 검사 코드를 플랫폼에서 실행하는 기능이다. 현재 공식 문서는 표준 라이브러리만 허용하고 외부 네트워크를 제한하며, self-hosted에서는 별도 dispatcher 설정이 필요하다. 프로젝트의 Pydantic·로컬 원문 파일 감사를 그대로 올릴 수 없고, 사람의 의미 판단을 대체하지도 않는다. [실행 제약](https://langfuse.com/docs/evaluation/evaluation-methods/code-evaluators), [Self-hosted 설정](https://langfuse.com/self-hosting/configuration/code-evaluators)

### Local Raw Retention And Hard Deadlines Are Separate Requirements

Langfuse가 관측을 보관해도 네트워크 단절 때의 로컬 원문 보존은 대신하지 못한다. 사용자가 요구한 실패 조사 목적에는 **응답이 반환되면 의미 판정 전에 원문을 저장하는 작은 경계**를 남기는 것이 적절하다. [현재 저장 순서](https://github.com/mols3131d/hmda-data-reliability/blob/ffdc9467b7cd0d283c9022c18212a681c8064854/src/hmda_reliability/review_ai/staged/service.py)와 [원문 저장소](https://github.com/mols3131d/hmda-data-reliability/blob/ffdc9467b7cd0d283c9022c18212a681c8064854/src/hmda_reliability/review_ai/store.py)를 참고한다. 본문 없이 실패하거나 Runtime이 크기 초과로 차단한 경우에는 보존할 본문이 현재 호출자까지 반환되지 않는다는 한계도 유지된다.

하지만 모든 실행에서 manifest·checkpoint·raw·output을 다시 읽고, 점수 조회에서도 다시 감사하는 구조까지 원문 보존 자체에 필수인 것은 아니다. Native experiment/item/trace와 실제 commit·prompt version을 연결하고 상세 파일 감사는 필요할 때 수행하도록 분리할 수 있다. 어느 수준까지 보장할지는 구현 제약이 아닌 정책 선택이다.

프로세스 watchdog도 별도 선택이다. 프로젝트에 고정한 SDK 4.15.6은 `run_experiment()` 말미에 `flush()`를 호출하고 resource manager가 queue `join()`을 기다린다. HTTP timeout은 전체 SDK lifecycle의 강제 종료 한도와 같지 않다. [고정 SDK client](https://github.com/langfuse/langfuse-python/blob/v4.15.6/langfuse/_client/client.py), [고정 resource manager](https://github.com/langfuse/langfuse-python/blob/v4.15.6/langfuse/_client/resource_manager.py)

| Policy | 자체 실행 코드에 미치는 영향 |
| --- | --- |
| SDK가 멈춰도 정해진 시각 안에 강제 종료 | 최소 프로세스 경계 또는 외부 실행기의 timeout이 필요. 현재 watchdog을 단순 SDK 옵션으로 동등 대체했다고 볼 수 없음 |
| 개발 실험은 native export lifecycle·유한 요청 timeout·명시적 중단 수용 | 자체 worker·JSON IPC·phase watchdog 제거 후보. 강제 종료 보장은 완화됨을 명시 |

SDK의 flush와 실제 원격 조회 가능 시점도 다르다. 전송 성공·UI 가시성·사람 평가를 하나로 합쳐 성공 판정하지 않는 원칙은 유지할 수 있으며, 이를 위해 매번 큰 조회 프레임워크가 필요한 것은 아니다. [SDK lifecycle와 비동기 적재](https://python.reference.langfuse.com/langfuse)

### Version And Deployment Affect The Smallest Design

조사일의 PyPI 최신 Python SDK는 **5.0.4**다. 현재 4.15.6에서도 chat placeholder·prompt config/cache·실험 runner가 있으므로, 프롬프트 관리 도입 자체가 v5 업그레이드를 요구하지는 않는다. 고정 버전의 `ChatPromptClient.compile()`과 `Langfuse.get_prompt()`를 직접 확인했다. [PyPI](https://pypi.org/project/langfuse/), [4.15.6 prompt client](https://github.com/langfuse/langfuse-python/blob/v4.15.6/langfuse/model.py)

최신 문서의 v5는 Cloud 또는 self-hosted Langfuse **v4.59.0 이상**, Python 3.11 이상을 요구한다. 현재 사용 중인 `get_dataset_run()` 등 helper와 일부 score API가 변경·제거됐으므로 단순 pin 변경으로 끝나지 않는다. 서버가 지원하면 v5로 옮겨 현재 실험 API를 쓰는 편이 장기 유지에는 유리하다는 것이 권고이며, 서버 미확인 상태에서 자동 업그레이드할 근거는 아니다. [Python v4 → v5](https://langfuse.com/docs/observability/sdk/upgrade-path/python-v4-to-v5), [호환성 표](https://langfuse.com/docs/compatibility)

로컬 Ollama를 사용할 때도 실행 위치를 구분해야 한다. 로컬 SDK task는 로컬 모델 endpoint를 호출하고 관측만 Langfuse로 보낸다. Playground/UI 실험의 모델 호출은 Langfuse 서버에서 발생한다. Cloud LLM Connection은 public HTTPS endpoint를 요구하고 loopback/private endpoint 예외를 허용하지 않으므로 개발 PC의 `localhost`를 그대로 사용할 수 없다. Self-hosted는 필요한 내부 endpoint를 명시적으로 허용하는 구성이 가능하다. [LLM Connections](https://langfuse.com/docs/administration/llm-connection)

플랫폼 도입이 특정 유료 계약을 무조건 요구하지는 않는다. Core self-hosted 기능과 Cloud 요금제의 사용자·보관 기간·queue 수 제한을 구분하고 실제 계정을 확인해야 한다. 불필요한 별도 서버나 gateway 운영까지 포함하면 Python 코드가 줄어도 전체 운영 부담은 커질 수 있다. [Cloud 가격표](https://langfuse.com/pricing), [Self-hosted 기능](https://langfuse.com/pricing-self-host)

## Options

| Option | 자체 구현 | 기존 세 단계와의 관계 | 판단 |
| --- | --- | --- | --- |
| 현재 경계 유지 | 사후 관측·bootstrap·조회·watchdog 유지 | 현재 동작 유지 | native API 사용은 충족하지만 이번 최소화 목표에는 부족 |
| Prompt Management + native 계측 + SDK task | 세 단계 연결·원문 보존·JSON 조립과 필요한 최소 검증 | 실제 앞선 응답을 다음 단계에 전달 | **권고**. 강제 종료·정본 정책을 함께 결정해야 함 |
| Playground/UI Prompt Experiments만 사용 | 실행용 Python 코드를 크게 줄임 | 제공된 history를 이용한 개별 prompt 실험. 현재 전체 세 단계와 동등하지 않음 | 프롬프트별 탐색·검토용으로 병행 |

프롬프트 정본도 선택해야 한다. 직접 구현 최소화에는 **Langfuse Prompt Management를 실행 정본으로 두고 기존 한국어 Markdown 내용을 모듈 prompt로 옮기는 방향**을 권고한다. Git 파일을 계속 정본으로 유지하려면 작은 단방향 publish 단계가 필요하다. 공식 GitHub 연동은 Langfuse의 변경 event를 보내는 방향이며 저장소를 자동으로 읽는 양방향 동기화가 아니다. 두 편집 경로를 동시에 정본으로 만들거나 새 동기화 서버를 기본으로 추가하지 않는다. [GitHub Integration](https://langfuse.com/docs/prompt-management/features/github-integration)

## Implications

최소 구성을 판단하기 위한 개념적 실행 순서는 다음과 같다. 완성 코드나 검증된 전환 결과는 아니다.

1. Dataset·다섯 Score Config·Queue와 한국어 prompt 모듈을 Langfuse에서 준비한다.
1. SDK experiment가 고정 Dataset version에 대해 작은 task를 실행한다.
1. Task가 세 단계의 native chat prompt를 compile하고 실제 이전 답변을 history에 추가한다.
1. 모델 호출 지점에서 관측하고 반환 원문을 보존한 뒤 facts와 세 텍스트를 코드로 JSON에 조립한다.
1. 사람은 native experiment/compare/annotation UI에서 읽고 평가한다. 별도 로컬 평가 저장·집계·화면을 만들지 않는다.

우선 축소 후보는 매 실행 bootstrap·사후 generation 재생성·항상 수행하는 사람 점수 조회/전체 파일 감사다. 프롬프트 조회·캐시·재시도도 SDK가 제공하는 것을 사용한다. CLI는 필요하다면 실행과 링크 출력만 하는 얇은 진입점으로 두고, heartbeat가 필요한 경우 실제 단계 시작·종료의 작은 로그를 남긴다. UI 관측이 터미널 heartbeat나 모델 내부 진행률을 보장한다고 설명하지 않는다. [SDK prompt cache](https://langfuse.com/docs/prompt-management/features/caching), [조회 timeout/retry](https://langfuse.com/faq/all/error-handling-and-timeouts)

현행 [프롬프트 Spec](https://github.com/mols3131d/hmda-data-reliability/blob/ffdc9467b7cd0d283c9022c18212a681c8064854/openspec/specs/review-ai-prompt-engineering/spec.md)과 [Review Spec](https://github.com/mols3131d/hmda-data-reliability/blob/ffdc9467b7cd0d283c9022c18212a681c8064854/openspec/specs/reliability-agentic-review/spec.md)의 `Verified model IO observation linkage`, `Versioned human utility evaluation`, `Independent bounded external evaluation IO`는 저장소 정본·전송 전 로컬 파일 검증·system 본문 미전송·기계적 완비 검사·외부 대기 한도를 고정한다. 빈 관측 context를 실행 후 만드는 현재 구현 방식 자체가 Spec의 필수 조건은 아니다. 다만 전체 prompt 연결이나 파일 재검증·watchdog 제거까지 하려면 관련 정책도 명문화해 바꿔야 한다. **현재 Spec 때문에 존재하는 코드와 사용자 목표에 본질적으로 필요한 코드를 동일시하지 않는 것이 이번 조사의 핵심 판단이다.**

전환 검증은 줄 수 목표보다 다음 동작에 둔다. 한국어 모듈과 실제 컴파일 입력·prompt version이 UI에서 연결되는지, 세 호출의 실제 history가 유지되는지, 실패 응답도 원문으로 남는지, JSON이 코드에서 조립되는지, UI에서 다섯 항목과 사유를 기록할 수 있는지 확인한다. 실제 SDK/server 조합으로 확인하기 전에는 삭제 가능 줄 수·품질·시간·비용 개선을 수치로 약속하지 않는다.

## Open Questions

- 실제 대상은 Cloud인가 self-hosted인가? 서버 버전과 UI·LLM endpoint 접근성이 있어야 SDK 버전과 Playground 사용 범위를 결정할 수 있다.
- 프롬프트의 실행 정본을 Langfuse로 옮길 것인가, Git Markdown을 유지하고 단방향 publish할 것인가?
- 개발용 실험에도 SDK의 강제 종료 한도와 다섯 사람 점수의 기계적 완비 gate가 필요한가? 유지 여부가 삭제 가능한 자체 코드 규모를 크게 바꾼다.
- 실제 Ollama 모델에서 compile된 메시지·종료 이유·usage·prompt 연결과 실패 원문 보존이 기대대로 동작하는가? 문서 조사와 서버 실증은 별도다.
