---
type: research
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
> Project Pivot의 첫 MVP는 `volume_drop` 하나를 detection부터 승인된 recovery와 재검증까지 연결하는 vertical slice로 제한한다. Foundation readiness는 현재 `GO`이므로 별도 phase gate로 MVP Apply를 막지 않는다. 대신 candidate-bound approval, stale-state 차단, mutation 이후 reconciliation, full-source identity와 dbt artifact 보존을 후속 OpenSpec의 필수 safety contract로 넘긴다.

## Question

현재 architecture boundary를 유지하면서 Project Pivot의 핵심 가치를 가장 작고 안전하게 증명할 MVP는 무엇인가?

### Scope

- 첫 `volume_drop` incident의 detection, impact, candidate validation, human approval, recovery, failure handling과 post-recovery verification
- 여러 incident 유형, Dagster control-plane, 운영 UI, cloud deployment, security-grade authorization은 제외

### Stop Condition

- 하나의 vertical slice와 필수 safety contract를 결정한다.
- acceptance case와 OpenSpec planning 방향을 현재 repository evidence에 연결한다.
- 세부 구현 선택은 Planning/Design으로 넘긴다.

## Findings

### F1. `volume_drop`이 첫 recovery vertical slice에 가장 적합하다

현재 repository는 Foundation data path에 더해 partition overwrite, read-only incident lifecycle, dbt impact analysis와 approval-gated recovery를 분리된 capability로 제공한다. `volume_drop`은 deterministic row removal과 명확한 row-count oracle을 사용하므로 이 capability들을 하나의 recovery 흐름으로 연결하기에 가장 작다.

```text
clean fixture
→ controlled volume_drop
→ Bronze + dbt pipeline
→ read-only incident lifecycle
→ isolated candidate validation
→ candidate-bound human approval
→ approved recovery
→ incident + data + dbt verification
→ run evidence
```

- **Evidence** - `docs/ARCHITECTURE.md`, `docs/domains/reliability.md`, `src/project_pivot/data_operations/incident_lifecycle.py`
- **Implication** - 첫 MVP는 detector 확장보다 기존 capability 사이의 안전한 handoff와 recovery 증명에 집중한다.

### F2. Foundation은 MVP 진입을 더 이상 차단하지 않는다

Canonical Foundation readiness는 2026-08-08 snapshot에서 `GO`, implementation `147/147`, verification `111/111`, blocker 없음으로 판정되어 있다. Audited revision 이후 current `main`까지의 변경은 readiness, VCS/inbox 문서와 inbox artifact에 한정되며 source/spec/test 변경은 없다.

- **Evidence** - `docs/development/foundation/readiness.md`, audited revision `feea63fe5945c353f2f9b70b57a29cbe7294dafa` → current `main` compare
- **Implication** - 후속 OpenSpec Planning과 Apply는 Foundation completion을 다시 기다리지 않는다. 새 MVP Change 자체의 specification, design, task와 validation gate만 충족하면 된다.

Foundation의 non-gating inventory는 MVP 설계 입력으로 사용한다. 특히 `dbt last-known-good evidence retention` 위험은 이 vertical slice가 직접 다뤄야 한다.

### F3. Approval은 실제로 수행되는 모든 mutation에 결합되어야 한다

현재 approval은 실행 대상 binding 관점에서 `incident_id`와 requested actions만 가지며 target, candidate, validation state와 dbt execution identity를 고정하지 않는다. Recovery executor도 `overwrite_partition`, `rerun_profile_snapshot`만 요구한다. MVP가 실제 target에서 `dbt build`까지 수행하면 marts table materialization도 승인 대상 mutation이다.

후속 contract는 최소한 다음 stable identity를 approval에 결합해야 한다.

| Binding | Purpose |
| --- | --- |
| run + incident | 다른 incident에 approval 재사용 차단 |
| analysis digest | 승인한 evidence 고정 |
| target asset + full partition key | 다른 target mutation 차단 |
| candidate digest | 다른 recovery input 사용 차단 |
| candidate validation digest | 검증되지 않은 candidate 실행 차단 |
| validated target-state digest | validation 이후 target 변경 감지 |
| dbt project/config projection + target | 다른 dbt graph 또는 target 실행 차단 |
| approved actions | partition, profile, dbt mutation 범위 명시 |

MVP action semantics에는 최소한 다음이 필요하다.

```text
overwrite_partition
rerun_profile_snapshot
rebuild_dbt_models
```

