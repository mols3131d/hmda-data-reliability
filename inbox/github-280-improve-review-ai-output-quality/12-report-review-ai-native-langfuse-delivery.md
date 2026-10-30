---
type: report
title: Review AI Native Langfuse Delivery
description: Native 실험·사람 annotation 연결 구현과 로컬 검증, 실제 원격 평가의 남은 조건을 기록합니다.
tags:
  - review-ai
  - langfuse
  - human-review
  - evaluation
---

# Review AI Native Langfuse Delivery

**가상 컨텍스트를 현재 한국어 세 단계 검토에 전달하고, 실험·점수·대기열·비교는 Langfuse native 기능을 사용하도록 구현했다.** 실제 데이터 적재나 dbt 실행은 하지 않는다. 결과 JSON은 코드가 조립하고 단계 원문은 로컬에 먼저 보존한다.

## Scope And Revision

- PR: [#280](https://github.com/mols3131d/hmda-data-reliability/pull/280), Draft 유지.
- 시작 revision: `33e1a45366ca35596fe09be64d38d78c19a1e971`.
- 검증 대상: 이 보고서와 함께 제출하는 native 평가 구현의 작업 트리. 검증 명령과 범위는 아래에 기록했다.
- 확인한 원격 main: `017e6c2ca30c9a439dc8c72fb34a7aba9dc39d0b`. 이 기준의 prospective merge/CI 성공은 확인하지 않았다.
- 계획: [Langfuse Evaluation Plan](11-plan-review-ai-langfuse-evaluation.md). 요구사항·설계·로컬 완료 조건은 [OpenSpec Change](../../openspec/changes/review-ai-native-langfuse-evaluation/)에 반영했다.

## Implementation

| 영역 | 변경 |
| --- | --- |
| 실행 | [experiment](../../src/hmda_reliability/review_ai/evaluation/experiment.py)이 두 opt-in을 확인하고 합성 사례 3건을 기존 세 단계 함수로 직렬 실행 |
| Native 기능 | SDK 4.15.6 Dataset snapshot·experiment task·다섯 categorical Score Config·Annotation Queue·별도 채택 의견 Config 사용 |
| 입력 경계 | 고정 사례 자료만 모델에 전달; 검토자 oracle·기대값·controls는 history에서 제외 |
| IO 연결 | [adapter](../../src/hmda_reliability/review_ai/evaluation/native_sdk.py)가 로컬 manifest·checkpoint·raw·collection을 재검증한 뒤 허용된 input/output만 전송 |
| 원격 실패 | SDK를 별도 프로세스에서 실행해 시작·사례 사이·flush 대기를 제한; 완료한 core 결과와 로컬 파일 보존 |
| 사람 평가 조회 | `--check`가 실제 원격 관측과 로컬 workflow/output digest를 대조하고 작성자·source·시각·Config·다섯 점수·사유 확인 |
| 비교 | 같은 사례 payload·Config snapshot의 양쪽 실제 revision/run/output을 연결; 사람의 별도 categorical 의견과 사유 확인 |
| 중복 제거 | 로컬 ReviewValue 모델·합계·delta·비교 Markdown·호환 loader와 전용 serialization fixture 제거 |
| 기존 실행 | 단일 합성 제공자 검증인 `evaluation.live`와 현재 한국어 Markdown 프롬프트·history·예산·원문 보존 유지 |

`canonical_input`에는 현재 revision 필드가 없다. 사례 payload digest와 실제 bounded canonical digest는 각각 그대로 계산하고 실제 SHA는 별도 provenance로 남긴다. 계획에서 revision이 canonical 본문에 포함된다고 기술했던 부분을 바로잡았다.

## Validation

| 검사 | 결과와 한계 |
| --- | --- |
| Review AI / Runtime AI | `pytest tests/review_ai tests/runtime_ai`: **300개 통과**. 준비된 응답과 모의 전송을 사용하는 회귀; 실제 모델 품질 증거 아님 |
| 실제 SDK 계약 | Pin 4.15.6의 task 실행·메모리 span·categorical wire 검증; 실제 서버·UI는 미검증 |
| 워커 경로 | 실제 워커에서 세 사례와 세 단계를 모두 실행하고 로컬 manifest 3개 보존; SDK와 provider는 준비된 응답 사용 |
| 대상·사람 점수 | 원문 변조·원격 대상 바꿔치기·pagination·자동 점수·시각 누락·중복·Config/범주/사유 불일치 검사 |
| 실패 분리 | SDK hang·막힌 stdin·core 시간 분리·외부 timeout 뒤 완료 결과 보존·예외 본문 유출 차단 검사 |
| 정적 검사 | Ruff·format·ty·Tach 확인 |
| 정본·문서 | 전체 OpenSpec strict 32/32·Markdown·Inbox 계약·diff 검사 통과 |
| 배포 | Wheel의 현재 프롬프트·사례 포함과 삭제한 모델 부재, SDK 없는 기본 import·비활성 실행 확인 |

실제 측정한 provider latency·usage는 원래 checkpoint의 값으로 연결한다. Native 관측은 결과를 보존한 뒤 내보낸 것이므로 생성 시각을 provider 실행 시각으로 해석하지 않는다. 합성 응답·사람 점수 fixture는 실제 사람 평가로 기록하지 않았다.

## Run And Review

저장소 최상위에서 [환경 예시](../../.env.example)의 제공자 설정과 Langfuse 세 값을 확인한다. 기존 `.env`를 예제로 덮어쓰지 않는다.

```bash
uv run --extra langfuse --env-file .env python -m hmda_reliability.review_ai.evaluation.experiment
```

`HMDA_AGENTIC_REVIEW_LIVE=true`와 `HMDA_LANGFUSE_ENABLED=true`가 필요하다. SDK 외부 I/O 한도는 기본 30초이며 실제 검토 실행에는 기존 provider·단계·workflow 예산을 사용한다. 상세 설정·조회·비교 명령은 [Evaluation Guide](../../docs/development/review-ai-evaluation.md#native-langfuse-experiments)를 따른다.

## Remaining Evidence

- 현재 로컬 설정에는 `LANGFUSE_BASE_URL`·`LANGFUSE_PUBLIC_KEY`·`LANGFUSE_SECRET_KEY`가 없어 실제 대상 서버 실행을 하지 않았다.
- 실제 원격 Dataset·관측 조회·UI 연결, Queue/compare 화면과 실제 사람이 작성한 다섯 점수·사유는 미검증이다.
- `submitted_unverified`는 SDK 함수 반환이다. 실제 원격 적재·UI나 사람 평가 완료로 해석하지 않는다.
- 사람은 실제 원문을 독립 oracle와 대조하고 평가를 기록한 뒤 Ready·승인·병합 여부를 별도로 결정한다. 이 구현과 로컬 테스트는 해당 결정을 대신하지 않는다.
