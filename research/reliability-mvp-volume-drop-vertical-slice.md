---
type: openspec-rpi
category: research
title: Reliability MVP Volume-Drop Vertical Slice
description: Foundation 이후 volume_drop 단일 recovery vertical slice의 범위, 안전 계약과 planning 진입 조건을 결정한다.
status: completed
tags:
  - reliability
  - mvp
  - recovery
  - volume-drop
---

> [!NOTE]
> Project Pivot의 첫 MVP는 `volume_drop` 하나를 탐지부터 승인된 recovery와 재검증까지 연결하는 vertical slice가 적절하다. 다만 approval은 partition overwrite뿐 아니라 downstream `dbt build`에도 결합되어야 하며, stale-state 차단, mutation 이후 실패 상태와 재조정, full-source identity 검증이 planning contract에 포함되어야 한다. 현재 `main`은 EDA 축소 변경을 반영했지만 Foundation completion decision은 별도 gate로 남아 있으므로 planning은 시작할 수 있어도 Apply는 Foundation 완료 근거 전까지 차단한다.

## Question

- **Primary:** 현재 architecture boundary를 유지하면서 Project Pivot의 핵심 가치를 가장 작고 안전하게 증명할 MVP는 무엇인가?
- **Scope:** 첫 incident, candidate validation, human approval, recovery, failure handling, post-recovery verification과 evidence handoff를 다룬다. 여러 incident, 운영 UI, cloud deployment와 security-grade authorization은 제외한다.
- **Stop Condition:** 하나의 vertical slice, 필수 safety contract, acceptance case와 OpenSpec planning 방향을 결정하고 주요 주장을 현재 repository evidence와 연결한다.

## Findings

### F1. `volume_drop`이 첫 recovery vertical slice에 가장 적합하다

현재 Foundation은 HMDA source ingestion, partition overwrite, read-only incident lifecycle, dbt impact analysis와 approval-gated recovery를 분리된 capability로 제공한다. `volume_drop`은 deterministic row removal, 명확한 detection oracle과 자연스러운 partition recovery를 하나의 흐름으로 연결할 수 있다.

```text
clean fixture
→ controlled volume_drop
→ Bronze + dbt pipeline
→ read-only incident lifecycle
→ recovery candidate validation
→ candidate-bound human approval
→ approved recovery
→ incident + data + dbt verification
→ run report
```

- **Evidence** - `docs/ARCHITECTURE.md`, `docs/domains/hmda-data.md`, `docs/domains/reliability.md`, `openspec/specs/incident-lifecycle-runtime/spec.md`
- **Implication** - 첫 MVP는 detector 확장보다 기존 capability 사이의 안전한 handoff와 recovery 증명에 집중해야 한다.

### F2. Approval은 실제로 수행되는 모든 mutation에 결합되어야 한다

현재 recovery API의 승인 action은 partition overwrite와 profile 재생성을 기준으로 한다. 그러나 MVP completion gate가 실제 target에서 full `dbt build`를 요구한다면 table materialization을 포함한 downstream mutation도 승인 범위다.

필수 approval binding:

| Binding | Purpose |
| --- | --- |
| Run과 incident identity | 반복 incident의 approval 재사용 차단 |
| Analysis digest | 승인한 evidence와 action 고정 |
| Target asset과 full partition key | 다른 partition 또는 source file mutation 차단 |
| Candidate file digest | 다른 recovery input 사용 차단 |
| Candidate validation digest | 검증되지 않은 candidate 실행 차단 |
| Validated target-state digest | validation 이후 target 변경 감지 |
| dbt project projection과 target | 다른 model graph 또는 target 실행 차단 |
| Approved actions | partition overwrite, profile regeneration, dbt rebuild 명시 |

MVP의 approved actions에는 최소한 다음 semantics가 포함되어야 한다.

```text
overwrite_partition
rerun_profile_snapshot
rebuild_dbt_models
```

