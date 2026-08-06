---
type: openspec-spec-driven-tdd-spec
category: spec
title: "hmda-eda-baseline"
description: "Align HMDA descriptive EDA with the six-core evidence contract and reproducible readiness evidence."
tags:
  - "domain:hmda-data"
  - "subdomain:eda"
  - "capability:hmda-eda-baseline"
  - "contract-reconciliation"
---

## MODIFIED Requirements

### Requirement: HMDA required schema baseline

EDA는 ingestion required-column contract를 충족한 source에서 `activity_year`, `state_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`의 inferred type family compatibility를 검증해야 한다(SHALL). EDA는 `county_code`를 type compatibility, null baseline 또는 descriptive metric 대상으로 포함해서는 안 된다(MUST NOT). 직접 호출에서 6개 core column 중 하나가 누락되거나 호환되지 않는 type이면 partial evidence 없이 실패해야 한다(MUST).

#### Scenario: Six-core columns are compatible

- **WHEN** source가 6개 core column의 호환 타입을 포함할 때
- **THEN** EDA는 각 core column의 inferred type과 valid compatibility status를 제공해야 한다.
- **AND** `county_code`는 EDA required-column 결과에 포함되어서는 안 된다.

#### Scenario: A core column is missing or incompatible

- **WHEN** 직접 호출한 source에 6개 core column 중 하나가 없거나 type family가 호환되지 않을 때
- **THEN** EDA는 대상 column을 식별하는 validation failure로 종료해야 한다.
- **AND** partial evidence를 반환해서는 안 된다.

### Requirement: Volume and null baseline

EDA는 전체 row count, `activity_year`별 row count와 6개 core column별 null count·null rate를 제공해야 한다(SHALL). `NA`와 빈 문자열은 null로 해석해야 한다(MUST).

#### Scenario: Core null baseline calculation

- **WHEN** 유효한 HMDA source를 분석할 때
- **THEN** EDA는 정확히 6개 core column의 null count와 `null_count / total_row_count` null rate를 반환해야 한다.
- **AND** `county_code` null count 또는 rate를 반환해서는 안 된다.

### Requirement: MVP grain alignment

EDA는 `activity_year + state_code + loan_purpose`가 모두 non-null인 row의 distinct group count, 하나 이상 null인 row count와 complete-key coverage rate를 제공해야 한다(SHALL). Distinct group count는 complete-key row만 대상으로 계산해야 하며(MUST), coverage rate는 `complete_key_row_count / total_row_count`여야 한다(MUST).

#### Scenario: Complete-key grain coverage

- **WHEN** grain key 일부가 null인 HMDA source를 분석할 때
- **THEN** EDA는 null key row를 distinct group count에서 제외해야 한다.
- **AND** null key row count와 complete-key coverage rate를 반환해야 한다.

### Requirement: Reusable EDA computation boundary

시스템은 HMDA CSV path와 명시적인 DuckDB resource 설정을 입력받아 JSON-serializable 및 YAML-exportable core evidence를 반환해야 한다(SHALL). `duration_seconds`는 type validation 이후부터 모든 retained evidence aggregate를 마친 시점까지의 전체 EDA 계산 시간을 나타내야 한다(MUST). anomaly, freshness, schema hash 또는 Profile mapping evidence를 포함하거나 계산해서는 안 된다(MUST NOT).

#### Scenario: Full retained evidence duration

- **WHEN** 유효한 source를 분석할 때
- **THEN** 반환된 duration은 volume, distribution, numeric summary 및 grain evidence 계산을 모두 포함해야 한다.
- **AND** source observation timestamp가 존재해도 freshness aggregation을 수행하거나 반환해서는 안 된다.

### Requirement: Agent-friendly Python and YAML EDA exploration

EDA 결과는 에이전트(LLM 에이전트/CLI) 환경에서 쉽게 읽고 해석할 수 있도록 일반 Python API 및 YAML(`yml`) 직렬화 형태로 제공될 수 있어야 한다(SHALL). 시각화 요구 시 정적 이미지 파일(PNG/SVG) 또는 독립 실행형 HTML 차트 파일 형태로 렌더링해 반환해야 한다(SHALL). 마리모(Marimo) 반응형 UI 노트북은 사용해서는 안 된다(MUST NOT).

#### Scenario: YAML evidence generation

- **WHEN** EDA 탐색 결과를 YAML 형식으로 내보내거나 조회할 때
- **THEN** schema, volume, null metrics, categorical distribution, numeric summary 및 grouping-key coverage가 구조화된 YAML 형태로 포함되어야 한다.

#### Scenario: Static chart visualization export

- **WHEN** EDA 분포 및 경향성에 대한 시각화를 요청할 때
- **THEN** 마리모 노트북 서빙 없이 정적 이미지 파일(PNG) 또는 독립 실행형 HTML 파일 형태로 시각화 차트를 내보내야 한다.

### Requirement: Actual-source observation

Foundation EDA gate의 actual-source observation은 한 controlled run에서 machine-readable JSON과 그 JSON에서 파생한 human-readable summary를 생성해야 한다(SHALL). 두 artifact는 source logical identifier, source fingerprint, repository revision, execution timestamp, total duration 및 동일한 key metrics를 기록해야 한다(MUST). Evidence가 유효하지 않거나 재생성되지 않은 동안 EDA readiness는 blocked여야 한다(MUST).

#### Scenario: Evidence consistency

- **WHEN** actual-source observation을 수행할 때
- **THEN** Markdown summary의 income null count와 grain distinct group count는 같은 run의 JSON 값과 일치해야 한다.
- **AND** absolute local source path와 temporary directory path는 canonical evidence에 포함되어서는 안 된다.

#### Scenario: Evidence is not regenerated

- **WHEN** current code revision에 대한 controlled actual-source observation이 없을 때
- **THEN** EDA readiness는 blocked 또는 unverified로 표시되어야 한다.
- **AND** Foundation completion evidence로 표현되어서는 안 된다.
