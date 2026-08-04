# foundation-baseline Specification

## Purpose

기초 문서를 현재 repo의 foundation 완료 증거, 제외 범위, 후속 MVP 후보와 연결하는 기준선을 정의한다.

## Requirements

### Requirement: Foundation source alignment

시스템은 기초 문서의 foundation 목적, 원칙, MVP 범위, 작업 순서를 repo의 공식 기준선과 연결해야 한다(SHALL). 공식 기준선은 기초 문서의 반복 설명을 그대로 복제하지 않고 완료 판단에 필요한 핵심 요구만 제공해야 한다(MUST).

#### Scenario: foundation 기준선 입력 확인

- **WHEN** 사용자가 foundation 기준선을 확인할 때
- **THEN** repo 문서는 `docs/development/foundation/` 문서를 입력 근거로 참조해야 한다.

#### Scenario: 문서 역할 중복 방지

- **WHEN** 사용자가 proposal, architecture, tech stack, MVP scope 역할을 비교할 때
- **THEN** foundation 기준선은 비전, 아키텍처, 구현 후보, 완료 증거를 서로 다른 역할로 구분해야 한다.

### Requirement: Foundation evidence inventory

시스템은 foundation 완료 증거를 OpenSpec archive, 현재 spec, 테스트 명령으로 추적 가능하게 제공해야 한다(SHALL). foundation 증거에는 HMDA raw data의 기초 EDA, reliability contract, HMDA data foundation, partition ingestion, dbt analytics foundation이 포함되어야 한다(MUST).

#### Scenario: 완료된 foundation capability 확인

- **WHEN** 사용자가 foundation 완료 증거를 확인할 때
- **THEN** 문서는 완료된 OpenSpec archive와 현재 spec 위치를 함께 제공해야 한다.
- **AND** 각 foundation capability는 검증 가능한 테스트 또는 명령을 가져야 한다.

### Requirement: Foundational EDA readiness

다루는 데이터의 기초 EDA는 foundation 완료 전에 수행되어야 한다(SHALL). EDA는 원천 데이터의 schema, 전체 및 주요 partition별 volume, required column null baseline, freshness boundary를 read-only evidence로 확인해야 한다(MUST). EDA 결과와 재현 경로는 domain 문서, 실행 가능한 notebook 또는 script, automated test command로 추적 가능해야 한다(MUST).

#### Scenario: HMDA 기초 EDA 완료 확인

- **WHEN** 사용자가 foundation readiness를 검토할 때
- **THEN** HMDA 원천 CSV에 대한 schema, row count, `activity_year`별 row count, required-column null rate, freshness boundary evidence를 확인할 수 있어야 한다.
- **AND** EDA는 원천 파일, Bronze table, incident lifecycle을 변경하지 않는 read-only 실행이어야 한다.
- **AND** EDA correctness와 notebook smoke를 검증하는 test 또는 command가 문서에 제공되어야 한다.

#### Scenario: contract 기준 확인

- **WHEN** 사용자가 foundation contract 범위를 확인할 때
- **THEN** `Incident`, `Evidence`, `ProfileSnapshot`, `LineageEvidence`, `Approval` contract가 foundation evidence inventory에 포함되어야 한다.

### Requirement: MVP boundary separation

시스템은 foundation 완료 범위와 MVP 구현 후보를 분리해야 한다(SHALL). detector, LangGraph RCA workflow, Dagster asset graph, production deployment, dashboard UI는 foundation 완료 범위에 포함하지 않아야 한다(MUST NOT).

#### Scenario: 다음 작업 선택

- **WHEN** 사용자가 foundation 이후 다음 OpenSpec 변경을 선택할 때
- **THEN** 문서는 profile snapshot, incident detection, impact analysis, remediation draft, approval/backfill/validation, evaluation report를 후속 MVP 후보로 보여야 한다.

#### Scenario: foundation 제외 범위 확인

- **WHEN** 사용자가 foundation 완료 여부를 검토할 때
- **THEN** detector, LangGraph, Dagster asset graph가 구현되지 않았다는 이유만으로 foundation baseline이 미완료로 판단되지 않아야 한다.

### Requirement: Foundation readiness verification

시스템은 foundation baseline이 현재 repo 상태에서 검증 가능하도록 readiness checklist를 제공해야 한다(SHALL). checklist는 문서 경로, OpenSpec 상태, 테스트 명령을 포함해야 한다(MUST).

#### Scenario: readiness checklist 검증

- **WHEN** 사용자가 foundation readiness 문서를 열 때
- **THEN** 완료 증거, 제외 범위, 다음 작업, 검증 명령이 한 화면에서 확인 가능해야 한다.

#### Scenario: OpenSpec workflow 적용 확인

- **WHEN** 사용자가 foundation baseline OpenSpec 변경 이력을 확인할 때
- **THEN** `openspec/changes/archive/` 아래 `2026-06-10-complete-foundation-baseline` archive에 proposal, design, specs, tasks artifact가 있어야 한다.
