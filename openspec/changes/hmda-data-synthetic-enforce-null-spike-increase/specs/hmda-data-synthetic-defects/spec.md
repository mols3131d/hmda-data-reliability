---
type: openspec-spec-driven-tdd-spec
category: spec
title: hmda-data-synthetic-defects
description: Strengthen deterministic null-spike generation so emitted defects always represent a real target-column null increase.
tags:
  - "capability:hmda-data-synthetic-defects"
---

## MODIFIED Requirements

### Requirement: Null spike case

시스템은 존재하는 target column에 지정 비율의 null 증가를 주입할 수 있어야 한다(SHALL). 유효한 null-spike 요청의 결과 target-column null 비율은 원본보다 검증 가능하게 커야 하며(MUST), 증가를 위해 기존 non-null target value를 `NULL`로 전환해야 한다(MUST).

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
