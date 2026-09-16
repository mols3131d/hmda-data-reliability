---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: 2026년 가상 합성 데이터 평가 작업
description: 2026년 파티션 합성 결함 생성, 샌드박스 수명주기 통합 테스트, 재현 가능한 실행 경로를 구현한다.
tasks_completed: 4
tasks_total: 4
---

## Tasks

- [x] 2026년 파티션 대상 합성 결함(`null_spike`) 생성, 제약 검증 및 단위 테스트
  - **Done when:** `target_year` 유효 범위(2000 이상 2100 이하 정수, bool 제외), `target_column == "activity_year"` 거부, 다중 연도 원천 입력 거부 가드가 추가되고, docstring이 보강되며 관련 단위 테스트가 통과한다.
  - **Covers:** `hmda-data-synthetic-defects`

- [x] 2026년 가상 파티션에 대한 합성 산출물 E2E 결합 및 신뢰성 수명주기 통합 검증
  - **Done when:** 수동 SQL 주입 대신 실제 `null_spike()` 산출물(Parquet)을 적재하여 `run_incident_lifecycle()`로 평가하고, `null_spike` 사고 감지, dbt 하위 모델 계통 영향, 구체적 권고 조치 목록 및 메인 DB 무변경을 엄격히 단언하는 통합 테스트가 통과한다.

- [x] 재현 가능한 2026년 가상 평가 실행 경로, OpenSpec 델타 스펙 동기화 및 전체 검증
  - **Done when:** `hmda-data-synthetic-defects` 델타 스펙이 동기화되고, 프로젝트 전체 회귀 테스트 스위트(`pytest`), 린트, 포맷 검사가 모두 통과한다.

- [x] Synthetic filename의 첫 ASCII 연도와 `target_year` 일치 보장
  - **Done when:** `case_name="null_spike_2025_2026"` 및 `case_name="null_spike_２０２６"`, `target_year=2026` 요청이 output 생성 전에 거부되고, 첫 ASCII 4자리 연도가 2026인 사용자 지정 이름은 허용되며, 실제 ingestion 경계에서 2026 파티션으로 적재되는 회귀 테스트가 통과한다.
  - **Covers:** `hmda-data-synthetic-defects`의 `Reject conflicting filename year` scenario
  - **Test first:** 목표 연도가 문자열 뒤쪽에만 포함되거나 Unicode decimal digit으로만 표현된 사용자 지정 이름이 현재 잘못 허용되는 동작을 실패 테스트로 고정한다.
