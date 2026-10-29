---
type: plan
title: Review AI Langfuse Evaluation Plan
description: 기존 한국어 3단계 검토를 Langfuse 실험과 사람 평가에 연결하고 프로젝트 평가 중복을 제거할 구현 순서와 검증 조건을 정리합니다.
tags:
  - review-ai
  - langfuse
  - human-review
  - evaluation
---

# Review AI Langfuse Evaluation Plan

**Langfuse Dataset·SDK experiment에서 기존 한국어 3단계 검토를 실행하고, 관측·사람 점수·비교 화면은 Langfuse 기능을 사용한다.** 프로젝트에는 검토 실행·로컬 원문 보존·예산·대상 연결과 평가 완비 검사만 남기는 계획이다. 이 문서는 구현이나 원격 실행을 승인·완료한 기록이 아니다.

## Basis And Open Dependencies

- Planning baseline: `1d03c5397bd75422cfd94b6d2ce7d67d682e7565`.
- 조사 근거: [Langfuse Evaluation Research](10-research-review-ai-langfuse-evaluation.md). 정본은 현재 [Review AI Spec](../../openspec/specs/reliability-agentic-review/spec.md)이며 이 계획이 대신하지 않는다.
- 현재 dependency 선언은 `langfuse==4.15.6`이다. 작업 환경에는 optional SDK가 설치되지 않아 실제 함수 계약은 확인하지 못했다.
- 최신 [SDK experiment 문서](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)는 Python v4→v5 변경을 안내한다. 예제 API를 현재 pin에 그대로 적용하지 않는다.
- 대상 서버의 버전·기능·권한, 실제 compare UI·Annotation Queues 동작, 원격 적재와 사람 점수는 모두 미확인이다.

## Responsibility Split

| Owner | 맡길 책임 |
| --- | --- |
| Langfuse Dataset | 버전이 고정된 합성 사례, 검토자용 기대값과 사례 식별 |
| SDK experiment task | 기존 검토 함수를 사례별로 호출하고 실행·trace를 연결 |
| Langfuse trace / observation | 전체 사례와 세 단계의 입출력·상태·시간·usage 확인 |
| Score Configs / UI | 다섯 기준의 사람 점수와 comment 입력 |
| Compare / Annotation Queues | 실행별 답변 대조와 검토자 작업 배분 |
| 프로젝트 | 불변 입력·한도·실패·로컬 원문·digest 연결과 평가 완비 검사 |
| 사람 | 사실성·검토 가치 판단, 채택 결정과 GitHub 승인·병합 |

