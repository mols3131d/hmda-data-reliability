# orchestration-pipeline Delta Spec (orchestration-quality-gate)

## Delta Purpose

`hmda_data_plane` DAG의 기존 `orchestration-pipeline` spec에 quality gate requirement를 추가한다.

## ADDED Requirements

### Requirement: Data quality gate execution

시스템은 raw load 성공 후 analytics build 이전에 신뢰성 품질 게이트를 실행해야 한다(SHALL). Gate는 canonical dbt source relation과 partition column을 사용해 dbt가 소비할 전체 Bronze population을 평가해야 하며(MUST), quality-gated analytics build는 bundled canonical dbt project/profile configuration을 사용해야 한다(MUST). Analytics build는 database mutation lock 안에서 같은 전체 gate를 재검증한 뒤 동일한 lock을 유지한 채 dbt subprocess를 시작해야 한다(MUST). Orchestration은 task dependency와 task state만 조율하고, profile 구성과 lock-bound build 조합은 Data Operations에, baseline, threshold, detector와 blocking 판정은 Reliability public boundary에 위임해야 한다(MUST). 품질 게이트는 structural validation failure(파티션 식별자 누락, 프로파일 컬럼 계약 불일치)와 detector incident(통계적 이상 탐지)를 구분해 평가해야 하며(MUST), detector incident 중에서는 null spike와 empty partition만 pipeline을 차단해야 한다(SHALL).

#### Scenario: Quality gate passes – no anomaly detected

- **GIVEN** 적재된 파티션의 null rate, row count가 baseline 범위 내에 있을 때
- **WHEN** `evaluate_quality_gate` 태스크가 실행될 때
- **THEN** 태스크는 성공(정상 완료)해야 함
- **AND** 다운스트림 analytics build 태스크가 실행되어야 함

#### Scenario: Quality gate fails – anomaly detected

- **GIVEN** 적재된 파티션에서 이상(예: null spike)이 탐지될 때
- **WHEN** `evaluate_quality_gate` 태스크가 실행될 때
- **THEN** 태스크는 명시적으로 실패해야 함
- **AND** 탐지된 인시던트 유형이 실패 메시지에 포함되어야 함
- **AND** 다운스트림 analytics build 태스크는 실행되지 않아야 함

#### Scenario: Dirty non-requested partition

- **GIVEN** 요청 파티션은 clean이지만 dbt source가 함께 읽는 다른 Bronze 파티션에 blocking 이상이 있을 때
- **WHEN** quality gate가 실행될 때
- **THEN** gate는 dirty 파티션을 식별해 실패해야 함
- **AND** analytics build를 실행해서는 안 됨

#### Scenario: Canonical dbt source relation

- **GIVEN** caller가 canonical `raw.hmda_loans`와 다른 relation 또는 partition column을 quality-gated build request에 지정했을 때
- **WHEN** quality gate가 실행될 때
- **THEN** gate는 dbt가 실제 소비하는 source와 다른 relation을 평가해서는 안 됨
- **AND** request는 dbt source contract 불일치로 거부되어야 함

#### Scenario: Canonical quality-gated dbt configuration

- **GIVEN** caller가 bundled configuration과 다른 dbt project 또는 profiles directory를 quality-gated build request에 지정했을 때
- **WHEN** quality-gated analytics build가 실행될 때
- **THEN** dbt subprocess를 시작하기 전에 request를 거부해야 함
- **AND** 독립 `run_dbt_build()`의 configurable project/profile contract는 유지되어야 함

#### Scenario: Requested partition is absent

- **GIVEN** 다른 clean Bronze 파티션은 존재하지만 요청 파티션에는 행이 없을 때
- **WHEN** quality gate가 실행될 때
- **THEN** 요청 파티션도 평가되어 `empty_partition`으로 실패해야 함

#### Scenario: Missing partition discriminator