- **Evidence** - `src/project_pivot/reliability/contracts/approval.py`, `src/project_pivot/reliability/recovery/executor.py`, `dbt/dbt_project.yml`
- **Implication** - `dbt build`를 단순 verification으로 취급하지 않는다. 실제 mutation이면 승인된 recovery action으로 표현한다.

### F4. Stale approval은 짧은 writer gate와 target-state 재검증으로 차단한다

현재 partition replacement 자체는 DuckDB transaction으로 원자적이지만 approval freshness는 검증하지 않는다. MVP는 local single-writer system으로 제한하고 다음 behavioral boundary를 요구한다.

```text
candidate snapshot:
writer gate
→ consistent target snapshot + target-state digest
→ release gate

candidate validation:
isolated snapshot
→ candidate apply
→ isolated dbt build
→ validation digest

approved recovery:
writer gate
→ target-state digest recheck
→ partition overwrite transaction
→ release gate
→ approved downstream verification/rebuild
```

Gate는 consistent snapshot/digest를 얻거나 target mutation을 수행하는 동안만 유지한다. Candidate의 full dbt validation 동안 target writer를 막지 않는다.

- **Evidence** - `src/project_pivot/hmda_data/ingestion/partition.py`
- **Implication** - target-state mismatch나 gate 획득 실패가 있으면 target mutation 전에 중단하고 candidate validation부터 다시 수행한다.

### F5. Candidate validation은 적용 결과와 full partition identity를 검증해야 한다

Candidate file digest만으로는 ingestion contract를 통과한 결과 rows를 증명하지 못한다. Validation digest는 최소한 다음 stable projection을 포함해야 한다.

- candidate digest
- applied row count
- expected recovered partition fingerprint
- required-column/schema validation result
- analysis digest
- validated target-state digest
- dbt project/config projection
- model/test result projection

Partition fingerprint는 duplicate를 보존하는 row multiset semantics를 사용한다. `ingested_at`이나 absolute source path처럼 실행마다 달라질 수 있는 provenance는 제외하되, partition identity에 사용되는 `source_year`와 optional `source_file`은 보존한다. Exact canonical normalization은 Design과 property test에서 확정한다.

현재 overwrite scope는 `source_year`와 optional `source_file` 조합이므로 approval, candidate metadata, target-state와 recovery request도 같은 partition identity를 표현해야 한다.

- **Evidence** - `src/project_pivot/hmda_data/ingestion/partition.py`
- **Implication** - recovery oracle은 일부 profile column이 아니라 실제 replacement 대상 partition의 identity를 검증한다.

### F6. Candidate와 recovery dbt 실행은 current shared artifact를 파괴하면 안 된다

현재 `run_dbt_build()`는 실행 전에 configured `manifest.json`과 `run_results.json`을 삭제하며, `DataOperationRequest`의 기본 경로는 공유 `dbt/target`이다. 따라서 isolated candidate validation이 같은 경로를 사용하면 기존 impact evidence를 지우거나 candidate artifact로 교체할 수 있다. Recovery build 실패도 동일하게 last-known-good evidence를 잃을 수 있다.

MVP contract는 다음을 보장해야 한다.

- candidate validation은 run-scoped artifact workspace를 사용하고 current shared dbt artifacts를 변경하지 않는다.
- recovery build가 실패해도 이전 last-known-good shared artifacts를 유지한다.
- failed build가 생성한 artifact가 있으면 run-scoped evidence로 보존하고, artifact가 없어도 command/result/error evidence를 남긴다.
- 성공한 build만 검증 후 새로운 current artifact projection으로 승격한다.
- approval과 run evidence는 validation/recovery 판단에 사용한 artifact projection을 식별한다.

Exact path, promotion mechanism과 retention 기간은 Design이 결정한다.

- **Evidence** - `src/project_pivot/data_operations/runner.py`, `src/project_pivot/data_operations/request.py`, `docs/development/foundation/readiness.md`
- **Implication** - dbt artifact safety는 운영 편의가 아니라 replay, reconciliation과 approval evidence의 정확성을 위한 MVP correctness contract다.

### F7. Mutation 이후 실패는 pre-mutation failure와 구분하고 재조정 가능해야 한다

Partition commit 이후 profile, dbt rebuild 또는 final verification이 실패할 수 있다. dbt build 역시 일부 materialization을 수행한 뒤 실패할 수 있으므로 cross-system rollback을 약속하지 않는다.

필수 semantics:

