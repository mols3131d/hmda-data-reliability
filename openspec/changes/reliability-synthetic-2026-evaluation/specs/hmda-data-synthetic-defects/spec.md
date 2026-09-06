---
type: openspec-spec-driven-tdd-spec
category: spec
title: hmda-data-synthetic-defects
description: 합성 결함 생성 시 대상 연도(target_year) 오버라이드 및 유효성 검증 계약
tags:
  - "capability:hmda-data-synthetic-defects"
---

## MODIFIED Requirements

### Requirement: Null spike case

시스템은 존재하는 target column에 지정 비율의 null 증가를 주입할 수 있어야 한다(SHALL). 유효한 null-spike 요청의 결과 target-column null 비율은 원본보다 검증 가능하게 커야 하며(MUST), 증가를 위해 기존 non-null target value를 `NULL`로 전환해야 한다(MUST). 호출자가 `target_year`를 지정한 경우 단일 연도 원천 데이터에 대해 결과 파티션 연도를 해당 값으로 교체해야 하며(SHALL), output filename에서 ingestion이 추출하는 첫 번째 ASCII 4자리 연도(`[0-9]{4}`)도 `target_year`와 일치해야 한다(MUST). 유효 범위를 벗어난 연도, `target_column == "activity_year"`인 요청, ASCII 연도 없는 이름 또는 목표 연도보다 앞선 다른 연도가 있는 사용자 지정 `case_name`은 거부해야 한다(MUST).

#### Scenario: Income null spike

- **WHEN** `income`에 유효한 null fraction을 적용할 때
- **THEN** 결과 파일의 `income` null 비율은 원본보다 검증 가능하게 증가해야 한다.
- **AND** 결과에는 원본에서 non-null이었던 `income` 값이 `NULL`로 전환된 row가 하나 이상 있어야 한다.

#### Scenario: High-baseline income null spike

- **GIVEN** 원본 `income` null 비율이 이미 높지만 non-null `income` 값이 하나 이상 존재할 때
- **WHEN** 유효한 null fraction을 적용할 때
- **THEN** 결과 파일의 `income` null 비율은 여전히 원본보다 커야 한다.

#### Scenario: Fully null target column

- **WHEN** 모든 target-column 값이 이미 `NULL`인 source에 null spike를 요청할 때
- **THEN** 시스템은 synthetic case failure로 요청을 거부해야 한다.
- **AND** null-spike output을 생성해서는 안 된다.

#### Scenario: Missing target column

- **WHEN** source에 존재하지 않는 target column에 null spike를 요청할 때
- **THEN** 시스템은 synthetic case failure로 요청을 거부해야 한다.

#### Scenario: Target year override null spike

- **GIVEN** 단일 연도 원천 데이터가 주어졌을 때
- **WHEN** 유효한 `target_year`(2000~2100)와 null fraction으로 null_spike를 실행할 때
- **THEN** 결과 파일의 `activity_year`는 지정된 `target_year` 값이어야 한다.
- **AND** target column의 null 비율은 원본보다 커야 한다.

#### Scenario: Reject target column activity year with target year

- **WHEN** `target_year`가 지정되고 `target_column="activity_year"`일 때
- **THEN** 시스템은 상호 모순을 알리는 `SyntheticCaseError`를 발생시켜야 한다.

#### Scenario: Reject invalid target year

- **WHEN** `target_year`가 2000 미만, 2100 초과 또는 정수가 아닐 때
- **THEN** 시스템은 유효성 오류(`SyntheticCaseError`)를 발생시켜야 한다.

#### Scenario: Reject multi-year source with target year

- **GIVEN** 2개 이상의 서로 다른 `activity_year`를 포함한 원천 데이터가 주어졌을 때
- **WHEN** `target_year`가 지정된 null_spike를 실행할 때
- **THEN** 시스템은 단일 연도 원천이 필요함을 알리는 `SyntheticCaseError`를 발생시켜야 한다.

#### Scenario: Reject conflicting filename year

- **WHEN** `target_year=2026`과 `case_name="null_spike_2025_2026"`으로 null_spike를 실행할 때
- **THEN** 시스템은 ingestion이 2025년 파티션으로 해석할 수 있는 이름을 `SyntheticCaseError`로 거부해야 한다.
- **AND** synthetic output을 생성해서는 안 된다.

#### Scenario: Reject non-ASCII filename year

- **WHEN** `target_year=2026`과 `case_name="null_spike_２０２６"`으로 null_spike를 실행할 때
- **THEN** 시스템은 ingestion이 연도로 추출하지 못하는 이름을 `SyntheticCaseError`로 거부해야 한다.
- **AND** synthetic output을 생성해서는 안 된다.