현재 Markdown 프롬프트 정본과 세 단계 history는 유지한다. Langfuse Prompt Management로 프롬프트를 이전하거나 모델에 JSON 응답을 다시 요구하지 않는다. Native 기능의 근거는 [Scores via UI](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-ui)와 [Annotation Queues](https://langfuse.com/docs/evaluation/evaluation-methods/annotation-queues)를 따른다.

## Target Flow

1. 합성 corpus를 Dataset에 등록하고 dataset/item/version, case/version과 실행 출처를 제외한 사례 payload digest를 고정한다.
1. SDK experiment task는 허용된 `review_input`만 기존 `review_null_spike()`에 전달한다. Fixture의 `project_revision` 표식 대신 해당 실행의 실제 SHA를 사용한다. `expected_output`·oracle·합성 controls는 모델 입력·history에 넣지 않는다.
1. 최초 구현은 사례를 직렬 실행한다. 기존 단계·workflow 예산과 Runtime retry 한도를 유지하고 SDK가 모델 호출을 중복 재시도하지 않는지 검증한다.
1. 전체 사례 trace 아래에 세 단계 observation을 연결한다. 원문은 검증된 로컬 파일·결과를 읽는 얇은 adapter로 연결하며 본문 없는 `on_progress` payload는 확장하지 않는다.
1. 세 단계 collection과 로컬 digest를 실험 결과에 연결한다. 검토자는 실제 입력·원문·단계 실패를 확인한 뒤 다섯 점수와 rationale을 작성한다.
1. Native compare 화면에서 같은 사례를 대조한다. 프로젝트는 평가 자료의 연결과 완비 여부만 확인하고 점수·사람 판단을 생성하지 않는다.

SDK의 자동 입출력 캡처에 전체 함수 인자·설정 객체를 넘기지 않는다. 모델 호출은 현재 Runtime adapter를 사용하며 Langfuse 예제를 복사해 별도 provider 경로를 만들지 않는다.

## Scores And Completion

기준 이름은 `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`을 유지한다. `rubric_v1` 설명과 기준별 Score Config ID·설정 snapshot을 연결한다.

- 0·1·2에 대응하는 세 범주만 허용하는 `CATEGORICAL` 설정을 우선 검증한다. 실제 SDK·서버의 값 반환 방식과 매핑이 확인돼야 채택한다.
- `NUMERIC`의 min=0/max=2만으로 정수 제한을 보장한다고 쓰지 않는다. 완비 검사에서도 고정 config 매핑과 정확한 0·1·2를 확인하고 소수·boolean·알 수 없는 값은 거부한다. [Score data model](https://langfuse.com/docs/evaluation/scores/data-model)
- UI의 comment는 선택 입력이므로, 프로젝트 완비 검사는 기준별 공백이 아닌 rationale/comment를 요구한다. 사람이 설명을 생략하면 평가 미완료로 남긴다.
- 한 검토자·대상 결과·rubric의 다섯 기준을 확인한다. 누락·중복·충돌, 잘못된 Config ID, 다른 output digest와 연결된 점수는 완료로 처리하지 않는다.
- 서버가 제공하는 annotation source·작성자·시각을 확인한다. 자동 evaluator 점수를 사람 점수로 대체하지 않으며 작성자 확인의 실제 제공 범위도 첫 단계에서 검증한다.
- Queue의 완료 표시와 프로젝트의 평가 완비 판정은 구분한다. 실제 입력·단계 답변·검토자용 기대값에 접근 가능한지도 UI에서 확인한다.
- 비교의 채택 의견은 candidate 결과를 대상으로 별도 native categorical `accept`·`reject`·`no_change`와 사람이 작성한 사유/comment로 기록한다. 양쪽 run identity·output digest와 연결해 검증하며, 다섯 점수로 채택 의견을 자동 생성하지 않는다.

Compare UI의 기준별 평균·분포는 기존 합계·`total_delta`와 같은 값이 아니다. 평균 향상으로 중요 사례의 수치 오류·실패·미평가를 숨기지 않는다. [Compare experiments](https://langfuse.com/docs/evaluation/experiments/compare-experiments)

## Identity And Comparison

- dataset/item/version과 case/version, rubric/Score Config snapshot을 연결한다. 비교용 사례 payload는 `incident`·`evidence`·`draft` 등 고정된 필드로 정의하고 실행 출처를 제외해 별도 digest를 산출한다.
- 사례 payload digest는 양쪽에서 같아야 한다. 각 실행의 canonical input digest는 실제 `project_revision`을 포함한 본문 그대로 따로 산출·보존하며 동일 값을 강요하지 않는다. 코드 SHA가 변경 변수이면 허용한 차이가 실제 revision 차이인지 검증한다.
- DatasetItem ID는 upsert 대상이므로 입력 변경을 같은 사례로 숨기지 않는다. Dataset version을 고정하고, 한 experiment의 같은 item 결과를 덮어쓰지 않도록 반복마다 별도 run identity를 사용한다. [Experiment data model](https://langfuse.com/docs/evaluation/experiments/data-model)
- 각 실행에는 실제 application SHA, 프롬프트 식별·digest, 모델·context·Thinking·예산·retry·반복 조건과 workflow/trace/observation/output digest를 기록한다.
- 같은 workflow identity가 서로 다른 output digest를 가리키면 연결 충돌로 차단한다. 이 무결성 검사는 로컬 평가 모델 제거 후에도 얇은 검사와 회귀로 유지한다.
- baseline/candidate는 같은 입력·사례·rubric으로 비교하고 의도한 변경 변수를 먼저 명시한다. 코드 SHA가 변경 변수이면 양쪽 실제 SHA를 보존한다.
- 같은 SHA나 digest를 만들려고 revision·ID를 바꾸거나 기존 canonical input·digest를 정규화해 다시 쓰지 않는다. 사례 payload·rubric이 다르면 직접 개선 비교를 보류한다.
- 실행 실패·누락 사례·미평가도 분모에 남긴다. 이전에 승인된 baseline과 새 candidate를 명시하고 UI 선택만으로 채택·CI gate를 만들지 않는다.

## Policy Changes Before Transmission

현재 Spec은 로컬 평가 모델과 raw 외부 전송 금지를 요구한다. 실제 원문을 Langfuse에서 읽으려면 아래 변경을 먼저 OpenSpec으로 명문화해야 한다. **이 계획만으로 현재 전송 금지가 해제되지 않는다.**

| Current owner | 계획할 변경 |
| --- | --- |
| Purpose / Local response retention | 외부 평가 연동과 명시적 opt-in 합성 입력·단계 텍스트 전송 허용 범위 |
| Human utility evaluation / Comparison | 로컬 거대 평가 모델 대신 native 사람 점수·비교와 얇은 완비 검사 |
| CLI configuration / 개발 가이드 | SDK·서버·실험 설정과 실제 전송 범위·실패 해석 |

Current review surface의 금지는 옛 JSON 전용 Langfuse projection에 대한 것이다. 이를 새 staged 통합까지 이미 금지한다고 확대 해석하지 않으며, 옛 projection·호환 wrapper·버전 fallback을 부활시키지도 않는다.

승인될 전송 allowlist는 합성 입력, 실제 단계 텍스트와 코드 collection의 필요한 필드로 한정한다. 본문은 명시적 input/output 필드로 보내고 metadata에는 식별자·digest·상태·검증된 설정만 둔다. Credential·개인 절대경로·provider 예외 원문·전체 설정 객체는 로그와 전송 자료에 넣지 않는다. 로컬 create-only 원문은 계속 보존한다.

## Failure Semantics

- 로컬 검토 status와 외부 관측 전송 status를 분리한다. 인증·네트워크·flush 실패가 이미 저장한 원문이나 core 결과를 덮어쓰지 않는다.
- 전송·flush에는 검토 실행과 구별되는 대기 한도를 정한다. 비활성 실행·일반 import·기본 테스트는 SDK 설치나 제공자·Langfuse 연결을 요구하지 않는다.
- SDK 제출·flush 반환은 원격 UI 적재 확인이나 사람 평가 완료가 아니다. 원격 객체 ID와 실제 조회 증거를 별도로 남긴다.
- 모델이 timeout·connection error로 본문을 반환하지 않으면 답변·성공 observation을 만들지 않는다. 앞선 단계와 실패 정보만 보존한다.
- 늦은 원문·부분 실패·저장 실패는 기존 의미를 유지한다. SDK 예외도 안전한 분류만 기록하고 credential·개인 경로를 포함한 원문은 출력하지 않는다.
- 전송 재시도와 experiment 재실행을 구별한다. 전송 실패 복구 때문에 모델을 다시 호출하거나 기존 workflow를 덮어쓰지 않는다.

## Implementation Sequence

- [ ] 대상 서버·권한과 SDK 버전을 선택한다. 실제 환경 설치 후 experiment task·trace/step·score·queue 계약을 검증하고 pin 유지 또는 변경 근거를 남긴다.
- [ ] 위 전송·평가 소유권 변경을 OpenSpec에 반영하고, 허용 필드·명시적 opt-in·실패 분리를 결정한다. 새 실행 API·명령은 이 단계 전 임의로 가정하지 않는다.
- [ ] Dataset 연결과 SDK task·단계 adapter를 추가한다. 입력 경계·직렬 실행·기존 예산·raw 보존을 회귀 검증한다.
- [ ] 다섯 Score Config와 Annotation Queue, compare 흐름을 연결하고 얇은 평가 완비 검사를 만든다.
- [ ] [value.py](../../src/hmda_reliability/review_ai/evaluation/value.py)의 거대 평가·비교 모델, 합계/delta·Markdown 보고서와 전용 재수출·serialization golden을 제거한다. 독립 oracle·품질 corpus와 실제 무결성 회귀는 유지하고 같은 기능의 호환 wrapper는 남기지 않는다.
- [ ] 도메인·평가·환경·인간 검토 안내를 native 흐름으로 갱신한다. 과거 실행 파일은 역사 자료로 보존하고 현재 성공으로 재작성하지 않는다.
- [ ] 통제된 실제 실행과 사람 평가를 별도 수행해 아래 acceptance 증거를 남긴다. Draft·Ready·승인·병합은 기존 사람 gate로 유지한다.

## Acceptance Evidence

| Evidence level | 완료 조건 |
| --- | --- |
| SDK contract | 선택한 SDK·서버 조합에서 실제 지원 함수·필드·전송/조회 방식이 확인됨 |
| Offline regression | 기대값/controls 유출 없음, 같은 사례 payload digest와 각 실행의 실제 SHA·canonical digest 구분, 세 단계 순서·예산·부분 실패·raw 보존 유지 |
| Output integrity | 같은 workflow의 다른 output digest 연결을 차단하는 회귀가 통과하며 독립 oracle·품질 corpus는 유지됨 |
| Privacy / isolation | 자동 캡처·전송 실패·관찰자 예외에도 credential·예외 원문·개인 경로 유출이나 core 결과 변경 없음 |
| Evaluation completeness | 5개 기준·정수 범주·non-empty rationale·작성자·config/output 연결을 검증; 소수·누락·중복·불일치는 미완료 |
| Real remote evidence | 실제 사례가 Dataset 실험과 세 단계 관측에 연결되고 원격 조회·UI에서 입력/원문/실패가 확인됨 |
| Human evidence | 사람이 실제 결과에 다섯 점수·근거를 기록하고, 비교 시 양쪽 run/output digest에 연결된 별도 categorical 채택 의견과 사유를 남김 |

원격 UI가 미확인되면 원격 검증 미완료, 사람 점수가 없으면 품질 미검증으로 남긴다. 준비된 응답·가짜 점수·SDK 제출 성공을 위 두 증거로 대체하지 않는다.
