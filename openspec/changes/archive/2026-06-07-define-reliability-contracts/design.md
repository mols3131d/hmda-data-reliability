# Design

## 개요

`project_pivot.reliability.contracts` 모듈을 추가하고, 외부 contract는 Pydantic `BaseModel`로 정의한다. LangGraph State는 이후 작업에서 `TypedDict`로 별도 정의하되, State 내부 payload는 이 contract를 사용한다.

## Contract 구조

### Incident

품질 이상 사건의 중심 객체다.

주요 필드:

- `incident_id`
- `asset_name`
- `partition`
- `incident_type`
- `severity`
- `status`
- `owner`
- `evidence_refs`
- `affected_assets`
- `recommended_actions`
- `human_review_status`

### Evidence

RCA와 영향 분석이 참조하는 구조화 근거다. 모든 evidence는 `evidence_id`, `source`, `asset_name`, `partition`, `observed_at`, `summary`, `payload`를 가진다.

### ProfileSnapshot

Detector 입력 지표다. `row_count`, `null_rates`, `schema_hash`, `freshness_at`, `metric_values`를 포함한다.

### LineageEvidence

downstream 영향 범위를 표현한다. `upstream_asset`, `downstream_assets`, `dbt_manifest_path`, `dbt_run_results_path`를 포함한다.

### Approval

위험 작업 실행 가능 여부를 표현한다. `status = approved`일 때만 partition overwrite, backfill, validation 실행 대상으로 사용할 수 있다.

## 상태 값

Enum은 문자열 기반으로 정의해 JSON 출력 안정성을 유지한다.

- `IncidentSeverity`: `low`, `medium`, `high`, `critical`
- `IncidentStatus`: `detected`, `triaged`, `planned`, `approved`, `remediated`, `validated`, `closed`
- `HumanReviewStatus`: `pending`, `approved`, `rejected`
- `EvidenceSource`: `profile`, `table_metadata`, `dbt_artifact`, `catalog`, `dagster`
- `ApprovalStatus`: `pending`, `approved`, `rejected`

## Validation 원칙

- `evidence_refs`는 비어 있으면 안 된다.
- `Approval.status = approved`이면 `approved_by`와 `approved_at`이 필요하다.
- `Approval.status`가 `pending` 또는 `rejected`이면 실행 가능한 action으로 취급하지 않는다.
- contract는 `model_dump(mode="json")`로 직렬화 가능해야 한다.

## 오류 처리

contract 생성 또는 validation 실패를 domain/application 경계에서 다룰 수 있도록 custom exception을 추가한다. 사용자/API 응답에는 raw stack trace를 노출하지 않는다.

## 테스트 전략

- 최소 유효 `Incident` fixture 생성 테스트
- `Evidence` 참조가 없는 incident validation 실패 테스트
- 승인된 `Approval`의 필수 승인자/시간 검증 테스트
- JSON 직렬화 snapshot 성격의 필드 안정성 테스트
