# reliability-data-contracts Specification

## Purpose

데이터 신뢰성 인시던트, 근거, 프로파일, 계보 영향, 승인 상태를 일관된 data contract로 교환하기 위한 요구사항을 정의한다.

## Requirements

### Requirement: Incident contract

시스템은 Data Reliability Incident를 구조화된 contract로 표현해야 한다(SHALL).

#### Scenario: 유효한 incident 생성

- **GIVEN** 품질 이상이 특정 `asset_name`과 `partition`에서 발견됨
- **WHEN** 해당 이상을 `Incident` contract로 표현할 때
- **THEN** incident는 `incident_id`, `asset_name`, `partition`, `incident_type`, `severity`, `status`, `owner`, `evidence_refs`, `human_review_status`를 포함해야 함
- **AND** `evidence_refs`는 최소 1개 이상이어야 함

### Requirement: Evidence contract

시스템은 RCA와 영향 분석에 사용할 evidence를 독립적으로 참조 가능한 contract로 표현해야 한다(SHALL).

#### Scenario: evidence 참조

- **GIVEN** profile, metadata, dbt artifact, catalog, Dagster 중 하나에서 근거가 수집됨
- **WHEN** `Evidence`가 생성됨
- **THEN** evidence는 `evidence_id`, `source`, `asset_name`, `partition`, `observed_at`, `summary`, `payload`를 포함해야 함
- **AND** incident는 `evidence_id`를 통해 evidence를 참조해야 함

### Requirement: ProfileSnapshot contract

시스템은 incident detection 입력 지표를 `ProfileSnapshot`으로 표현해야 한다(SHALL). Snapshot은 `row_count`, `null_rates`, `schema_hash`, nullable `freshness_at`, `freshness_status`와 `metric_values`를 포함하고 JSON으로 직렬화 가능해야 한다(SHALL). `freshness_status=measured`이면 `freshness_at`이 반드시 존재하고, `freshness_status=unavailable`이면 `freshness_at`은 반드시 `null`이어야 한다(MUST).

#### Scenario: Measured profile input

- **GIVEN** partition freshness timestamp가 측정되었을 때
- **WHEN** `ProfileSnapshot`을 생성하고 JSON으로 직렬화할 때
- **THEN** `freshness_status`는 `measured`이고 `freshness_at`은 측정 timestamp여야 한다.

#### Scenario: Unavailable profile input

- **GIVEN** partition freshness timestamp를 측정할 수 없을 때
- **WHEN** `ProfileSnapshot`을 생성하고 JSON으로 직렬화할 때
- **THEN** `freshness_status`는 `unavailable`이고 `freshness_at`은 `null`이어야 한다.

#### Scenario: Inconsistent freshness fields

- **WHEN** measurement status와 nullable timestamp가 서로 일치하지 않는 snapshot을 생성할 때
- **THEN** contract validation은 해당 snapshot을 거부해야 한다.

### Requirement: LineageEvidence contract

시스템은 downstream 영향 범위를 `LineageEvidence`로 표현해야 한다(SHALL).

#### Scenario: downstream 영향 범위 계산 결과

- **GIVEN** dbt artifact에서 lineage가 조회됨
- **WHEN** `LineageEvidence`가 생성됨
- **THEN** `upstream_asset`, `downstream_assets`, `dbt_manifest_path`, `dbt_run_results_path`를 포함해야 함
- **AND** downstream asset 목록은 incident의 `affected_assets`로 연결 가능해야 함

### Requirement: Approval contract

시스템은 위험 작업 실행 여부를 `Approval` contract로 표현해야 한다(SHALL).

#### Scenario: 승인된 작업만 실행 가능

- **GIVEN** incident remediation plan이 생성됨
- **WHEN** `Approval.status`가 `approved`임
- **THEN** approval은 `approved_by`와 `approved_at`을 포함해야 함
- **AND** partition overwrite, backfill, validation workflow 실행 대상으로 사용할 수 있어야 함

#### Scenario: 미승인 작업 차단

- **GIVEN** incident remediation plan이 생성됨
- **WHEN** `Approval.status`가 `pending` 또는 `rejected`임
- **THEN** partition overwrite, backfill, validation workflow 실행 대상으로 사용할 수 없어야 함