- **Evidence** - `src/project_pivot/reliability/contracts/approval.py`, `src/project_pivot/reliability/recovery/executor.py`, `dbt/dbt_project.yml`
- **Implication** - `dbt build`를 검증 단계라고만 부르면 승인하지 않은 side effect가 생긴다. Planning은 이를 하나의 승인된 recovery operation 또는 명시적으로 분리된 승인 action으로 정의해야 한다.

### F3. Stale approval 차단은 target 확인과 overwrite 사이의 경쟁 조건을 닫아야 한다

Validation은 current target의 일관된 copy에서 수행하고 target-state digest를 기록해야 한다. Recovery 시점에는 exclusive local writer gate를 획득한 뒤 같은 target state를 transaction 안에서 다시 확인하고 partition overwrite를 수행해야 한다.

```text
candidate validation:
exclusive local writer gate
→ consistent target copy
→ candidate apply in copy
→ full dbt build
→ validation digest
→ release gate

approved recovery:
exclusive local writer gate
→ transaction
→ target-state digest recheck
→ partition overwrite
→ commit
→ release transaction
```

MVP는 local single-writer system으로 제한한다. Gate 획득 실패, target-state mismatch 또는 concurrent mutation evidence가 있으면 mutation 전에 중단하고 candidate validation부터 다시 수행한다.

- **Evidence** - current partition loader는 delete와 insert를 하나의 DuckDB transaction으로 수행하지만 approval freshness 확인은 현재 recovery contract에 없다.
- **Implication** - digest 비교만 추가해서는 stale approval을 막을 수 없다. Single-writer gate와 transaction boundary가 behavioral contract에 포함되어야 한다.

### F4. Mutation 이후 실패는 일반적인 `failed`와 구분해야 한다

Partition overwrite 이후 profile, fingerprint, dbt build, report writing 또는 process 실행이 실패할 수 있다. 이 상태를 mutation 전 실패와 동일한 `failed`로 기록하면 target이 변경됐는지 판단할 수 없다.

필요한 semantic state:

```text
analyzed
→ validated
→ approved
→ recovery_started
→ partition_replaced
→ verified

validated → rejected
before mutation → failed
partition_replaced → verification_failed
verification_failed → reconciled | verified
```

MVP에서는 cross-system rollback을 약속하지 않는다. 대신 다음을 보장한다.

- partition commit 직후 `partition_replaced` evidence를 durable하게 기록한다.
- downstream verification 실패는 `verification_failed`로 남긴다.
- 같은 run, approval과 candidate에 한해 idempotent reconciliation을 허용한다.
- reconciliation은 partition fingerprint를 확인하고 필요할 때만 overwrite를 반복한 뒤 profile과 full `dbt build`를 재실행한다.
- 완료되지 않은 recovery를 성공으로 보고하지 않는다.

- **Evidence** - current architecture는 recovery와 dbt execution을 별도 boundary로 두므로 하나의 transaction rollback으로 묶을 수 없다.
- **Implication** - Recovery correctness에는 success oracle뿐 아니라 partial failure의 관찰 가능성과 재개 계약이 필요하다.

### F5. Candidate validation은 적용된 data result까지 approval에 결합해야 한다

Candidate file digest만으로는 candidate가 target schema와 ingestion contract를 거쳐 어떤 rows가 되었는지 증명하지 못한다. Validation digest에는 candidate를 temporary target에 적용한 결과가 포함되어야 한다.

필수 stable projection:

- candidate file digest
- applied row count
- full partition fingerprint
- required-column and schema validation result
- baseline/current incident analysis digest
- validated target-state digest
- dbt project node projection
- model and test statuses

Partition fingerprint는 duplicate를 보존하는 row multiset semantics를 사용한다. `ingested_at`, source path처럼 실행마다 바뀌는 provenance field는 제외하되 HMDA source columns는 모두 포함한다. Core six-column fingerprint만 사용한다면 `data identity`가 아니라 `core-column identity`라고 제한해야 한다.

- **Evidence** - ingestion은 source columns 전체를 Bronze에 적재하고 required contract에는 `county_code`도 포함한다. 기존 six-column proposal은 raw partition 전체 identity를 증명하지 못한다.
- **Implication** - MVP의 recovery oracle은 full-source identity를 기본으로 하고 exact normalization은 Design에서 확정해야 한다.

