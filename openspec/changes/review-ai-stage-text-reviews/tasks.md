---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Stage Review AI Text Responses
description: 텍스트 대화·단계별 프롬프트·기록과 코드 조립을 구현하고 live 경로에 연결합니다.
tasks_completed: 4
tasks_total: 4
---

## Tasks

- [x] Runtime에 assistant 이력과 호출별 text 응답 모드를 추가한다.
  - **Test first:** plain 요청의 wire에서 response_format이 생략되고 legacy JSON은 유지됨을 확인하는 회귀를 먼저 실패시킨다.
  - **Done when:** 실제 SDK fake transport에서 선택 모드와 assistant 메시지를 보존하고 기존 runtime 회귀가 통과한다.
- [x] 고정 단계의 typed 출력·결정적 renderer와 한국어 Markdown 모듈을 구현한다.
  - **Test first:** 세 단계 순서, 원문을 포함한 코드 직렬화, 최초 입력과 assistant 이력, 누적 byte cap에 대한 회귀를 먼저 실패시킨다.
  - **Done when:** 기존 프롬프트 bytes를 유지하면서 모델 JSON 지시 없는 단계 질문과 exact text collection을 제공한다.
- [x] 단계 service와 bounded create-only 기록·최종 JSON 저장을 구현한다.
  - **Test first:** 세 단계 성공, 중간 실패·빈 답변·length·저장 실패·identity 충돌과 누적 입력 한도에서 원문 보존·후속 중단을 먼저 실패시킨다.
  - **Done when:** 원input facts와 exact 답변을 코드로 취합하고 단계 기록·최종 digest를 연결한다. Partial 실패가 성공으로 반환되지 않는다.
- [x] Live 기본 staged 경로·명시 structured 비교 경로와 문서를 연결한다.
  - **Test first:** 기본 경로, 명시 structured 선택, disabled/missing config 및 staged projection 생략을 회귀로 확인한다.
  - **Done when:** 기존 명령으로 staged 결과 파일을 확인할 수 있고 새 계약·한계·실행 방법을 문서화한다. 관련 suite·정적·패키지·OpenSpec 검증을 완료한다.

## Validation

- 기존 변경 checkpoint `77761a75`는 feature 착수 전에 커밋·푸시하고 원격 HEAD를 확인했다.
- Runtime text mode 2개, 공백·순서 계약 4개, 초기 실행 경로, CLI staged 경로 7개의 구현 전 실패를 확인했다. Identity 충돌·UTF-8 원문 실패와 bool/int canonical input 충돌도 실패 재현 후 수정했다.
- Review AI/Runtime AI 전체 suite는 **346 passed, 1 skipped**다. 생략은 optional Langfuse SDK media smoke다. 실제 SDK와 가짜 HTTP를 연결한 세 단계 성공 및 중간 잘림 테스트도 포함한다.
- Ruff·format·ty·Tach, Markdown·diff 검사 및 OpenSpec strict **30 passed, 0 failed**를 확인했다. Wheel/sdist에 새 모듈 4개가 포함되고 checkout 밖에서 세 단계 조립과 기존 v1/v2/v3 golden digest 보존을 확인했다.
- 실제 로컬 모델 smoke는 retry 0, 단계별 timeout 60초·4096토큰으로 한 번 실행했다. 첫 요청에서 본문을 받지 못해 `unavailable / provider_connection_error`로 종료됐다. Workflow `sr-20261028-6543e4292f04`의 실패 checkpoint·manifest를 보존하고 수정된 CLI verifier로 재검증했다.
- 이 live attempt는 `local-staged-text-worktree` 표식의 미커밋 실행이다. 실제 모델의 세 단계 완료·품질·사람 평가 및 현재 commit의 hosted CI 성공을 증명하지 않는다.
