---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: 가상 2026년 합성 데이터 신뢰성 수명주기 검증 및 평가
description: 2026년 가상 결함 데이터를 샌드박스에 적재하고 신뢰성 이상 탐지 및 복구 권고를 종단간으로 검증하는 평가 체계 정립
tags:
  - "domain:reliability"
  - "capability:synthetic-evaluation"
---

## Why

현재 시스템은 2025년 단일 연도 HMDA 데이터를 중심으로 검증되어 있습니다. 실전 운영 환경처럼 새로운 연도(2026년) 데이터 파티션이 유입되고, 그 과정에서 대규모 결측치 급증(`null_spike`)과 같은 데이터 품질 사고가 발생했을 때 시스템이 안전하게 동작하는지 검증할 필요가 있습니다.

특히 기존 메인 데이터 레이크를 오염시키지 않으면서, 격리된 샌드박스 환경에서 가상 2026년 결함 데이터를 적재하고 신뢰성 수명주기(`run_incident_lifecycle`)를 통해 사고를 정확히 감지하며 복구 권고안을 도출하는 전 과정을 재현 가능하게 보장해야 합니다.

## What Changes

- 2026년 가상 결함(`income` 결측치 급증) 합성 데이터셋 생성 및 샌드박스 격리 적재 절차 정의
- 2025년 정상 기준선(Baseline)과 2026년 현재(Current) 프로파일을 비교하는 신뢰성 수명주기 종단간 검증
- dbt 모델 계통(`stg_hmda_loans`, `mart_hmda_loan_outcomes`)에 대한 영향도 분석 및 복구 권고안 도출 자동화 검증

## Boundaries

- **In Scope:**
  - 2026년 파티션 대상 결정론적 `null_spike` 합성 결함 생성
  - 샌드박스 DB 기반의 격리 적재 및 dbt 분석 마트 변환 검증
  - 신뢰성 수명주기(`run_incident_lifecycle`)를 통한 사고 탐지, dbt 계통 영향 분석, 권고 조치 검증
- **Out of Scope:**
  - 실제 외부 공공 포털의 2026년 HMDA 데이터 다운로드
  - Airflow DAG 스키마 또는 스케줄러 구조 변경
  - 승인 없는 자동 데이터 변이(Mutation) 또는 실 데이터 복구 실행

## Capabilities

### Modified Capabilities

#### `hmda-data-synthetic-defects`

- 특정 연도 파티션(`activity_year=2026`)을 지정하여 결정론적으로 `null_spike` 결함을 주입하고, 기존 원천을 수정하지 않는 합성 파일 산출물 계약을 명시합니다.

#### `data-operations-incident-lifecycle`

- 2026년 신규 파티션에 대한 프로파일 스냅샷을 생성하고, 이전 정상 기준선과의 비교를 통해 `null_spike` 사고와 downstream dbt 자산 영향을 정상 도출함을 보장합니다.

## Impact

- **데이터**: 기존 메인 데이터([data/README.md](../../../data/README.md) 참조)는 변경되지 않으며, 격리된 샌드박스 DB에서만 안전하게 실행됩니다.
- **테스트**: 2026년 합성 결함 데이터에 대한 종단간 신뢰성 수명주기 통합 테스트가 추가됩니다.
- **운영**: 신규 연도 파티션 유입 시의 품질 감시 및 복구 계획 수립 절차가 명확해집니다.
