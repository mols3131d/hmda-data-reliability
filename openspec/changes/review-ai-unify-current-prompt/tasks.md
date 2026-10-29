---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Unify Current Review Prompt
description: 레거시 호환 구현을 삭제하고 현재 실행·평가·설정을 일치시킵니다.
tasks_completed: 3
tasks_total: 3
---

## Tasks

- [x] 현재 단계 실행의 input·공유 저장 경계를 유지하면서 레거시 실행·prompt·계약·파서·validator·기록 reader를 삭제한다.
  - **Test first:** 공개 API와 input에서 과거 타입·prompt_identity가 사라지고 배포 리소스에 버전 snapshot이 없음을 먼저 실패시킨다. 기존 snapshot·context·원문·예산·실패 보존 회귀는 현재 계약으로 유지한다.
  - **Done when:** 현재 import와 wheel에는 현재 실행만 있으며 세 단계 text 수집·코드 facts 취합·정확한 원문과 create-only 실패 보존이 동작한다.
- [x] Human rubric 평가를 StagedReviewOutput과 workflow_id로 전환하고 과거 projection·annotation 구현을 삭제한다.
  - **Test first:** 현재 output의 독립 golden shape·단계 원문 digest와 workflow identity를 고정하고 같은 사례/facts/revision 및 다섯 criterion 경계의 회귀를 먼저 실행한다.
  - **Done when:** 현재 collection만 평가하며 과거 shape용 alias·union loader·Langfuse 전용 실행이 없고 human decision과 비교 차단 조건이 유지된다.
- [x] CLI·환경 예제·정본 안내를 현재 실행 전용으로 정리한다.
  - **Test first:** mode/version 선택 없는 기본 함수 연결과 현재 env 우선순위·disabled·missing/invalid 설정·provenance 검증 및 실패 경로를 확인한다.
  - **Done when:** 이전 mode/version/export 읽기·호환 분기·fallback 없이 현재 실행만 제공하고 관련 테스트·정적 검사·배포 리소스·OpenSpec 검증이 통과한다.

## Validation

- 이전 완료 표시는 레거시 지원을 남긴 구현의 결과이므로 같은 목표의 owning task를 재개했다. 현재 기준은 `24b5f26833121de853ce0787c0bb67c3ad25673d`이다.
- 구현 전 공개 surface·입력에서 7건, CLI에서 1건, 평가 전환에서 42건의 실패를 확인했다. 독립 검토에서 찾은 동일 workflow/상이 digest 비교의 2개 회귀도 먼저 실패시킨 뒤 보완했다.
- 현재 계약으로 Review AI/Runtime AI 전체 **261 passed**를 확인했다. 입력 snapshot·bounded context·정확한 원문·실패 경로·create-only 원자성·시간 예산과 다섯 rubric 및 독립 수치 oracle을 유지했다.
- Wheel을 checkout 밖의 isolated Python에서 직접 import하여 현재 세 단계의 한국어 메시지 digest가 source와 같고 레거시 모듈·snapshot·reader·projection이 배포되지 않음을 확인했다.
- Ruff·format·ty·Tach·Markdown·Inbox·diff 및 문서 Mermaid syntax/preview가 통과했다. OpenSpec strict는 완료된 이전 Change 2개를 정본 재적용 없이 archive한 뒤 30 passed, 0 failed다. 이동한 10개 파일은 HEAD의 원문과 byte 동일하다.
- 작업 폴더의 `.env`에서 이전 mode/version/export 선택 키만 제거했다. 모델·credential·시간 설정과 read-only 첨부 snapshot은 변경하지 않았다.
- 과거 artifact·Inbox·Git 기록은 유지하며 실제 모델 생성·품질 채택·main 병합은 이 작업의 완료 주장에 포함하지 않는다.
