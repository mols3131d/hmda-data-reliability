## ADDED Requirements

### Requirement: dbt manifest downstream traversal

시스템은 dbt `manifest.json`의 dependency graph를 읽어 특정 upstream asset의 downstream nodes를 계산해야 한다(SHALL).

#### Scenario: source에서 mart까지 downstream 계산

- **WHEN** upstream asset이 `source.project_pivot.raw.yellow_tripdata`일 때
- **THEN** downstream asset 목록에는 해당 source를 참조하는 staging/mart nodes가 포함되어야 한다.

### Requirement: LineageEvidence generation

시스템은 downstream 계산 결과를 `LineageEvidence` contract로 반환해야 한다(SHALL).

#### Scenario: lineage evidence 생성

- **WHEN** impact analysis가 실행될 때
- **THEN** `LineageEvidence`는 upstream asset, downstream assets, manifest path, run results path를 포함해야 한다.

### Requirement: Incident affected assets update

시스템은 impact analysis 결과를 incident의 `affected_assets`에 반영해야 한다(SHALL).

#### Scenario: affected assets 연결

- **WHEN** incident asset의 downstream nodes가 계산될 때
- **THEN** 반환된 incident의 `affected_assets`는 downstream asset 목록과 같아야 한다.
