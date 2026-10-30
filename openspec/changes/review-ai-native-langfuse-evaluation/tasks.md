---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Native Langfuse Review Evaluation
description: Native SDK 실험·사람 평가와 기존 실행의 최소 무결성 검사를 연결합니다.
tasks_completed: 5
tasks_total: 5
---

## Tasks

- [x] SDK-free 사례·출력 연결과 native annotation 완비 검사를 구현하고 중복 평가 모델을 제거한다.
  - **Test first:** 정확한 원문 digest·사례/실행 출처 구분·workflow 충돌·다섯 사람 점수와 사유·독립 채택 의견을 RED로 고정한다.
  - **Done when:** 점수 합계·비교 보고서 없이 불일치·누락·자동 점수를 차단하고 독립 품질 corpus를 유지한다.
- [x] SDK 4.15.6의 Dataset·Score Config·Queue·실험 task와 검증된 단계 IO를 연결한다.
  - **Test first:** 실제 SDK 계약·bootstrap 재사용/충돌·원문 변조·부분 실패·oracle 미주입을 모의 외부 전송으로 고정한다.
  - **Done when:** Native 실험이 현재 세 단계 함수를 호출하고 허용된 IO와 출처만 전달하며 자동 judge를 실행하지 않는다.
- [x] 두 opt-in과 독립 외부 I/O 예산을 가진 실행 진입점을 구현한다.
  - **Test first:** 비활성·누락 설정·외부 hang·core 실행 구간·정제 protocol과 예외 유출 차단을 검증한다.
  - **Done when:** SDK의 무제한 flush를 종료할 수 있고 이미 저장된 core 결과를 보존한다.
- [x] Native 사람 annotation 조회와 평가 완비 확인을 실행 가능한 경로로 제공한다.
  - **Test first:** Pagination·source/작성자·Config·trace/관측·사유·pair digest 불일치를 거부한다.
  - **Done when:** API 제출과 실제 사람 평가를 구분하며 확인된 원격 자료만 완비로 보고한다.
- [x] 환경·개발·인간 검토 안내와 정본을 현재 native 경계에 맞춘다.
  - **Done when:** 관련 회귀·정적 검사·문서·OpenSpec과 배포 검증이 통과하며 실제 원격/UI·사람 평가의 미검증 한계를 기록한다.

## Validation Boundary

로컬 구현 작업은 위 task로 추적한다. 실제 대상 서버의 원격 조회·UI와 사람이 입력한 점수는 아직 미검증이며, fixture·SDK 설치·flush 반환으로 완료 처리하지 않는다.
