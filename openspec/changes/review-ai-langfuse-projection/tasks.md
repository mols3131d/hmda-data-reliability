---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Langfuse Local Projection Tasks
description: Optional projection과 annotation 계약의 로컬 구현 결과를 추적한다.
tasks_completed: 3
tasks_total: 3
---

## Tasks

- [x] 검증된 합성 record의 bounded projection과 exact identity를 구현한다.
  - **Done when:** accepted, failed, input mismatch, forbidden fields, oversize와 digest binding을 test-first 검증한다.
- [x] Optional SDK child와 live harness의 실패 격리를 구현한다.
  - **Done when:** SDK 없는 disabled 경로, opt-in, invalid config, child 오류·timeout과 provenance 실패를 검증하고 SDK 4.15.6의 network-free runtime smoke를 통과한다. Media-like output 경로에서 SDK media detection/upload가 꺼지고 exact structured output이 유지되는지도 검증한다.
- [x] Integration-local annotation completeness와 수동 setup 안내를 제공한다.
  - **Done when:** 다섯 score/rationale의 누락·중복·잘못된 값·target mismatch, unsupported rubric, missing/changed/malformed output, model coercion으로 달라지는 JSON 값/타입과 재계산 digest mismatch를 test-first 검증하고 사용 안내에 live/human proof 미검증을 명시한다.

실제 endpoint/project가 없어 live ingestion과 human annotation은 이 로컬 구현 실행의 완료 조건에 포함하지 않는다. PR 전체 proof는 후속 live 실행이 필요하다.