- **GIVEN** canonical Bronze source에 `activity_year`가 `NULL`인 행이 있을 때
- **WHEN** quality gate가 실행될 때
- **THEN** profile되지 않는 행을 허용하지 않고 partition discriminator 오류로 실패해야 함

#### Scenario: Bronze changes after gate task

- **GIVEN** 독립 quality gate task가 통과한 뒤 analytics task 시작 전 Bronze 상태가 변경되었을 때
- **WHEN** analytics build가 database mutation lock을 획득할 때
- **THEN** 같은 lock 안에서 전체 Bronze gate를 다시 평가해야 함
- **AND** blocking 이상이 있으면 dbt subprocess를 시작해서는 안 됨
- **AND** analytics task는 `QualityGateError`를 causal context가 보존된 `AirflowException`으로 변환해야 함

#### Scenario: Quality gate evidence

- **WHEN** quality gate 태스크가 성공 또는 실패로 완료될 때
- **THEN** `source_year`, `asset_name`, `detected_incident_types` 또는 `status: clean`이 로그에 기록되어야 함

#### Scenario: Delegated quality policy

- **WHEN** quality gate 태스크가 현재 파티션을 평가할 때
- **THEN** Orchestration은 baseline, threshold 또는 detector 선택을 직접 구현해서는 안 됨
- **AND** Reliability public boundary가 blocking 판정을 수행해야 함
- **AND** Data Operations가 전체 Bronze partition profile, Reliability 호출과 lock-bound quality-gated build를 조합해야 함

#### Scenario: Required profile coverage

- **WHEN** quality gate가 current profile을 평가할 때
- **THEN** Reliability policy가 요구하는 모든 profile column이 current profile에 존재해야 함
- **AND** 필수 column이 누락되거나 지원하지 않는 column이 추가되면 gate는 평가를 거부해야 함
- **AND** 거부 로그에 `source_year`, `asset_name`과 profile coverage failure discriminator가 기록되어야 함

#### Scenario: MVP blocking incident scope

- **WHEN** Reliability quality gate가 detector incident 결과를 blocking policy에 적용할 때
- **THEN** detector incident 중에서는 null spike와 empty partition만 pipeline을 차단해야 함
- **AND** volume drop, schema drift 또는 freshness delay 결과만으로는 gate가 실패해서는 안 됨
- **AND** missing partition discriminator 또는 profile coverage failure와 같은 structural validation failure는 detector incident와 구분되어 gate를 차단하거나 거부를 유발해야 함

#### Scenario: Accepted 2025 normal profile

- **GIVEN** repository가 보존한 accepted 2025 HMDA profile과 같은 null rate를 가진 non-empty 파티션이 있을 때
- **WHEN** quality gate가 해당 파티션을 평가할 때
- **THEN** gate는 정상 통과해야 함
- **AND** accepted baseline에서 null rate가 blocking delta 이상 증가하면 `null_spike`로 실패해야 함

#### Scenario: Unexpected quality gate error

- **WHEN** quality gate 실행 중 `QualityGateError`가 아닌 예상 밖 오류가 발생할 때
- **THEN** Airflow adapter는 오류 타입과 원인을 별도의 quality domain failure로 정규화해서는 안 됨
- **AND** 원래 오류가 task failure로 전달되어야 함

## MODIFIED Requirements

### Requirement: Data-plane workflow graph

시스템은 하나의 loadable data-plane workflow에서 raw load, quality gate와 analytics build stage를 제공해야 한다(SHALL). Quality gate는 raw load에 의존하고 analytics stage는 quality gate에 의존해야 한다(MUST).

#### Scenario: Workflow inspection

- **WHEN** active Airflow workflow definitions를 로드할 때
- **THEN** 정확히 하나의 full data-plane DAG와 raw load → quality gate → analytics build 실행 경로를 식별할 수 있어야 함
- **AND** 별도의 active full-pipeline orchestrator가 없어야 함

### Requirement: Ordered stage execution