```text
analyzed
→ validated
→ approved
→ recovery_started
→ partition_replaced
→ verified

validated → rejected
before target mutation → failed
partition_replaced → verification_failed
verification_failed → reconciled | verified
```

Exact enum은 Planning/Design에서 정한다. Behavioral contract는 다음만 고정한다.

- target mutation이 시작됐는지 evidence로 구분한다.
- partition commit 이후 failure를 성공으로 보고하지 않는다.
- reconciliation은 writer gate 아래에서 current target fingerprint를 다시 확인한다.
- current partition이 expected recovered fingerprint와 같으면 overwrite를 생략하고 profile/dbt verification만 재실행한다.
- current partition이 approval에 결합된 pre-recovery target state와도 expected recovered state와도 다르면 old approval로 mutation하지 않고 candidate validation과 approval을 새로 요구한다.
- failed dbt run evidence와 last-known-good artifact를 함께 보존한다.

- **Evidence** - `docs/ARCHITECTURE.md`, `dbt/dbt_project.yml`, `src/project_pivot/data_operations/runner.py`
- **Implication** - reconciliation은 replay convenience가 아니라 stale approval 규칙을 그대로 유지하는 recovery continuation이어야 한다.

### F8. Research는 behavioral decision만 고정하고 세부 구현은 Planning으로 넘긴다

Research가 확정하는 사항:

- `volume_drop` 단일 vertical slice
- candidate validation 후 approval
- 모든 target mutation의 approval binding
- short-lived writer gate + stale-state revalidation
- full-source partition identity
- dbt artifact isolation/last-known-good preservation
- mutation-aware failure와 reconciliation
- deterministic acceptance cases

Planning/Design이 결정할 사항:

- exact contract models와 enum
- lock/snapshot 구현
- stable projection serialization과 hashing
- dbt artifact workspace와 promotion mechanism
- runner/command surface
- run evidence storage와 retention
- affected capability delta specs

현재 active `data-operations-refactor-runner` Change는 같은 runner 파일을 다루지만 public behavior를 바꾸지 않는 refactor이며 tasks는 `4/4`다. MVP가 runner contract를 변경하기 전 이 Change를 archive하거나 명확히 sequencing해야 한다. 이것은 MVP entry blocker가 아니라 overlapping active change 관리 문제다.

- **Evidence** - `research/AGENTS.md`, `inbox/_templates/research.md`, `openspec/changes/data-operations-refactor-runner/proposal.md`, `openspec/changes/data-operations-refactor-runner/tasks.md`
- **Implication** - 이 Research를 구현 명세로 확대하지 않고 후속 OpenSpec Change의 decision input으로 사용한다.

## Options

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| `volume_drop` recovery vertical slice | 기존 capability를 연결하며 detection, approval, mutation, verification을 모두 증명 | approval/stale-state/artifact safety 계약 필요 |
| 여러 incident recovery 동시 구현 | coverage가 넓음 | incident별 oracle과 remediation 차이로 MVP 범위 확대 |
| Dagster control-plane 우선 | 실행 흐름 가시화 | 핵심 reliability contract보다 orchestration이 먼저 확장 |
| Detection + report만 제공 | 가장 작음 | 승인된 recovery라는 프로젝트 가치를 증명하지 못함 |

`volume_drop` 단일 vertical slice를 선택한다. 다른 incident와 orchestration은 이 slice가 검증된 뒤 별도 Change로 다룬다.

## Required Acceptance

| Case | Expected Result |
| --- | --- |
| Clean baseline | incident 없음, impact/remediation analysis 없음 |
| Controlled volume drop | 정확한 detection, downstream impact와 remediation draft |
| Candidate validation failure | approval과 recovery 진입 차단 |
| Mismatched candidate | candidate digest mismatch, target mutation 전 차단 |
| Stale target state | writer gate 안에서 digest mismatch, target mutation 전 차단 |
| Unauthorized dbt mutation | required dbt action 또는 project/config binding이 없으면 recovery 차단 |
| Candidate dbt failure | target database와 current shared dbt artifacts 변경 없음, failed-run evidence 보존 |
| Approved recovery | partition identity, incident resolution, profile과 full dbt build 검증 통과 |
| Recovery dbt failure | `verification_failed`, prior last-known-good shared artifact 유지 |
| Recovery reconciliation | expected recovered fingerprint면 overwrite 없이 verification 재실행 |
| Diverged reconciliation target | old approval mutation 차단, 새 validation/approval 요구 |
| Repeated recovery | duplicate 증가와 semantic drift 없음 |
| Omitted-column corruption | full-source fingerprint mismatch로 실패 |
| Replay | volatile metadata를 제외한 stable projection이 동일 |

