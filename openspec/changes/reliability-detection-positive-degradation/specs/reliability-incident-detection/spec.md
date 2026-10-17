---
type: openspec-spec-driven-tdd-spec
category: spec
title: Reliability Incident Detection
description: 실제 양의 감소·결측 증가와 threshold equality를 구분하고 freshness 및 schema 규칙을 독립적으로 보존합니다.
---

## MODIFIED Requirements

### Requirement: Rule-based profile comparison

시스템은 비교 가능한 baseline `ProfileSnapshot`과 current `ProfileSnapshot`을 비교해 row count drop, null spike, schema drift와 freshness delay를 각 규칙의 탐지 조건에 따라 독립적으로 평가해야 한다(SHALL). Volume/null의 변화가 없다는 이유로 schema나 freshness 탐지를 생략해서는 안 된다(MUST NOT).

#### Scenario: Normal comparison

- **GIVEN** 행 수와 null rate 및 schema가 같고 current freshness age가 설정한 최대 나이 미만일 때
- **WHEN** volume/null threshold를 각각 0으로 설정해 탐지할 때
- **THEN** incident를 생성하지 않아야 한다.

#### Scenario: Incompatible profile pair

- **WHEN** baseline과 current profile의 asset identity 또는 partition identity가 다를 때
- **THEN** 시스템은 두 profile을 detection 대상으로 받아들이지 않아야 한다.

#### Scenario: Independent freshness and schema rules

- **GIVEN** 행 수와 null rate는 같고 volume/null threshold는 각각 0일 때
- **WHEN** schema hash가 바뀌거나 측정된 current freshness age가 최대 나이 이상일 때
- **THEN** 해당 schema/freshness incident를 생성하고 volume/null incident는 생성하지 않아야 한다.

### Requirement: Volume drop detection

시스템은 baseline row count가 양수이고 current row count가 실제로 감소했으며 감소율이 configured ratio 이상일 때만 `volume_drop` incident를 생성해야 한다(SHALL). Ratio 0을 유효한 설정으로 허용하고 어떤 양의 감소도 탐지해야 한다(SHALL). Baseline row count가 0이면 분모가 없으므로 volume 비교를 제외하고 다른 규칙의 실행은 유지해야 한다(SHALL).

#### Scenario: Material volume drop

- **WHEN** baseline row count가 100, current row count가 40이고 threshold가 0.5일 때
- **THEN** `volume_drop` incident와 baseline/current row count 및 drop ratio evidence를 생성해야 한다.

#### Scenario: Zero threshold without decrease

- **WHEN** baseline row count가 100이고 current row count가 100 이상이며 threshold가 0일 때
- **THEN** `volume_drop` incident를 생성하지 않아야 한다.

#### Scenario: Zero threshold with positive decrease

- **WHEN** baseline row count가 100, current row count가 99이고 threshold가 0일 때
- **THEN** `volume_drop` incident와 drop ratio 0.01 evidence를 생성해야 한다.

#### Scenario: Positive ratio equality

- **WHEN** baseline row count가 100, current row count가 50이고 threshold가 0.5일 때
- **THEN** `volume_drop` incident를 생성해야 한다.

#### Scenario: Zero-row baseline

- **WHEN** baseline row count가 0일 때
- **THEN** `volume_drop` incident를 생성하지 않고 다른 규칙은 독립적으로 평가해야 한다.

### Requirement: Null spike detection

시스템은 column null rate가 비교 기준보다 실제로 증가하고 그 증가량이 configured delta 이상일 때만 `null_spike` incident를 생성해야 한다(SHALL). Delta 0을 유효한 설정으로 허용하고 어떤 양의 증가도 탐지해야 한다(SHALL). Null rate가 같거나 감소한 경우에는 해당 column의 `null_spike` incident를 생성해서는 안 된다(MUST NOT).

#### Scenario: Material null spike

- **WHEN** 한 column의 null rate가 양의 threshold 이상 증가할 때
- **THEN** target column과 baseline/current null rate를 가진 evidence를 생성해야 한다.

#### Scenario: Zero threshold without increase

- **WHEN** 한 column의 null rate가 비교 기준과 같거나 낮고 threshold가 0일 때
- **THEN** 해당 column의 `null_spike` incident를 생성하지 않아야 한다.

#### Scenario: Zero threshold with positive increase

- **WHEN** 한 column의 null rate가 0.125에서 0.25로 증가하고 threshold가 0일 때
- **THEN** 해당 column의 `null_spike` incident와 delta 0.125 evidence를 생성해야 한다.

#### Scenario: Positive delta equality

- **WHEN** 한 column의 null rate가 0.125에서 0.25로 증가하고 threshold가 0.125일 때
- **THEN** 해당 column의 `null_spike` incident를 생성해야 한다.
