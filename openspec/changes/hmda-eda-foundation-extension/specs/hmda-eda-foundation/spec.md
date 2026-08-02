---
type: openspec-rpi
category: spec
relatedArtifacts:
  - hmda-eda-foundation-extension
title: "HMDA foundation EDA"
description: "MVP reliability 개발에 필요한 HMDA descriptive EDA evidence contract"
---

## ADDED Requirements

### Requirement: Core descriptive EDA evidence

시스템은 HMDA 원천 파일에 대해 schema, 전체 row count, `activity_year`별 volume, required-column null baseline과 freshness boundary를 포함하는 JSON-serializable descriptive EDA evidence를 생성해야 한다(SHALL). 기존 evidence key와 read-only 동작은 유지해야 한다(MUST).

EDA analysis, deterministic fixture와 resource helper는 `project_pivot.hmda_data.eda` subpackage가 소유해야 하며(SHALL), 기존 `project_pivot.hmda_data.analyze_hmda_csv` public import는 유지되어야 한다(MUST).

#### Scenario: Core evidence generation

- **WHEN** 유효한 HMDA CSV를 EDA entrypoint에 전달할 때
- **THEN** evidence는 schema, row count, activity-year counts, required-column null counts/rates와 freshness 상태를 포함해야 한다.
- **AND** 원천 파일과 lifecycle 상태는 변경되지 않아야 한다.

#### Scenario: EDA package compatibility

- **WHEN** 기존 caller가 `project_pivot.hmda_data` public package에서 `analyze_hmda_csv`를 import할 때
- **THEN** subpackage 전환 뒤에도 동일한 public callable을 사용할 수 있어야 한다.
- **AND** fixture와 resource helper는 `project_pivot.hmda_data.eda` namespace에서 import할 수 있어야 한다.

### Requirement: Core code distributions

시스템은 `action_taken`, `loan_purpose`, `state_code`와 선택적으로 `county_code`의 observed value별 count와 share를 제공해야 한다(SHALL). 허용 code 밖의 값은 정제하지 않고 unknown 또는 anomaly observation으로 식별해야 한다(MUST).

#### Scenario: Code distribution evidence

- **WHEN** 핵심 code field가 존재하는 HMDA source를 분석할 때
- **THEN** 각 field의 observed value별 count와 전체 row 대비 share를 반환해야 한다.
- **AND** count의 합은 해당 field의 분석 population과 일치해야 한다.

#### Scenario: Unknown code preservation

- **WHEN** 허용 code 목록에 없는 값이 관찰될 때
- **THEN** 해당 값과 count는 anomaly observation으로 기록되어야 한다.
- **AND** 원천 row는 삭제되거나 자동 변환되지 않아야 한다.

### Requirement: Numeric summary and anomaly observation

시스템은 `loan_amount`와 `income`에 대해 non-null count, min, p25, median, p75, max와 suspicious range count를 제공해야 한다(SHALL). domain 의미가 확정되지 않은 extreme value는 관찰 flag로만 기록해야 한다(MUST).

#### Scenario: Numeric summary evidence

- **WHEN** 수치형 핵심 field가 포함된 HMDA source를 분석할 때
- **THEN** 각 대상 field에 대해 non-null count와 five-number summary를 반환해야 한다.
- **AND** summary는 원천 값을 삭제하거나 임의의 범위로 clipping하지 않고 계산되어야 한다.

#### Scenario: Suspicious numeric observation

- **WHEN** `income < 0`, `loan_amount <= 0` 또는 configured suspicious condition이 관찰될 때
- **THEN** field, condition, count와 share가 anomaly observation에 포함되어야 한다.
- **AND** anomaly는 자동 정제나 incident 생성으로 이어지지 않아야 한다.

### Requirement: MVP grain alignment

시스템은 `activity_year + state_code + loan_purpose` grain을 기준으로 aggregate row count와 핵심 metric의 연결을 확인할 수 있는 evidence를 제공해야 한다(SHALL). EDA는 새로운 canonical business grain을 정의하거나 현재 mart grouping rule을 변경해서는 안 된다(MUST NOT).

#### Scenario: Mart grain evidence

- **WHEN** HMDA source에 현재 mart의 grain field가 존재할 때
- **THEN** EDA evidence는 해당 grain의 aggregate count와 null/coverage 상태를 포함해야 한다.
- **AND** grain key와 metric 해석은 current dbt mart contract와 일치해야 한다.

### Requirement: Reproducible validation surfaces

시스템은 deterministic fixture correctness, representative resource validation, actual-source observation과 notebook runtime smoke를 서로 구분된 validation surface로 제공해야 한다(SHALL).

#### Scenario: Fixture and source validation separation

- **WHEN** EDA validation을 실행할 때
- **THEN** fixture test는 deterministic expected value를 검증해야 한다.
- **AND** actual-source observation은 source path와 실행 결과를 기록해야 하며 immutable fixture assertion으로 취급하지 않아야 한다.

#### Scenario: Notebook runtime smoke

- **WHEN** valid fixture와 malformed fixture로 EDA notebook smoke를 실행할 때
- **THEN** valid 입력은 evidence rendering path를 완료해야 한다.
- **AND** malformed 입력은 partial evidence 없이 명시된 exception 상태를 반환해야 한다.