## Conclusion

Project Pivot의 첫 MVP는 versioned HMDA fixture에서 `volume_drop`을 재현하고, read-only analysis, isolated candidate validation, candidate-bound human approval, approved recovery와 post-recovery verification을 하나의 run evidence로 연결하는 vertical slice다.

Foundation readiness는 이미 `GO`이므로 후속 OpenSpec Planning을 시작하고 해당 Change의 자체 gate가 충족되면 Apply로 진행할 수 있다. OpenSpec은 approval binding, stale-state protection, full partition identity, dbt artifact safety와 mutation-aware reconciliation을 필수 contract로 포함해야 한다.

### Next Step

1. `data-operations-refactor-runner`의 archive/sequencing 상태를 정리한다.
1. `reliability-mvp-volume-drop-vertical-slice` OpenSpec Change에 accepted decision을 이전한다.
1. Planning artifact가 이 결론을 소유하면 `research/AGENTS.md` lifecycle에 따라 이 Research를 삭제한다.

## OpenSpec Direction

| Capability | Direction |
| --- | --- |
| `incident-lifecycle-runtime` | read-only analysis boundary 유지 |
| `approval-backfill-validation` | target/candidate/validation/dbt action/stale-state binding 확장 |
| New `recovery-candidate-validation` | isolated target snapshot, candidate apply, isolated full dbt build |
| New `reliability-recovery-run` | phase evidence, approved mutations, artifact promotion, reconciliation/replay |
| `pipeline-stage-runtime` | dbt stage가 run-scoped artifact output과 last-known-good 보존을 지원하도록 필요 시 확장 |
| `evaluation-report` | 기존 detector/action evaluation 책임 유지 |

Out of scope:

- `null_spike`, `schema_drift`, `freshness_delay` end-to-end recovery
- Dagster control-plane job, schedule, sensor
- approval UI와 external identity provider
- security-grade signature, RBAC, append-only audit
- cloud deployment와 production SLO
- LLM 기반 RCA와 automatic remediation

## Evidence

| Evidence | Supports | Location |
| --- | --- | --- |
| Analysis와 risky mutation 분리 | F1, F7 | `docs/ARCHITECTURE.md` |
| Read-only lifecycle와 approved recovery boundary | F1, F3 | `docs/domains/reliability.md` |
| Clean/incident lifecycle behavior | F1 | `src/project_pivot/data_operations/incident_lifecycle.py` |
| Foundation `GO`와 non-gating risk | F2, F6 | `docs/development/foundation/readiness.md` |
| Current approval fields | F3 | `src/project_pivot/reliability/contracts/approval.py` |
| Current recovery action gate | F3 | `src/project_pivot/reliability/recovery/executor.py` |
| Partition transaction와 replacement scope | F4, F5 | `src/project_pivot/hmda_data/ingestion/partition.py` |
| dbt table materialization | F3, F7 | `dbt/dbt_project.yml` |
| dbt pre-build artifact deletion | F6, F7 | `src/project_pivot/data_operations/runner.py` |
| Shared default dbt artifact paths | F6 | `src/project_pivot/data_operations/request.py` |
| Canonical dbt stage contract | F6 | `openspec/specs/pipeline-stage-runtime/spec.md` |
| Research lifecycle/template | F8 | `research/AGENTS.md`, `inbox/_templates/research.md` |
| Active runner refactor scope/status | F8 | `openspec/changes/data-operations-refactor-runner/` |

## Open Questions

| Question | Why It Matters | Next Step |
| --- | --- | --- |
| Local writer gate의 owner와 mechanism은 무엇인가? | snapshot과 overwrite 사이 경쟁 조건을 닫아야 함 | Design에서 process lock + DuckDB boundary 결정 |
| Full-source fingerprint normalization은 무엇인가? | type/null/duplicate/order에 독립적인 oracle 필요 | Spec scenario + property test로 확정 |
| dbt run workspace와 current artifact promotion은 어떻게 분리하는가? | failed build가 prior evidence를 파괴하면 안 됨 | Design에서 path/promotion/retention 결정 |
| Active runner refactor는 언제 archive하는가? | 동일 runner의 overlapping Change를 피해야 함 | MVP Change 생성 전 lifecycle 정리 |