시스템은 raw load가 성공한 뒤 quality gate를 실행하고, gate가 통과한 뒤 analytics stage를 실행해야 한다(SHALL). `run_dbt_build=true`인 경우 analytics stage는 성공한 dbt candidate를 promotion한 뒤에만 완료로 판정해야 한다(MUST).

#### Scenario: Successful ordered execution

- **WHEN** 유효한 request로 data-plane workflow를 실행하고 raw load, quality gate와 dbt build가 성공할 때
- **THEN** raw load → quality gate → dbt build → artifact promotion 순서가 관찰되어야 함
- **AND** current artifact projection은 검증된 candidate만 반영해야 함

#### Scenario: Raw stage failure

- **WHEN** raw load가 실패할 때
- **THEN** quality gate와 analytics stage는 실행되지 않아야 함
- **AND** workflow는 실패 상태를 관찰 가능하게 전달해야 함

#### Scenario: Quality gate failure

- **WHEN** quality gate가 blocking 이상을 탐지할 때
- **THEN** analytics stage는 실행되지 않아야 함
- **AND** workflow는 탐지된 이상을 포함한 실패 상태를 관찰 가능하게 전달해야 함

#### Scenario: Analytics stage failure

- **WHEN** dbt build 또는 artifact promotion이 실패할 때
- **THEN** analytics stage는 실패해야 함
- **AND** artifact promotion 또는 current projection 성공으로 오인되어서는 안 됨

### Requirement: Domain delegation

Orchestration은 source parsing, ingestion, analytics build, artifact promotion 또는 reliability business rule을 중복 구현하지 않고 Data Operations와 Reliability public boundary에 위임해야 한다(SHALL).

#### Scenario: Delegated workflow execution

- **WHEN** data-plane task가 domain 작업을 실행할 때
- **THEN** orchestration은 dependency, config conversion, task state와 execution evidence만 조율해야 함
- **AND** ingestion, dbt build, promotion, profile 구성 또는 quality policy를 직접 포함해서는 안 됨

### Requirement: Single pipeline orchestration owner

시스템은 Airflow data-plane workflow가 전체 실행 순서를 유일하게 소유하게 해야 하며(SHALL), 다른 domain 또는 active vendor runtime이 별도의 full-pipeline coordinator를 공개해서는 안 된다(MUST NOT).

#### Scenario: Single full-pipeline execution surface

- **WHEN** active project runtime과 configuration에서 full-pipeline 실행 surface를 확인할 때
- **THEN** Airflow data-plane workflow만 raw-to-gate-to-analytics 순서를 소유해야 함
- **AND** Dagster dependency, import, definitions, asset 또는 job configuration이 active surface에 남아서는 안 됨

### Requirement: Disabled analytics skip semantics

시스템은 `run_dbt_build=false`여도 raw load와 quality gate를 실행하고 analytics stage만 명시적으로 skip해야 한다(SHALL).

#### Scenario: dbt build disabled

- **WHEN** valid request의 `run_dbt_build`가 `false`일 때
- **THEN** raw load와 quality gate stage는 성공할 수 있어야 함
- **AND** analytics stage는 `SKIPPED` 상태여야 함
- **AND** analytics data update evidence가 없어야 함
- **AND** workflow run은 raw stage와 quality gate 성공을 보존하며 성공으로 완료할 수 있어야 함

### Requirement: Task data boundary

Task 간 실행 순서는 workflow dependency로 표현해야 하며(SHALL), domain request, result, DataFrame 또는 Arrow table을 task transport payload로 전달해서는 안 된다(MUST NOT).

#### Scenario: Non-transported domain results

- **WHEN** workflow task definitions를 검사할 때
- **THEN** `DataOperationRequest`, `RawLoadResult`, `DbtBuildResult`, DataFrame 또는 Arrow table이 task transport payload에 포함되어서는 안 됨
- **AND** raw → quality gate → analytics 순서는 task dependency로 확인할 수 있어야 함
