---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Observe Live Review Validation
description: 단계 관찰 사건·evaluation 실행 모듈·안전한 대기 표시와 실행 안내를 연결합니다.
tasks_completed: 3
tasks_total: 3
---

## Tasks

- [x] 현재 단계 실행에 부작용 없는 선택적 진행 관찰 경계를 연결한다.
  - **Covers:** Safe live stage progress.
  - **Test first:** 정상 단계의 네 사건 순서, provider 예외의 종료 사건, checkpoint 실패의 stage 실패, observer 오류 격리와 observer 없는 API의 무출력을 먼저 고정한다.
  - **Done when:** Provider 대기와 checkpoint 완료가 구별되고 예상한 실패에서 후속 단계 사건이 없으며 관찰자가 result·원문·manifest·시간 예산을 변경하지 않는다.
- [x] 실제 provider 검증을 evaluation 모듈로 이동하고 한국어 stderr 진행과 대기 heartbeat를 구현한다.
  - **Covers:** Evaluation-owned live validation entrypoint; Safe live stage progress.
  - **Test first:** 새 모듈 실행·import·disabled·설정 및 provenance 실패, 기본 5초와 provider 구간에 한정된 heartbeat, 정상·예외·중단 시 자원 정리, 로그의 민감 문자열 부재와 stdout JSON 불변을 fake provider와 제어 가능한 시간으로 검증한다. Source checkout과 다른 cwd 및 배포 설치의 revision 경계도 먼저 고정한다.
  - **Done when:** 새 모듈만 실행 진입점이고 기존 script·wrapper가 없으며 source 소유 revision을 검증한다. 동기 호출·retry·예산·원문·provenance 결과를 유지하고 종료 이후 timer나 로그가 남지 않는다.
- [x] 현재 실행 안내와 검증 경로를 새 모듈에 맞춰 통일한다.
  - **Test first:** 실행 가이드·테스트 import·배포 모듈의 경로가 새 진입점을 가리키고 삭제한 script에 의존하지 않음을 확인한다.
  - **Done when:** 문서가 stderr의 로컬 대기와 stdout JSON, 실제 provider 검증과 사람의 품질 평가를 구분하고 관련 domain 회귀·정적 검사·Markdown·OpenSpec 및 배포 실행 검증이 통과한다.

## Validation Boundary

- 현재 작업트리의 Review AI/Runtime AI 회귀는 **287 passed**다. Fake provider와 제어 가능한 시간으로 단계 사건·provider 대기·heartbeat·종료 정리와 기존 결과·원문·provenance 경계를 확인했다.
- Ruff·format·ty·Tach와 IDE 진단이 통과했다. Source와 checkout 밖의 격리 wheel에서 새 모듈의 disabled 실행을 확인했다.
- Source 소유 checkout의 revision 경계를 유지하고, 격리 wheel에서 auto revision 거부와 명시적 revision 경로를 확인했다. 이전 script와 호환 wrapper는 남기지 않았다.
- 두 임시 Git 저장소로 환경변수 출처 우회 RED→GREEN을 확인했다. 관찰 thread의 console·clock 오류와 시작 실패도 격리하고 임의 상태·예외 본문 유출과 자원 잔류를 차단했다.
- 두 ADDED 요구사항은 구현 후 정본에 같은 본문으로 동기화했다. 이 Change는 active 상태로 유지한다.
- OpenSpec 전체 strict는 **31 passed, 0 failed**, 정본과 현재 Change의 Markdown 5개 및 `git diff --check`가 통과했다.
- 실제 모델을 호출하지 않았다. Offline 회귀·배포 실행 확인·진행 표시는 현재 모델의 세 단계 완료·한국어 준수·정확성 또는 사람의 rubric 평가 증거가 아니다.
