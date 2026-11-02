---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Budget Staged Review Execution
description: 전송·실행 예산과 환경 설정을 회귀로 검증합니다.
tasks_completed: 3
tasks_total: 3
---

## Tasks

- [x] Runtime에 선택적 phase timeout과 호출별 retry 예산을 적용한다.
  - **Test first:** 기존 fallback·명시 override, timeout 구분, fake clock으로 retry·backoff 중단과 실제 SDK timeout 전달을 먼저 실패시킨다.
  - **Done when:** 숨은 retry 없이 실제 호출 수와 정제된 실패 코드를 반환하고 늦은 bounded body를 버리지 않는다.
- [x] Staged 실행의 단계·전체 예산과 호환 가능한 시간 기록을 적용한다.
  - **Test first:** 예산 초과 원문 보존, 단계 사이 소진·0회 호출, 잔여 예산 전달과 과거 JSON 로딩을 먼저 실패시킨다.
  - **Done when:** 완료·실패 결과가 시간 예산과 일치하며 이전 checkpoint와 본문을 보존한다.
- [x] Live 환경 설정·provenance 검증과 운영 문서를 연결한다.
  - **Test first:** 새 환경 변수 우선순위, staged/structured 기본값, 유효하지 않은 설정의 호출 전 거부를 먼저 실패시킨다.
  - **Done when:** 설정 예제와 문서가 실제 코드·예산 한계를 설명하고 관련 회귀·정적·OpenSpec 검증이 통과한다.

## Validation

- 기존 revision `fa0645055db03d5f5a416e19f992400ad2b4a65f` 이후 작업이다. 새 Runtime·CLI 회귀 27개와 staged 설정 모듈 부재의 구현 전 실패를 확인했다.
- Review AI/Runtime AI 전체 **400 passed, 1 skipped**. 생략은 optional Langfuse SDK media smoke다. 가짜 monotonic clock으로 늦은 원문 보존, 단계 사이·출력 저장 중 소진, retry budget과 실제 SDK timeout 전달을 확인했다.
- 이전 기록의 새 설정 누락, 현재 설정 변조 거부, URL 표기의 의미상 동등성 및 두 모드의 환경 우선순위를 확인했다. 기존 Langfuse fixture는 본문을 유지하고 CLI 환경의 timeout/retry만 원기록의 5초/0회에 맞췄다.
- Ruff·format(66 Python files), ty·Tach·Markdown·diff 검사 및 OpenSpec strict **31 passed, 0 failed**. Wheel build와 새 설정 모듈 포함 여부를 확인했다.
- Git-local 환경을 제거한 synthetic Git fixture probe가 통과했다. 같은 격리 경계로 pre-push 검증을 실행한다.
- 로컬 `.env`에 기존 값과 credentials를 유지하며 새 시간 설정만 추가했다. 실제 CLI 설정 로딩이 connect 10초·read 300초·stage 360초·workflow 1200초·retry 0회임을 provider 호출 전에 확인했다.
- 실제 모델 생성은 재실행하지 않았다. 과거 provider_connection_error 기록은 새 코드의 provider_timeout 판정이나 세 단계 완료·품질 검증으로 소급 해석하지 않는다.