### F6. Target partition identity는 current loader contract와 일치해야 한다

현재 partition overwrite 범위는 `source_year`와 선택적인 `source_file` 조합이다. Approval과 candidate metadata가 연도만 표현하면 같은 연도의 여러 source file 중 무엇을 교체하는지 모호하다.

MVP는 다음 중 하나를 planning에서 명시해야 한다.

1. fixture가 연도당 정확히 하나의 source file만 가진다는 invariant를 둔다.
2. `source_file`을 candidate, approval, target-state digest와 recovery request에 포함한다.

Candidate digest 확인에는 file read가 필요하다. 따라서 fail-closed 순서는 다음과 같이 표현해야 한다.

```text
approval metadata validation
→ candidate read-only digest validation
→ exclusive target gate
→ target-state revalidation
→ mutation
```

- **Evidence** - `load_hmda_loans_partition()`은 `source_year`와 optional `source_file`로 replacement scope를 결정한다.
- **Implication** - “source read 전에 모든 검증”이 아니라 “target mutation 전에 metadata, candidate와 target-state 검증”이 정확한 contract다.

### F7. Research와 Planning의 책임을 분리해야 한다

Research는 MVP 선택, scope, safety requirement와 planning gate를 결정한다. Exact model fields, enum names, module layout, DuckDB copy method와 canonical hashing algorithm은 OpenSpec Proposal, Specs와 Design이 소유해야 한다.

Research가 확정하는 사항:

- `volume_drop` 단일 vertical slice
- candidate validation 후 approval
- 모든 mutation에 대한 approval binding
- single-writer stale-state protection
- mutation 이후 failure와 reconciliation
- full-source partition identity
- deterministic acceptance cases
- Foundation completion 전 Apply 차단

Planning으로 넘기는 사항:

- exact contract models와 ownership
- lock와 snapshot implementation
- stable projection serialization
- runner와 command surface
- artifact root와 atomic writer
- affected capability delta specs

- **Evidence** - `research/AGENTS.md`, `research/templates/research.md`, `openspec/schemas/spec-driven-tdd/`
- **Implication** - 이 Research를 구현 명세로 사용하지 않고 후속 Change의 decision input으로 사용해야 한다.

## Options

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| `volume_drop` recovery vertical slice | 기존 capability를 연결하며 detection, approval, mutation과 verification을 모두 증명 | approval binding, stale-state와 partial failure contract가 필요 |
| 여러 incident의 recovery 동시 구현 | coverage가 넓음 | incident별 remediation이 달라 MVP 범위와 oracle이 불명확해짐 |
| Dagster control-plane부터 구축 | 운영 흐름을 시각화하기 쉬움 | 핵심 domain contract보다 orchestration이 먼저 확장됨 |
| Detection과 report만 제공 | 가장 빠름 | Project Pivot의 승인된 recovery 가치를 증명하지 못함 |

`volume_drop` 단일 vertical slice를 선택한다. 다른 incident와 orchestration 확장은 이 slice가 검증된 뒤 별도 Change로 다룬다.

## Required Acceptance

| Case | Expected Result |
| --- | --- |
| Clean baseline | incident 없음, impact analysis 생략 |
| Controlled volume drop | 정확한 detection, downstream impact와 remediation draft |
| Candidate validation failure | approval과 recovery 진입 차단 |
| Mismatched candidate | candidate read 후 digest mismatch, target mutation 전 차단 |
| Stale target state | gate 획득 후 target digest mismatch, mutation 전 차단 |
| Unauthorized dbt mutation | required dbt action 또는 project binding이 없으면 recovery 차단 |
| Approved recovery | partition identity, incident resolution과 full dbt build 통과 |
| Post-mutation verification failure | `verification_failed` 기록, 성공으로 보고하지 않음 |
| Recovery reconciliation | 같은 run과 approval로 idempotent하게 검증 완료 |
| Repeated recovery | duplicate 증가와 semantic drift 없음 |
| Omitted-column corruption | full-source fingerprint mismatch로 실패 |
| Replay | volatile metadata를 제외한 canonical projection이 동일 |

