---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Synthetic Source Preservation Tasks
description: 실제 원본 보존 실패를 검출하고 합성 출력 충돌을 차단하는 최소 수정 및 회귀 검증입니다.
tasks_completed: 2
tasks_total: 2
---

## Tasks

- [x] 원본이 출력 case directory에 포함되는 상황을 회귀 테스트로 고정한다.
  - **Test first:** 임시 CSV를 `cases/row_count_drop/year_2025.csv`에 만들고 겹치는 output root로 public API를 호출한다. 정상적인 test collection 후 source bytes 보존 assertion이 기존 코드에서 실패하는지 확인한다.
  - **Done when:** 원본이 삭제·변경되지 않고 요청이 `SyntheticCaseError`로 거부됨을 확인하며, 실제 경로 별칭에 의한 중첩도 회귀가 감지한다.

- [x] 합성 출력의 삭제 전 경로 충돌 보호를 구현하고 정상 생성 동작을 유지한다.
  - **Done when:** 세 synthetic case 진입점에서 원본이 기존 case directory 정리로 삭제되지 않고, 비중첩 입력의 생성·재생성 및 관련 HMDA Data 테스트가 통과한다. 변경 범위의 lint·type·CI 검증 근거를 기록한다.
