---
type: plan
title: Review AI Langfuse Native Consolidation
description: PR #280의 후속 작업 에이전트가 Langfuse 네이티브 기능을 우선 사용하고 중복 구현을 줄이기 위한 범위·판단 기준·검증 인계안입니다.
tags:
  - review-ai
  - langfuse
  - llmops
  - evaluation
---

# Review AI Langfuse Native Consolidation

> [!IMPORTANT]
> **Goal:** Langfuse가 이미 제공하는 기능은 Langfuse에 맡기고, 프로젝트 코드는 도메인 고유 실행과 신뢰 경계만 소유한다. **네이티브 API 호출 수나 삭제 줄 수를 최대화하는 것이 아니라, 전체 유지보수·운영 비용을 줄이는 것**이 목적이다. 이 문서는 PR #280의 비정본 작업 인계안이다. 항목을 무조건 구현하지 말고 현재 정본 계약, 코드, SDK 버전과 실험 근거를 대조해 필요한 변경만 수용한다.

## Starting Point

- **대상:** PR [#280](https://github.com/mols3131d/hmda-data-reliability/pull/280), `agent/feat/improve-review-ai-output-quality`. 조사 기준 HEAD `02786dc5`(2026-10-31). **착수 시 HEAD, base, 실제 원격 설정을 다시 확인한다.**
- **이미 네이티브:** Prompt Management의 text/chat composition·label·version, Langfuse Dataset과 `dataset.run_experiment(task=...)`, 실행 구간 generation, Score Config·Annotation Queue·experiment compare 운영 선택. [구현 보고서](14-report-review-ai-native-minimal-delivery.md)를 참조하며 **이미 대체된 코드를 다시 설계하지 않는다.**
- **현재 고정 버전:** `langfuse==4.15.6`. 최신 Langfuse 공식 문서에는 Python SDK v5 예제가 섞인다. 이 문서의 후보 기능도 **4.15.6과 실제 Cloud/서버에서 지원되는지** 확인한 후 사용한다. SDK 업그레이드는 별도 비용·호환성 판단 없이는 하지 않는다.
- **실제 모델 증거:** 로컬 Ollama의 3개 사례·9개 단계 `completed` 실험이 보고되어 있다. 이는 출력 보존·실행의 증거이며 **사람에 대한 유용성 검증은 미완료**다. [실행 보고서](15-report-review-ai-live-execution-validation.md), [사람 평가 가이드](02-guide-review-ai-human-guide.md) 참조.

## Responsibility Map

각 행마다 **현재 코드 → 사용 가능한 Langfuse 기능 → 최소 로컬 책임 → 전환 시 얻는 이득/잃는 보장**을 확인하고, 이득이 실제로 있는 항목만 변경한다.

| Concern | Native first | Keep locally / decision boundary |
| --- | --- | --- |
| Prompt 작성·공통 지침·배포 | Prompt Management, composition reference, message placeholders, label/version, config, Playground | 최초 seed 등록과 각 실행의 실제 prompt version 고정; bounded canonical input과 **이전 모델 원문의 실제 history 전달** |
| Dataset과 실험 순회 | Langfuse Dataset, `expected_output`, dataset version, SDK `run_experiment`와 native compare | 세 단계 `task`, 입력 검증과 독립 oracle의 모델 미주입. 반복 실행마다 Dataset을 다시 만들거나 업로드하지 않음 |
| Tracing·generation·사용량 | SDK OpenTelemetry observation 또는 공식 provider integration, prompt/model/usage linkage, UI trace | provider 호출 전/후 순서, 실패 상태와 **raw 로컬 저장 후 원격 output 갱신**. 실호출이 없는 단계에 generation을 만들지 않는지 검증 |
| 평가 기준·사람 점수·검토 큐 | Score Config, Annotation Queue, UI score/comment, experiment compare·Score Analytics | 실제 근거를 읽은 사람의 사유와 채택 판단. 자체 점수 저장소·조회기·완비 gate·비교 renderer 재도입 금지 |
| 반복 가능한 단순 채점 | **선택적** native Code Evaluators(지원·제약 확인) | 실험 후 관찰 값의 표준 라이브러리 기반 객관적 검사에만 적용. 입력 계약·보안·원문 저장의 핵심 deterministic validation을 옮기지 않음 |
| 의미·효용 채점 | **선택적** Langfuse LLM-as-a-Judge, human calibration, score comparison | 사람의 독립 평가가 먼저. Judge가 접근할 모델 endpoint·비용·동의·점수 신뢰도 검증 전에는 자동화하지 않음 |
| 실행 종료·실패 진단 | SDK 실험 결과·traces·export lifecycle 우선 | 단계/전체 예산, 타입화된 실패, 로컬 create-only raw/checkpoint/manifest, 필요한 프로세스 timeout. SDK flush와 원격 조회 완료를 동일시하지 않음 |

## Work Sequence

1. **Inventory before coding.** `evaluation/experiment.py`·`setup.py`, `staged/service.py`·`prompt.py`, `runtime_ai/provider.py`와 관련 tests를 보고 실제 중복 소유권만 표로 정리한다. [기존 축소 조사](13-research-review-ai-langfuse-reduce-custom-code.md)의 과거 파일 목록은 현재 코드로 오해하지 않는다. 네이티브로 이미 충분한 항목은 **변경 없음**으로 종료한다.
2. **Fix observability semantics only if reproducible.** 현재 `staged/service.py`는 generation context를 열고 `_run_stage()` 내부에서 호출 전 프롬프트·예산 검사를 한다. preflight 실패가 실제 모델 호출 없는 generation을 남기는지 확인한다. 재현되면 최소 변경으로 호출 경계를 바로잡고, native in-memory exporter에서 **실제 호출 수와 generation 수가 대응하는지** 검증한다. 관측 실패가 core 결과를 바꾸거나 모델을 재호출해서는 안 된다.
3. **Audit native substitutions, not blanket rewrites.** `staged/prompt.py`의 compile 후 history 치환은 원문에 포함된 `{{history}}`를 SDK가 재치환하는 문제를 회피한다. 고정 SDK에서 native placeholder만으로 **동일한 원문 bytes·역할·순서·digest**가 유지되는지 테스트해 확인될 때만 제거한다. OpenAI instrumentation wrapper도 **raw-first 저장·오류 정규화·retry·byte limit**과 양립할 때에만 현재 수동 observation을 대체한다.
4. **Keep evaluation operations in Langfuse.** 기존 UI의 다섯 사람 평가 기준으로 실제 `staged-review-4k` 사례를 평가하고 같은 Dataset snapshot·model·prompt version·revision으로 비교한다. UI가 이미 제공하는 score/queue/compare 기능을 위한 Python CLI·DB·API 재조회 계층을 만들지 않는다. UI Prompt Experiments는 개별 프롬프트 탐색에는 쓸 수 있지만 **실제 응답을 다음 호출에 전달하는 세 단계 task와 동등하지 않다.**
5. **Only then consider optional native evaluators.** 반복해서 필요한 객관적 검사에 한해 Code Evaluator를 작은 파일 없는 sandbox에서 시험한다(표준 라이브러리·네트워크 제한). 의미 평가는 사람 annotation과 먼저 대조하고, Langfuse가 접근 가능한 별도 judge 모델 연결 및 비용이 정당화될 때만 LLM-as-a-Judge를 시험한다. 로컬 `localhost` Ollama를 Cloud UI 또는 managed judge가 직접 호출할 수 있다고 가정하지 않는다.
6. **Bound upgrade decisions.** v5의 실질적 기능·유지보수 이득이 확인되면 server compatibility와 migration guide를 바탕으로 별도 변경 필요성을 제안한다. **PR #280에서 버전 변경, 신규 webhook/server, 별도 agent framework, 자체 eval runner를 기본 작업으로 추가하지 않는다.**

## Acceptance And Evidence

- **Native ownership:** 남은 자체 코드가 왜 필요한지 각 책임마다 한 문장으로 설명할 수 있다. 기능을 Langfuse UI·SDK가 이미 담당하면 이를 중복 구현하지 않는다.
- **Behavior:** 세 단계 순서, 한국어 텍스트, 실제 이전 raw history, 원입력 deterministic facts의 코드 JSON 조립, 원문 우선 create-only 저장, 실패 격리·제한·advisory 경계가 유지된다. `completed`는 품질 승인이나 원격 전송 성공을 뜻하지 않는다.
- **Observability:** provider 무호출/timeout/불완전 응답/원문 저장 실패/관측 장애에서 call count·generation·usage·원문 경로의 의미가 일치한다. SDK 실험 완료·flush·서버 UI 조회·사람 평가를 별개 상태로 취급한다.
- **Evaluation:** human scores와 판단 근거, baseline/candidate 비교에서 실패·미평가 사례도 드러난다. 객관적 test pass나 9/9 단계 완료로 유용성을 대체하지 않는다.
- **Validation:** 변경된 코드 경로의 test와 실제 고정 SDK contract test를 먼저 실행한다. 필요할 때 CI·Langfuse 실험 결과를 현재 revision에 연결한다. 직접 실행하지 않은 검증을 Pass로 기록하지 않는다. **삭제 줄 수는 보조 지표**이며, 제거된 운영 책임과 남은 위험을 먼저 보고한다.

## Operational Boundaries

- 기존 Cloud에 prompt·Dataset·version이 등록돼 있다. **`evaluation.setup`을 반복 실행하지 않는다.** 재등록은 원격 쓰기와 중복 item·label 변경 위험을 검토하고 별도 승인받아 수행한다.
- 실제 모델·원격 평가 실행은 인증정보·비용·대상 데이터 경계를 확인한 뒤 수행한다. Credential·원문·개인 경로를 metadata나 repository에 남기지 않는다.
- 이 문서는 새로운 OpenSpec 요구사항이나 병합 승인 정책이 아니다. 계약 충돌은 [정본 Spec](../../openspec/specs/reliability-agentic-review/spec.md), [Prompt Spec](../../openspec/specs/review-ai-prompt-engineering/spec.md), [평가 가이드](../../docs/development/review-ai-evaluation.md)를 우선하고 차이를 보고한다.
- 작업 결과로 **수용/보류/드랍**한 네이티브 대체 후보, 실제 제거한 중복 책임, 잔여 코드의 이유, 수행한 검증과 미검증 한계를 짧게 인계한다.

## Official Langfuse References

- [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk) · [Datasets](https://langfuse.com/docs/evaluation/experiments/datasets) · [Compare](https://langfuse.com/docs/evaluation/experiments/compare-experiments)
- [Prompt Composability](https://langfuse.com/docs/prompt-management/features/composability) · [Message Placeholders](https://langfuse.com/docs/prompt-management/features/message-placeholders) · [Instrumentation](https://langfuse.com/docs/observability/sdk/instrumentation)
- [Annotation Queues](https://langfuse.com/docs/evaluation/evaluation-methods/annotation-queues) · [Code Evaluators](https://langfuse.com/docs/evaluation/evaluation-methods/code-evaluators) · [LLM-as-a-Judge](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge)
- [Python SDK v4 → v5](https://langfuse.com/docs/observability/sdk/upgrade-path/python-v4-to-v5): 공식 최신 예시를 현재 pin과 혼용하지 않도록 버전별 검증 필요.