## Conclusion

- **Answer** - Project Pivot의 첫 MVP는 versioned HMDA fixture에서 `volume_drop`을 재현하고, read-only analysis, isolated candidate validation, 모든 mutation에 결합된 human approval, approved recovery와 post-recovery verification을 하나의 run evidence로 연결하는 vertical slice다.
- **Recommendation** - 후속 OpenSpec Change는 `reliability-mvp-volume-drop-vertical-slice`로 제한한다. Approval binding, single-writer stale-state gate, mutation-aware state, reconciliation과 full-source identity를 필수 contract로 포함한다.
- **Next Step** - Proposal과 delta Specs를 작성할 수 있다. Apply는 Foundation readiness의 pipeline execution evidence와 completion decision이 닫히기 전까지 시작하지 않는다. Research의 accepted conclusion이 planning artifacts로 이전되면 이 파일은 `research/AGENTS.md` lifecycle에 따라 삭제한다.

## OpenSpec Direction

| Capability | Direction |
| --- | --- |
| `incident-lifecycle-runtime` | 변경하지 않고 read-only analysis result를 사용 |
| `approval-backfill-validation` | target, candidate, validation, dbt action과 stale-state binding 추가 |
| New `recovery-candidate-validation` | consistent target copy, temporary candidate apply와 full dbt build |
| New `reliability-recovery-run` | phase evidence, mutation-aware state, reconciliation과 replay |
| `evaluation-report` | 기존 detector/action evaluation 책임 유지 |

Out of scope:

- `null_spike`, `schema_drift`, `freshness_delay` end-to-end recovery
- Dagster control-plane job, schedule와 sensor
- approval UI와 external identity provider
- security-grade signature, RBAC와 append-only audit
- cloud deployment와 production SLO
- LLM 기반 RCA와 automatic remediation

## Evidence

| Evidence | Supports | Location |
| --- | --- | --- |
| Analysis와 risky mutation의 분리 | F1, F4 | `docs/ARCHITECTURE.md` |
| HMDA partition key와 full source ingestion | F5, F6 | `docs/domains/hmda-data.md` |
| Read-only lifecycle와 approved recovery boundary | F1, F4 | `docs/domains/reliability.md` |
| Current approval fields | F2 | `src/project_pivot/reliability/contracts/approval.py` |
| Current recovery gate와 execution | F2, F3 | `src/project_pivot/reliability/recovery/executor.py` |
| Partition transaction과 replacement scope | F3, F6 | `src/project_pivot/hmda_data/ingestion/partition.py` |
| Required HMDA source columns | F5 | `src/project_pivot/hmda_data/ingestion/_common.py` |
| dbt table materialization | F2 | `dbt/dbt_project.yml` |
| Current lifecycle requirements | F1 | `openspec/specs/incident-lifecycle-runtime/spec.md` |
| Current backfill requirements | F2, F4 | `openspec/specs/approval-backfill-validation/spec.md` |
| Foundation readiness remains separately gated | F7 | `docs/development/foundation/readiness.md` |

## Open Questions

| Question | Why It Matters | Next Step |
| --- | --- | --- |
| Exclusive local writer gate를 어떤 mechanism이 소유하는가? | stale-state check와 overwrite 사이 경쟁 조건을 닫아야 함 | Design에서 process lock과 DuckDB transaction boundary 결정 |
| Full-source fingerprint의 canonical normalization은 무엇인가? | type, null, duplicate와 ordering에 독립적인 oracle 필요 | Spec scenario와 property test로 확정 |
| Reconciliation runner가 partition overwrite를 언제 생략하는가? | mutation 이후 재실행이 안전하고 idempotent해야 함 | `partition_replaced` evidence와 fingerprint 조건 설계 |
| Run artifact root와 retention은 어디서 설정하는가? | Research가 새 global path를 고정하면 안 됨 | 기존 project configuration과 artifact policy 확인 |
