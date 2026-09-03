---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: 2026년 가상 합성 데이터 평가 작업
description: 2026년 파티션 합성 결함 생성, 샌드박스 수명주기 통합 테스트, 재현 가능한 실행 경로를 구현한다.
tasks_completed: 3
tasks_total: 3
---

## Tasks

- [x] 2026년 파티션 대상 합성 결함(`null_spike`) 생성 및 검증
  - **Done when:** 원본 2025년 파일을 변경하지 않고 `activity_year=2026` 및 `income` 결측치가 30% 이상인 합성 데이터를 생성할 수 있으며, 관련 통계가 테스트로 검증된다.
  - **Covers:** `hmda-data-synthetic-defects`

- [x] 2026년 가상 파티션에 대한 신뢰성 수명주기(`run_incident_lifecycle`) 통합 검증
  - **Done when:** 격리된 샌드박스 DB에서 2026년 데이터를 대상으로 baseline과 current를 비교했을 때 `null_spike` 사고 감지, dbt 하위 모델(`stg_hmda_loans`, `mart_hmda_loan_outcomes`) 계통 영향 분석 및 복구 권고안 생성을 검증하는 통합 테스트가 통과한다.
  - **Covers:** `data-operations-incident-lifecycle`

- [x] 재현 가능한 2026년 가상 평가 실행 경로 및 검증 스위트 동기화
  - **Done when:** 샌드박스 2026년 평가 시나리오가 프로젝트 전체 테스트 스위트(`pytest`)에 포함되어 회귀 없이 안정적으로 통과하고, 메인 DB 파일에 어떠한 부작용(Side effect)도 남기지 않음이 확인된다.
