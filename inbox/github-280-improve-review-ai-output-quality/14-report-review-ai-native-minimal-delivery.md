---
type: report
title: Native Langfuse Minimal Integration Delivery
description: 프롬프트·실험·관측·사람 평가를 Langfuse 기본 기능에 맡기고 직접 구현을 축소한 변경과 검증 상태를 기록합니다.
tags:
  - langfuse
  - review-ai
  - implementation
  - validation
---

# Native Langfuse Minimal Integration Delivery

**Langfuse native 기능을 실행의 기본 경로로 삼고 중복 운영 계층을 제거했다.** Prompt Management·Dataset experiment·generation·native 사람 평가를 사용하며 프로젝트에는 세 단계 대화와 Runtime 한도·로컬 원문 보존·기계적 JSON 취합을 남긴다. [조사 13](13-research-review-ai-langfuse-reduce-custom-code.md)을 사용자가 채택한 뒤의 구현 기록이다.

## Scope And Changes

| Area | Current implementation |
| --- | --- |
| Prompt | Native text composition과 history placeholder를 가진 chat prompt 세 개. `production` 기본 label·실제 version·compiled digest 보존 |
| Setup | [setup.py](../../src/hmda_reliability/review_ai/evaluation/setup.py)에서 한국어 Markdown seed·합성 Dataset을 명시적으로 최초 등록 |
| Experiment | [experiment.py](../../src/hmda_reliability/review_ai/evaluation/experiment.py)에서 `get_client()` → `get_dataset()` → `dataset.run_experiment(task=...)` → native `format()` |
| Model calls | 실제 호출 구간의 native generation에 prompt·model·전체 허용 메시지·저장된 원문·usage 연결 |
| Human evaluation | UI의 Score Config·Annotation Queue·compare. 별도 점수 조회·완비 gate·합계·비교 저장 모델 제거 |
| Configuration | 기본 SDK 4.15.6·표준 `LANGFUSE_*`·`OPENAI_BASE_URL`·`OPENAI_API_KEY`. 실험 모델·token·읽기 timeout은 첫 prompt config |
| Local evidence | 기존 raw 우선 저장·create-only checkpoint·입력 facts와 세 원문의 코드 JSON 조립 유지 |

SDK 공식 예제의 작은 task·Dataset·native 결과 표시 패턴을 따른다. 두 module을 기존 도메인의 평가 경로에 둔 것은 프로젝트의 구성 선택이며 공식 프레임워크가 강제하는 폴더 표준은 아니다. 다른 agent framework나 범용 workflow registry를 추가하지 않았다.

### Reduction

운영 평가 경로는 기존 8개 파일 **1,728줄**에서 현재 `experiment.py` 134줄·`setup.py` 106줄, 합계 **240줄**로 줄었다. 이 수치는 구현 중 측정한 공백·주석 포함 물리 줄 수이며 전체 source 크기나 품질 점수는 아니다. Runtime·단계 실행·로컬 보존 코드는 별도다.

별도 live CLI·heartbeat thread·worker·stdin protocol·watchdog·사후 관측 재구성·매 실험 bootstrap·사람 점수 API 재조회와 전용 identity/artifact/annotation 운영 모듈을 제거했다. 과거 호환 진입점이나 환경 설정 해석은 제공하지 않는다.

## Execution And Prompt Ownership

최초 등록과 반복 실험을 분리했다. Setup은 원격 Prompt·Dataset을 쓰며 재실행하면 새 version이나 중복 item을 만들 수 있다. 이후 편집·label·평가 설정은 native UI를 사용하고 반복 실험은 기존 Dataset만 읽는다. `--dataset-version`으로 고정 snapshot을, `--prompt-label`로 native label을 지정할 수 있다.

세 prompt는 `hmda-review-ai/evidence_review`, `hmda-review-ai/draft_critique`, `hmda-review-ai/synthesis`다. 시작에 읽은 객체를 고정해 실행 도중 label 이동으로 후속 prompt를 다시 읽지 않는다. Canonical JSON과 이전 질문·assistant 원문을 history로 전달하며 oracle·expected output은 모델 입력에 넣지 않는다. 실행 정본은 원격 Prompt Management이고 Markdown은 seed다. 시작에 조회하지 못하면 모델 호출 전 `prompt_unavailable`로 끝나며 fallback은 없다.

