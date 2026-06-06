# reliability-contracts Specification

## ADDED Requirements

### Requirement: Incident contract

시스템은 Data Reliability Incident를 구조화된 contract로 표현해야 한다.

#### Scenario: 유효한 incident 생성

- **GIVEN** 품질 이상이 특정 `asset_name`과 `partition`에서 발견됨
- **WHEN** Detector 또는 fixture가 `Incident`를 생성함
- **THEN** incident는 `incident_id`, `asset_name`, `partition`, `incident_type`, `severity`, `status`, `owner`, `evidence_refs`, `human_review_status`를 포함해야 함
- **AND** `evidence_refs`는 최소 1개 이상이어야 함

### Requirement: Evidence contract

시스템은 RCA와 영향 분석에 사용할 evidence를 독립적으로 참조 가능한 contract로 표현해야 한다.

#### Scenario: evidence 참조

- **GIVEN** profile, metadata, dbt artifact, catalog, Dagster 중 하나에서 근거가 수집됨
- **WHEN** `Evidence`가 생성됨
- **THEN** evidence는 `evidence_id`, `source`, `asset_name`, `partition`, `observed_at`, `summary`, `payload`를 포함해야 함
- **AND** incident는 `evidence_id`를 통해 evidence를 참조해야 함

### Requirement: ProfileSnapshot contract

시스템은 Detector 입력 지표를 `ProfileSnapshot`으로 표현해야 한다.

#### Scenario: profile 기반 탐지 입력

- **GIVEN** 특정 asset partition의 profile이 계산됨
- **WHEN** `ProfileSnapshot`이 생성됨
- **THEN** snapshot은 `row_count`, `null_rates`, `schema_hash`, `freshness_at`, `metric_values`를 포함해야 함
- **AND** JSON 직렬화가 가능해야 함

### Requirement: LineageEvidence contract

시스템은 downstream 영향 범위를 `LineageEvidence`로 표현해야 한다.

#### Scenario: downstream 영향 범위 계산 결과

- **GIVEN** dbt artifact에서 lineage가 조회됨
- **WHEN** `LineageEvidence`가 생성됨
- **THEN** `upstream_asset`, `downstream_assets`, `dbt_manifest_path`, `dbt_run_results_path`를 포함해야 함
- **AND** downstream asset 목록은 incident의 `affected_assets`로 연결 가능해야 함

### Requirement: Approval contract

시스템은 위험 작업 실행 여부를 `Approval` contract로 표현해야 한다.

#### Scenario: 승인된 작업만 실행 가능

- **GIVEN** incident remediation plan이 생성됨
- **WHEN** `Approval.status`가 `approved`임
- **THEN** approval은 `approved_by`와 `approved_at`을 포함해야 함
- **AND** partition overwrite, backfill, validation workflow 실행 대상으로 사용할 수 있어야 함

#### Scenario: 미승인 작업 차단

- **GIVEN** incident remediation plan이 생성됨
- **WHEN** `Approval.status`가 `pending` 또는 `rejected`임
- **THEN** partition overwrite, backfill, validation workflow 실행 대상으로 사용할 수 없어야 함
