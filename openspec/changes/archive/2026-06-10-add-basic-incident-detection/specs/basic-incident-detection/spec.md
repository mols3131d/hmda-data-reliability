## ADDED Requirements

### Requirement: Rule-based profile comparison

시스템은 baseline `ProfileSnapshot`과 current `ProfileSnapshot`을 비교해 기본 품질 이상을 탐지해야 한다(SHALL). 탐지 대상은 row count drop, null spike, schema drift, freshness delay를 포함해야 한다(MUST).

#### Scenario: 정상 profile 비교

- **WHEN** baseline과 current profile이 threshold를 넘지 않을 때
- **THEN** detector는 incident를 생성하지 않아야 한다.

### Requirement: Volume drop detection

시스템은 current row count가 baseline 대비 설정 비율 이상 감소하면 `volume_drop` incident를 생성해야 한다(SHALL).

#### Scenario: row count 급감 탐지

- **WHEN** baseline row count가 100이고 current row count가 40이며 volume drop threshold가 0.5일 때
- **THEN** detector는 `volume_drop` incident와 profile evidence를 생성해야 한다.
- **AND** evidence payload에는 baseline row count, current row count, drop ratio가 포함되어야 한다.

### Requirement: Null spike detection

시스템은 current null rate가 baseline null rate 대비 설정 delta 이상 증가하면 `null_spike` incident를 생성해야 한다(SHALL).

#### Scenario: null rate 급증 탐지

- **WHEN** 특정 컬럼의 baseline null rate가 0.01이고 current null rate가 0.20이며 null spike threshold가 0.10일 때
- **THEN** detector는 `null_spike` incident와 profile evidence를 생성해야 한다.
- **AND** evidence payload에는 대상 컬럼명과 baseline/current null rate가 포함되어야 한다.

### Requirement: Schema drift detection

시스템은 baseline schema hash와 current schema hash가 다르면 `schema_drift` incident를 생성해야 한다(SHALL).

#### Scenario: schema hash 변경 탐지

- **WHEN** baseline과 current profile의 schema hash가 다를 때
- **THEN** detector는 `schema_drift` incident와 profile evidence를 생성해야 한다.

### Requirement: Freshness delay detection

시스템은 current freshness가 baseline freshness보다 설정 임계치 이상 지연되면 `freshness_delay` incident를 생성해야 한다(SHALL).

#### Scenario: freshness 지연 탐지

- **WHEN** current freshness가 baseline freshness보다 threshold 이상 오래되었을 때
- **THEN** detector는 `freshness_delay` incident와 profile evidence를 생성해야 한다.

### Requirement: Incident and evidence linkage

시스템은 탐지된 각 이상마다 `Incident`와 `Evidence`를 생성하고 `Incident.evidence_refs`에 생성한 evidence id를 포함해야 한다(SHALL).

#### Scenario: evidence ref 연결

- **WHEN** detector가 incident를 생성할 때
- **THEN** incident는 최소 1개 evidence id를 가져야 한다.
- **AND** 해당 evidence id는 같은 detection result의 evidence id와 일치해야 한다.
