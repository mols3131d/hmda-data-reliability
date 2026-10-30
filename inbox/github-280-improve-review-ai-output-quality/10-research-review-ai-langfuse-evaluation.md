---
type: research
title: Review AI Evaluation With Langfuse
description: 직접 구현한 사람 평가·비교 기능을 Langfuse로 대체할 수 있는 범위와 프로젝트에 남길 검증을 조사합니다.
tags:
  - review-ai
  - langfuse
  - evaluation
---

# Review AI Evaluation With Langfuse

> [!NOTE]
> 사람의 점수·사유 입력, 검토 대기열과 실행 결과 비교는 Langfuse 기본 기능으로 맡길 수 있다. 현재 로컬 평가 모델을 줄이고, 세 단계 실행·원문 보존·평가 대상 연결 검증을 프로젝트에 남기는 방향을 권고한다. 공식 기능과 저장소 코드는 확인했지만 실제 서버 연결과 사람 평가 화면은 검증하지 않았다.

## Question

Review AI의 사람 평가와 baseline/candidate 비교를 모두 직접 구현해야 하는가, Langfuse가 맡을 기능과 프로젝트에 남겨야 할 기능은 무엇인가?

## Scope

- 조사 기준: 2026-10-29, PR #280의 코드 revision `1d03c5397bd75422cfd94b6d2ce7d67d682e7565`.
- 대상: [평가 코드](https://github.com/mols3131d/hmda-data-reliability/blob/1d03c5397bd75422cfd94b6d2ce7d67d682e7565/src/hmda_reliability/review_ai/evaluation/value.py), [현재 실행 모듈](../../src/hmda_reliability/review_ai/evaluation/live.py), [Review Spec](../../openspec/specs/reliability-agentic-review/spec.md)과 Langfuse 공식 문서. 사용자 첨부와 해당 평가 코드의 SHA-256이 같음을 확인했다.
- 산출물은 조사와 [후속 계획](11-plan-review-ai-langfuse-evaluation.md)이다. 이번 작업에서 SDK 설치, 실제 모델 호출, 원격 등록 또는 구현·명세 변경은 수행하지 않는다.

## Findings

### Native Evaluation Features Cover The Management Layer

공식 문서에서 확인한 기능과 현재 필요한 기능은 다음처럼 대응한다. 이 표는 기능 지원 근거이며 현재 프로젝트의 연동 완료를 뜻하지 않는다.

| 현재 필요 | Langfuse 기능 | 공식 근거 |
| --- | --- | --- |
| 합성 사례 관리와 반복 실행 | Dataset과 SDK Experiment | [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk) |
| 다섯 기준의 점수와 사유 입력 | Score Config와 사람 annotation, score comment | [Scores via UI](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-ui) |
| 검토 대상의 순차 처리 | Annotation Queue | [Annotation Queues](https://langfuse.com/docs/evaluation/evaluation-methods/annotation-queues) |
| 변경 전후 답변·점수 비교 | Experiment 비교 화면과 그 안의 annotation | [Compare Experiments](https://langfuse.com/docs/evaluation/experiments/compare-experiments) |
| 사람의 채택 의견 기록 | Categorical score로 `accept`·`reject`·`no_change` 표현 | [Scores Data Model](https://langfuse.com/docs/evaluation/scores/data-model) |

Categorical score를 채택 의견에 쓰는 것은 이 프로젝트를 위한 적용 제안이다. 실제 비교 대상 두 실행의 식별자를 함께 연결해야 하며, 이 점수를 GitHub 승인·병합이나 데이터 복구 권한으로 사용하지 않는다.

### Local Models Duplicate Evaluation Storage And Presentation

현재 평가 코드는 사람이 입력한 점수와 사유를 검증·집계하는 모델이다. 모델 답변의 품질을 자동으로 채점하는 엔진이 아니다. `ReviewValueAssessment`는 점수·대상을 보관하고, `ReviewValueComparisonEvidence`와 `CriterionDelta`는 양쪽 결과·합계·차이를 다시 담는다. `render_review_value_comparison_markdown()`은 별도 비교 보고서를 만든다. 근거는 위 revision의 [평가 코드](https://github.com/mols3131d/hmda-data-reliability/blob/1d03c5397bd75422cfd94b6d2ce7d67d682e7565/src/hmda_reliability/review_ai/evaluation/value.py)다.

Langfuse를 사람 평가 기록과 비교 화면의 소유자로 정하면 이 저장·집계·표현 모델은 삭제하거나 축소할 수 있다. 다섯 평가 기준의 의미와 사람의 명시적 판단은 정책으로 유지할 수 있으며, 큰 Python 모델을 유지해야만 지킬 수 있는 조건은 아니다.

### SDK Experiments Can Reuse The Existing Staged Execution

SDK 실험은 사례마다 프로젝트가 제공한 `task` 함수를 실행하고 결과를 기록한다. 기존 한국어 세 단계 함수를 그 task에 연결하는 구성이 가능하다. UI의 prompt 실험만 실행해서는 프로젝트의 누적 대화·예산·원문 저장 경로를 검증했다고 볼 수 없다. [SDK 실험](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk), [UI 실험](https://langfuse.com/docs/evaluation/experiments/experiments-via-ui)

권고하는 연결은 **Dataset 사례 → 기존 세 단계 실행 → 검증된 결과 연결 → Langfuse 사람 평가·비교**다. 한 사례 안의 단계 순서와 이전 답변은 현재 실행 코드가 계속 소유한다. Repository Markdown 프롬프트를 Langfuse Prompt Management로 옮기는 것은 이번 평가 전환 범위에 포함하지 않는다.

공식 데이터 모델은 같은 dataset item을 한 experiment에서 한 번만 취급하고 조회도 item별 최대 한 결과를 제공한다고 명시한다. 반복 평가에는 반복별 run identity가 필요하다. Dataset item ID는 upsert되므로 사례 ID만 믿지 않고 version·input digest와 사용할 dataset version을 고정해야 한다. [Experiments Data Model](https://langfuse.com/docs/evaluation/experiments/data-model)

### Project Integrity Rules Still Need A Small Boundary

Langfuse의 `comment`는 선택 항목이다. Numeric Score Config의 최솟값·최댓값만으로 0·1·2 정수만 허용한다고 볼 수도 없다. 따라서 아래 조건까지 기본 UI가 모두 보장한다고 가정하면 안 된다. [Scores Data Model](https://langfuse.com/docs/evaluation/scores/data-model), [Manual Scores](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-ui)

| 프로젝트에 남길 검사 | 이유 |
| --- | --- |
| 다섯 기준의 점수·필수 사유 완비와 중복 처리 | 개별 score의 유효성과 전체 평가의 완비는 다르다. |
| 정확한 0·1·2점 | 세 categorical 선택지를 사용하거나 읽어온 값을 별도로 확인해야 한다. |
| 사례·입력·평가 기준과 비교 조건의 일치 | 화면에서 두 실험을 선택했다고 같은 조건이라는 보장은 없다. |
| Workflow와 실제 원문·output digest의 연결 | 우리 파일의 동일성과 출처는 플랫폼이 자동으로 알 수 없다. |
| 같은 workflow의 서로 다른 output 차단 | 기존 `workflow_output_conflict` 의미를 유지해야 한다. |
| 사람이 내린 판단의 식별 | 자동 점수·API 점수를 사람의 독립 평가로 바꾸어 해석하면 안 된다. |

현재 helper도 실제 workflow manifest를 읽어 확인하지 않고 전달받은 output·식별자를 대조한다. 연동에서는 [manifest와 출력 저장](../../src/hmda_reliability/review_ai/staged/store.py)의 검증된 내용을 원격 trace·run에 연결해야 한다. 점수 화면의 평균·집계가 기존 다섯 항목 합계·차이와 같은 계산이라는 가정도 피해야 한다.

### Integration And Version Compatibility Remain Unverified

- [의존성 선언](../../pyproject.toml)의 선택 extra와 lock은 `langfuse==4.15.6`이다. 현재 Python 환경에서 distribution 조회 결과 SDK가 설치되어 있지 않아 실제 SDK 함수 계약은 검증하지 못했다.
- 최신 공식 문서는 Python SDK v4→v5의 dataset·score API 변경을 별도로 안내한다. 문서 예제를 현재 pin에 그대로 붙이거나 SDK를 자동으로 올리는 근거로 사용할 수 없다. [Python v4 → v5](https://langfuse.com/docs/observability/sdk/upgrade-path/python-v4-to-v5)
- 현재 Review AI 소스와 환경 예제에는 새 staged 결과의 Langfuse 연동이 없다. 앞서 제공하던 옛 JSON 결과 전용 projection은 제거된 상태다. 이전 도입 기록은 현재 연동 성공의 증거가 아니다.
- 실제 대상 서버의 버전·권한·기능, 전송·조회, annotation·비교 화면과 실제 사람 점수는 확인하지 않았다. 로컬 모델 완료, SDK 전송, 원격 조회, 사람의 품질 판단은 각각 별도 증거가 필요하다.

## Implications

전환은 큰 평가 도메인을 추가하기보다 Langfuse와 현재 결과를 연결하는 작은 adapter를 만드는 방향이 적합하다. Runtime AI의 provider 호출, 한국어 프롬프트·누적 대화, 시간 예산과 실패 시 원문 보존은 유지한다. 원격 기록 실패가 로컬 검토 결과를 바꾸거나 같은 모델 호출을 다시 실행하게 해서는 안 된다.

명세도 함께 정리해야 한다. [현재 Review Spec](../../openspec/specs/reliability-agentic-review/spec.md)의 `Versioned human utility evaluation`과 `Baseline and candidate utility comparison evidence`는 특정 로컬 모델을 요구한다. `Local provider response retention`은 원문 외부 projection을 금지하므로, 합성 입력·답변을 사람이 원격 화면에서 볼 수 있게 하려면 별도의 명시적 허용 범위가 필요하다. `Current review surface`의 옛 JSON 전용 projection 제거는 유지한다.

이 문서는 전환 권고이며 current contract를 바꾸지 않는다. 구현 순서·완료 조건과 미완료 확인 항목은 [전환 계획](11-plan-review-ai-langfuse-evaluation.md)이 소유한다.

## Open Questions

- 대상 서버와 선택할 SDK 버전에서 Dataset·annotation·비교와 필요한 API를 함께 지원하는가?
- 다섯 점수와 사유의 완비, 재평가 시 중복 score 선택을 실제 API와 UI에서 어떻게 확인할 것인가?
- 합성 입력·답변의 원격 표시를 허용할 필드와 실패한 단계의 표시 범위를 어디까지로 정할 것인가?
- 코드 revision 자체를 비교 변수로 삼을 때 같은 사례·rubric·입력 조건을 어떻게 고정할 것인가? 현재의 동일 revision 요구를 맞추려고 실제 SHA를 다시 쓰면 안 된다.

## Follow-Up Verification

2026-10-30 후속 구현에서 SDK 4.15.6을 설치하고 native task 실행·메모리 exporter·categorical 요청 wire를 검증했다. 근거는 [4.15.6 client source](https://github.com/langfuse/langfuse-python/blob/v4.15.6/langfuse/_client/client.py)와 설치된 해당 SDK 계약이다. 실제 서버·UI·사람 평가는 아직 미검증이다. 구현 결과와 검증 범위는 [Native Evaluation Delivery](12-report-review-ai-native-langfuse-delivery.md)를 따른다.