각 model generation은 실제 호출을 감싼다. 실제 input은 호출 직전에, 확인된 usage는 반환 시 기록해 timeout·크기 초과·원문 저장 실패도 조사할 수 있다. 응답 본문은 Runtime이 반환한 bounded raw를 먼저 로컬에 저장한 뒤에만 원격 output으로 갱신한다. 관측 실패를 이유로 모델을 다시 호출하지 않는다. 본문은 명시적인 input/output에만 보내며 metadata·진행 로그에 credential·원문·개인 절대 경로·provider 예외를 복제하지 않는다.

## Policy Tradeoffs

사람 점수의 동일 작성자·다섯 항목·non-empty comment를 별도 API로 다시 확인하던 gate를 제거했다. Native UI가 평가를 소유하고 사람은 실제 답변과 판단 이유를 기록한다. 운영 코드가 작아지는 대신 프로젝트 CLI가 평가 완비를 자동 증명하지 않는다. Queue 완료·점수 평균이 채택·GitHub 승인·병합·recovery 권한으로 바뀌지 않는다.

프로세스 강제 외부 deadline도 제거했다. SDK HTTP timeout·Runtime timeout·단계/전체 예산은 유지하지만 SDK flush·프로세스 종료의 wall-clock 상한을 보장하지 않는다. 강제 종료가 필요하면 실행 환경의 job timeout을 사용한다. Native prompt cache는 SDK가 소유하며 새 프로세스가 서버를 읽지 못하면 실행을 시작할 수 없다.

## Validation

아래 검증은 이 보고서와 함께 제출하는 코드·테스트 변경을 대상으로 로컬에서 실행했다. 과거 CI를 현재 변경의 증거로 소급하지 않는다.

| Check | Recorded state |
| --- | --- |
| Full suite | 관측 실패 경계 보완 전 `pytest -q -n 4`: **1,174 passed, 2 skipped** |
| Final Review AI·Runtime AI regression | 관측 실패 보완·추가 회귀를 포함한 최종 관련 suite: **216 passed**. 실제 SDK compile·task·generation을 메모리 exporter로 검증 |
| Static and packaging | 전체 Ruff·format·ty·Tach, offline lock·sync, TOML lint·설정 format, wheel build·직접 import·기본 SDK 의존성·한국어 seed·세 사례 확인 통과 |
| Documentation | OpenSpec strict **32/32**, 변경 Markdown **18개**·Inbox·`git diff --check` 통과. 개인 절대 경로 없음. 조사 13의 역사 코드 링크는 조사 기준 commit에 고정 |
| Independent review | 두 관점에서 실패 input·usage 누락 한 건을 확인해 보완했다. 세 경계 회귀 RED → GREEN 후 보완 구간의 두 관점 재검토에서 추가 필수 수정 없음. Parent assessment: `clear`. 실제 서버·UI·품질 검증은 포함하지 않음 |
| Actual Langfuse·model·UI·human review | 미검증 |

로컬 환경 파일은 표준 변수로 전환하면서 기존 provider 값을 보존했다. 해당 파일은 ignored 상태이며 commit에 포함하지 않는다. Langfuse key가 설정되지 않아 실제 원격 등록·실험을 수행하지 않았다. Secret 값은 기록하지 않았다.

Offline fake·실제 설치 SDK 계약·wheel 검사는 실행 계약의 증거다. 실제 모델의 한국어 준수·수치 정확성·검토 가치 또는 사람의 품질 판단을 입증하지 않는다. 데이터 적재·실제 모델 호출·원격 Prompt/Dataset 쓰기·사람 평가를 이번 구현 검증에서 수행하지 않았다.

## Follow Through

구체적인 명령과 실패 조사는 [현재 Evaluation Guide](../../docs/development/review-ai-evaluation.md)를, 사람이 읽을 사례·수치·다섯 기준은 [Human Review Guide](02-guide-review-ai-human-guide.md)를 따른다. 환경 예제와 [Prompt Guide](../../docs/development/review-ai-prompts.md)도 native 경계에 맞췄다. 정본 요구사항과 현재 작업 계획은 [owning OpenSpec Change](../../openspec/changes/review-ai-native-langfuse-evaluation/proposal.md)에 반영했다.

실제 서버 연결과 모델을 준비한 뒤 최초 setup → 고정 조건의 experiment → native UI 출력 확인 → 사람 평가 순서로 증거를 확보한다. 그 결과와 GitHub의 Ready·승인·병합은 별도 판단이다.
