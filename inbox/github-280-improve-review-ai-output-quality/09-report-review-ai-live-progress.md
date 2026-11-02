---
type: report
title: Review AI Live Validation Progress
description: 실제 모델 통합 검증을 평가 모듈로 옮기고 실행 중 안전한 단계·대기 표시를 추가한 변경과 검증 결과입니다.
tags:
  - review-ai
  - evaluation
  - observability
---

# Review AI Live Validation Progress

기존 실행 도구는 합성 사례를 실제 모델로 검증하지만 `scripts/`에 분리되어 있었고 모델 응답을 기다리는 동안 진행 상황을 표시하지 않았다. 실행 진입점을 [evaluation/live.py](../../src/hmda_reliability/review_ai/evaluation/live.py)로 옮겨 Review AI 평가 영역이 소유하게 했다. 이전 script와 호환 wrapper는 제거했다.

## Run And Read

이 PR의 checkout 최상위에서 로컬 환경 설정을 확인한 뒤 실행한다.

```bash
uv run --env-file .env python -m hmda_reliability.review_ai.evaluation.live
```

실제 데이터 적재 없이 가상 컨텍스트 한 건을 실제 provider로 보낸다. 한국어 세 단계 답변을 수집하고 코드가 JSON을 만든 뒤 저장 근거를 확인한다. 사람이 답변의 정확성과 유용성을 평가하는 절차는 [Human Review Guide](02-guide-review-ai-human-guide.md)에서 이어간다.

진행 표시는 stderr에 즉시 출력한다. 다음은 형식을 보여주는 예시이며 실제 모델 실행 기록이 아니다.

```text
가상 사례로 실제 모델 통합 검증 시작 (staged-v1)
단계 1/3 근거 검토 시작
단계 1/3 근거 검토 응답 대기 · 단계 5.0초 · 전체 5.0초
단계 1/3 근거 검토 수집·저장 완료 · 단계 8.0초 · 전체 8.0초 · 요청 1회
```

대기 표시는 기본 5초마다 provider 호출 구간에서만 발생한다. 로컬 단계·전체 경과시간이며 내부 retry와 backoff도 포함할 수 있다. 모델의 실제 생성 진행률이나 정상 작동을 보장하지 않는다. 원문·설정값·credential·개인 절대 경로·예외 본문을 진행 이벤트나 로그에 넣지 않는다.

최종 상태와 경로 JSON은 stdout에 유지한다. `> result.json`으로 받으면서 진행 로그를 계속 볼 수 있다. 각 단계의 완료는 원문과 checkpoint 저장 후 표시하며 `completed`도 수집·저장 성공이라는 의미다. 내용의 사실성이나 사람 승인으로 해석하지 않는다.

## Execution Boundaries

- Service는 고정 단계·phase·상태·시도 수만 선택적 observer에 전달한다. 일반 API 호출에는 콘솔이나 timer가 생기지 않는다.
- Reporter가 단일 보조 thread를 소유하고 정상·실패·예외·중단 시 stop·join한다. Observer의 일반 예외와 끊긴 콘솔은 provider 결과와 저장 근거를 바꾸지 않는다.
- 자동 revision은 실제 import한 source checkout의 HEAD와 clean tracked tree를 사용한다. 설치된 wheel처럼 source를 입증할 수 없으면 명시적 revision을 요구한다.
- Live opt-in, HTTP timeout, 단계·전체 예산, transport retry, 원문 보존과 provenance 검사 의미는 유지한다.

## Verification

- 새 모듈과 관찰 계약이 없어 실패하는 테스트를 먼저 확인한 뒤 구현했다.
- Review AI·Runtime AI 관련 suite **287 passed**. 실제 SDK에 모의 HTTP 전송을 연결해 성공·미완료 응답의 로그, JSON과 원문 보존을 확인했다.
- 응답이 아직 끝나지 않은 동안 heartbeat가 보이는지, 호출 경계 밖에서는 멈추는지, 정상·예외에서 timer가 정리되는지, 저장 실패가 완료로 표시되지 않는지 검증했다.
- 서로 다른 두 임시 Git 저장소로 상속된 Git 환경변수가 출처를 바꾸는 결함을 재현하고 격리했다. Console·clock 오류와 thread 시작 실패는 관찰에만 영향을 주며 민감한 예외 본문을 출력하지 않는다.
- Wheel build와 checkout 밖의 격리 import·비활성 모듈 실행·자동 revision 거부·명시적 revision 검사가 통과했다. 실제 provider를 호출하지 않았다.
- Ruff·format·ty·Tach·IDE 진단이 통과했다. 구조도 Mermaid의 구문 검사와 미리보기도 확인했다.
- 사람 가이드의 선택 실행 예제도 세 합성 사례·아홉 준비된 provider 응답으로 실행해 JSON과 단계 로그를 확인했다. OpenSpec 전체 strict **31 passed, 0 failed**, Markdown·Inbox·diff 검사가 통과했다.

현재 변경의 실제 모델 품질·사람 점수와 hosted CI 결과는 위 로컬 검증으로 입증하지 않는다. 요구사항은 [Review Spec](../../openspec/specs/reliability-agentic-review/spec.md), 작업 근거는 [Change](../../openspec/changes/review-ai-observe-live-validation/tasks.md), 실행 안내는 [Evaluation Guide](../../docs/development/review-ai-evaluation.md)가 소유한다.
