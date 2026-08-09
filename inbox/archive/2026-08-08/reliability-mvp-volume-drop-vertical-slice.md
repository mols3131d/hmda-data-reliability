---
type: research
title: Reliability MVP Volume-Drop Vertical Slice
description: Foundation 이후 volume_drop 단일 recovery vertical slice의 범위, 안전 계약과 OpenSpec planning 진입 조건을 최신 main 기준으로 결정한다.
status: completed
tags:
  - reliability
  - mvp
  - recovery
  - volume-drop
---

> [!NOTE]
> 첫 MVP는 `volume_drop` 하나를 detection부터 승인된 recovery와 재검증까지 연결하는 vertical slice로 제한한다. Foundation의 phase decision은 `GO`지만 current `main`에는 audited revision 이후 runtime 변경이 있으므로 Planning은 즉시 시작하고, Apply 전에는 MVP 관련 baseline을 current `main`에서 다시 검증한다. MVP의 필수 safety behavior는 exact recovery proposal에 결합된 approval, mutation 직전 target-state 재검증, content-level partition identity, dbt artifact 격리와 last-known-good 보존, mutation 이후 failure/reconciliation이다.

## Question

현재 architecture boundary를 유지하면서 Project Pivot의 핵심 가치를 가장 작고 안전하게 증명할 첫 MVP는 무엇이며, OpenSpec Planning 전에 어떤 behavior를 고정해야 하는가?

### Scope

- `volume_drop` incident의 detection, impact, candidate validation, human approval, recovery, failure handling과 post-recovery verification
- current `main`의 Foundation readiness, recovery, ingestion, dbt execution과 active OpenSpec Change 상태
- 여러 incident 유형, Dagster control-plane, 운영 UI, cloud deployment, security-grade authorization은 제외

### Stop Condition

- 하나의 vertical slice를 선택한다.
- MVP에 필요한 safety behavior와 Design 선택을 분리한다.
- acceptance case를 current repository evidence에 연결한다.
- 오래된 repository-state 전제를 제거한다.

## Findings

### F1. `volume_drop` 단일 recovery slice가 첫 MVP에 가장 적합하다

현재 architecture는 read-only incident lifecycle과 승인된 recovery를 분리한다. `volume_drop`은 baseline/current row count로 결정론적으로 탐지할 수 있고 기존 partition overwrite, impact analysis, remediation draft를 하나의 end-to-end 흐름으로 연결하기 쉽다.

```text
clean fixture
→ controlled volume_drop
→ Bronze + dbt
→ read-only incident lifecycle
→ isolated candidate validation
→ bound human approval
→ approved recovery
→ data + incident + dbt verification
→ run evidence
```

- **Evidence** - `docs/ARCHITECTURE.md`, `docs/domains/reliability.md`, `openspec/specs/reliability-incident-detection/spec.md`
- **Implication** - 첫 MVP는 detector 종류를 늘리지 않고 기존 capability 사이의 안전한 handoff와 recovery 증명에 집중한다.

### F2. Foundation은 Planning을 막지 않지만 current-main validation freshness는 별도 gate다

Canonical Foundation readiness는 2026-08-08 snapshot에서 `GO`, implementation `147/147`, verification `111/111`, blocker 없음으로 판정했다. 그러나 current `main` head `587eb64f1b5a1c49a17532823561cd50ce8d12ba`에는 audited revision 이후 runtime, ingestion, dbt configuration 관련 변경이 포함된다.

최근 hardcoding RPI 작업은 cross-domain regression `67 passed`, HMDA ingestion/EDA suite `36 passed`를 기록하지만 Foundation focused suite 전체를 current `main`에서 재실행한 evidence는 아니다.

따라서 gate를 다음처럼 분리한다.

| Gate | Decision |
| --- | --- |
| MVP Planning 진입 | **GO** |
| MVP Apply 진입 | current `main`에서 MVP 관련 baseline 재검증 필요 |
| MVP acceptance | 새 Change가 정의한 end-to-end acceptance 통과 필요 |

- **Evidence** - `docs/development/foundation/readiness.md`, commit `587eb64f1b5a1c49a17532823561cd50ce8d12ba`
- **Implication** - Foundation을 다시 설계하지는 않지만 과거 audited result를 current runtime result로 간주하지 않는다.

Foundation non-gating risk 중 `dbt last-known-good evidence retention`은 이 slice가 직접 사용하므로 MVP 범위에 들어온다. Dagster dbt skip/materialization semantics는 Dagster control-plane을 제외하는 한 이 MVP의 blocker가 아니다.

### F3. Approval은 incident가 아니라 exact recovery proposal에 결합되어야 한다

현재 `Approval`은 `incident_id`와 `requested_actions`를 보유하고, recovery executor는 `overwrite_partition`과 `rerun_profile_snapshot` action 존재만 확인한다. 승인 이후 target, candidate 또는 validation evidence가 바뀌어도 이를 식별할 binding이 없다.

MVP는 최소한 다음 의미를 보장해야 한다.

- approval은 실행할 incident와 target partition을 식별한다.
- approval은 검증된 candidate와 그 validation evidence를 식별한다.
- approval은 검증 당시 target state와 실제 target mutation action을 식별한다.
- target에서 dbt materialization을 다시 수행한다면 해당 mutation도 approval 범위에 포함한다.
- candidate validation처럼 격리 환경에서만 일어나는 mutation은 target approval 대상과 구분한다.

Exact field, digest 구조와 action enum은 Planning/Design이 결정한다.

- **Evidence** - `src/project_pivot/reliability/contracts/approval.py`, `src/project_pivot/reliability/recovery/executor.py`
- **Implication** - 승인된 evidence와 실제 실행 대상이 달라지면 target mutation 전에 실패해야 한다.

### F4. Stale approval 방지는 lock 방식이 아니라 observable behavior로 고정한다

현재 partition overwrite의 delete/insert는 DuckDB transaction으로 원자적이지만 approval freshness를 검증하지 않는다. MVP는 local single-writer 범위에서 다음 behavior만 요구한다.

1. candidate는 current target과 분리된 환경에서 검증한다.
1. approval은 candidate validation 당시의 target state를 식별한다.
1. 첫 target mutation 직전에 같은 target state인지 다시 확인한다.
1. target이 바뀌었으면 mutation 전에 중단하고 candidate validation과 approval을 새로 요구한다.
1. target-state 확인과 첫 mutation 사이에는 concurrent writer가 끼어들 수 없는 경계를 제공한다.

lock, transaction, file lock 또는 다른 serialization 방식은 Design 선택이다.

- **Evidence** - `src/project_pivot/hmda_data/ingestion/partition.py`
- **Implication** - Research가 특정 writer-gate 구현을 선결하지 않으면서 stale approval을 차단한다.

### F5. Recovery oracle은 row count가 아니라 partition content identity를 검증해야 한다

현재 recovery success path는 overwrite row count와 profile snapshot row count의 일치를 validation 결과로 사용한다. Canonical Spec도 `source_file` scoped row-count comparison을 file-level population equivalence로 해석해서는 안 된다고 명시한다. 같은 row count이지만 내용이 다른 candidate는 이 oracle만으로 검출할 수 없다.

MVP의 recovery oracle은 다음을 보장해야 한다.

- target scope는 `table + source_year + optional source_file`과 일치한다.
- expected recovered state와 actual target partition의 stable content가 동일해야 한다.
- duplicate row를 보존하는 semantics를 사용한다.
- 실행마다 달라지는 metadata는 content identity에서 제외할 수 있다.
- exact canonicalization과 hashing은 Design/property test에서 결정한다.

- **Evidence** - `src/project_pivot/reliability/recovery/executor.py`, `tests/reliability/test_approval_backfill_validation.py`, `openspec/specs/reliability-recovery-backfill/spec.md`, `src/project_pivot/hmda_data/ingestion/partition.py`
- **Implication** - row-count validation은 보조 evidence로 유지할 수 있지만 MVP recovery correctness의 최종 oracle이 될 수 없다.

### F6. Candidate와 recovery dbt 실행은 current artifact를 파괴하면 안 된다

현재 `run_dbt_build()`는 dbt 실행 전에 configured `manifest.json`과 `run_results.json`을 삭제한다. 따라서 candidate validation이나 실패한 recovery build가 shared artifact path를 사용하면 이전 정상 evidence를 잃을 수 있다.

MVP는 다음 behavior를 요구한다.

- candidate dbt validation은 current target database와 shared current artifact를 변경하지 않는다.
- failed target dbt build는 prior last-known-good artifact를 제거하거나 current success로 승격하지 않는다.
- failed run의 command/result/error와 생성된 artifact가 있으면 run evidence로 식별할 수 있다.
- 성공하고 검증된 target build만 current artifact projection을 교체한다.
- impact, approval과 recovery evidence는 판단에 사용한 dbt artifact projection을 식별한다.

workspace path, artifact promotion mechanism과 retention 기간은 Design이 결정한다.

- **Evidence** - `src/project_pivot/data_operations/runner.py`, `openspec/specs/data-operations-stage-execution/spec.md`
- **Implication** - dbt artifact retention은 운영 편의가 아니라 recovery correctness와 replay 가능성의 일부다.

### F7. Partition commit 이후 failure는 별도 상태로 관찰되고 reconciliation 가능해야 한다

Partition commit 이후 profile 또는 dbt verification이 실패할 수 있고, dbt build 역시 일부 materialization 이후 실패할 수 있다. 여러 시스템에 걸친 rollback을 MVP 계약으로 약속하지 않는다.

MVP는 최소한 다음 상태 차이를 관찰 가능하게 해야 한다.

```text
before target mutation
→ target mutation started
→ partition changed
→ downstream verification passed | failed
```

Reconciliation behavior:

- current partition이 expected recovered state와 같으면 partition overwrite를 반복하지 않고 downstream verification을 재개할 수 있다.
- current partition이 approved pre-recovery state와 expected recovered state 어느 쪽과도 다르면 기존 approval로 추가 mutation하지 않는다.
- post-mutation failure를 성공으로 보고하지 않는다.
- failed dbt evidence와 prior last-known-good artifact를 함께 보존한다.

Exact enum과 run-state model은 Planning/Design이 결정한다.

- **Evidence** - `src/project_pivot/hmda_data/ingestion/partition.py`, `src/project_pivot/data_operations/runner.py`
- **Implication** - recovery retry는 무조건 replay가 아니라 현재 state를 다시 확인하는 reconciliation이다.

### F8. 현재 active OpenSpec Change는 Planning blocker가 아니지만 Apply 전에 sequencing이 필요하다

`data-operations-refactor-runner`는 더 이상 active Change가 아니다. Current `main`에는 다음 완료된 hardcoding 관련 Change가 active 상태로 남아 있다.

- `data-operations-centralize-runtime-settings`
- `data-platform-require-database-path`
- `hmda-data-align-ingestion-contracts`
- `orchestration-consume-runtime-settings`

이들은 구현과 focused validation이 완료됐지만 아직 archive되지 않았다. MVP는 `data-operations`, `data-platform`, `hmda-data` 경계를 다시 건드릴 가능성이 있으므로 Planning은 시작할 수 있지만 Apply 전에는 relevant Change를 archive/sync하거나 delta overlap이 없음을 명시해야 한다.

- **Evidence** - `openspec/changes/`, commit `587eb64f1b5a1c49a17532823561cd50ce8d12ba`
- **Implication** - 오래된 Change 이름을 blocker로 남기지 않고 실제 active work와 sequencing한다.

### F9. Research는 behavior만 고정하고 구현·capability 분해는 Planning에 넘긴다

Research가 확정하는 사항:

- `volume_drop` 단일 vertical slice
- isolated candidate validation 후 approval
- exact recovery proposal과 target state에 결합된 approval
- mutation 직전 stale-state 재검증
- content-level partition recovery oracle
- dbt artifact isolation과 last-known-good 보존
- mutation-aware failure와 reconciliation
- deterministic end-to-end acceptance

Planning/Design이 결정할 사항:

- contract model과 enum
- serialization/locking 방식
- fingerprint canonicalization과 hashing
- dbt workspace와 artifact promotion
- runner/command surface
- run evidence 저장 방식과 retention
- 기존 capability delta와 새 capability 분해

- **Evidence** - `inbox/_guidelines/research.md`, `inbox/_templates/research.md`
- **Implication** - 이 문서는 구현 명세가 아니라 OpenSpec Planning의 decision input으로 유지한다.

## Options

| Option | Value | Decision |
| --- | --- | --- |
| `volume_drop` recovery vertical slice | 기존 detection→approval→recovery를 가장 작은 end-to-end value로 연결 | **Select** |
| 여러 incident recovery 동시 구현 | coverage는 넓지만 oracle과 remediation 차이로 범위 확대 | Reject |
| Dagster control-plane 우선 | 실행 가시성은 높지만 핵심 reliability contract보다 orchestration이 앞섬 | Defer |
| Detection + report only | 작지만 승인된 recovery라는 프로젝트 핵심 가치를 증명하지 못함 | Reject |

## Required Acceptance

| Case | Expected Result |
| --- | --- |
| Clean baseline | incident와 remediation draft가 생성되지 않는다. |
| Controlled volume drop | 예상한 `volume_drop` incident, downstream impact와 remediation draft를 생성한다. |
| Invalid candidate | content-level expected state를 만족하지 못하면 approval/recovery 진입을 차단한다. |
| Stale target | approval 이후 target state가 바뀌면 첫 target mutation 전에 차단한다. |
| Incomplete approval | target mutation action 또는 required evidence binding이 없으면 recovery를 차단한다. |
| Candidate dbt failure | current target database와 shared current artifact가 변하지 않고 failed-run evidence가 남는다. |
| Approved recovery | partition content가 expected recovered state와 일치하고 incident가 해소되며 downstream dbt verification이 통과한다. |
| Recovery dbt failure | post-mutation failure가 관찰되고 prior last-known-good artifact가 유지된다. |
| Reconciliation | 이미 expected recovered state이면 partition overwrite를 반복하지 않고 downstream verification을 재개한다. |
| Diverged reconciliation | current state가 approved before/after state 어느 쪽과도 다르면 새 validation과 approval을 요구한다. |
| Replay | repeated recovery가 duplicate 또는 semantic drift를 만들지 않고 stable evidence projection은 재현 가능하다. |

## Conclusion

Project Pivot의 첫 MVP는 versioned HMDA fixture에서 `volume_drop`을 재현하고 read-only analysis, isolated candidate validation, bound human approval, approved recovery와 post-recovery verification을 하나의 evidence-backed vertical slice로 연결한다.

**Planning은 지금 시작해도 된다.** 다만 current `main`은 Foundation audited revision 이후 runtime 변경이 있으므로 Apply 전에 MVP 관련 baseline을 재검증하고, 완료됐지만 active 상태인 관련 OpenSpec Change를 sequencing해야 한다. MVP Change는 approval binding, stale-state protection, content-level recovery oracle, dbt artifact safety와 mutation-aware reconciliation을 필수 behavior로 가져가되 구현 방식은 Design이 소유한다.

### Next Step

1. `reliability-mvp-volume-drop-vertical-slice` OpenSpec Change를 생성한다.
1. 이 Research의 accepted behavior와 Required Acceptance만 Proposal/Spec/Design/Tasks로 이전한다.
1. Apply 전에 current `main`에서 MVP 관련 baseline을 재검증하고 overlapping active Change를 archive/sync 또는 명시적으로 sequence한다.
1. OpenSpec artifact가 normative contract를 소유한 뒤 이 문서는 archived evidence로만 사용한다.

## OpenSpec Direction

| Canonical capability | MVP direction |
| --- | --- |
| `data-operations-incident-lifecycle` | read-only analysis boundary 유지 |
| `reliability-recovery-backfill` | approval binding, stale-state 차단, content-level post-recovery validation 확장 검토 |
| `data-operations-stage-execution` | isolated dbt execution과 last-known-good artifact preservation delta 검토 |
| `hmda-data-ingestion` | atomic partition overwrite semantics 유지; fingerprint 책임은 Planning에서 소유권 결정 |
| `reliability-evaluation-report` | end-to-end synthetic acceptance를 기존 evaluation 책임과 연결할지 Planning에서 결정 |
| New capability | candidate validation 또는 recovery run이 독립 계약을 필요로 할 때만 추가 |

Out of scope:

- `null_spike`, `schema_drift`, `freshness_delay` end-to-end recovery
- Dagster control-plane job, schedule, sensor
- approval UI와 external identity provider
- security-grade signature, RBAC, append-only audit

## Open Questions

| Question | Owner |
| --- | --- |
| Stable partition fingerprint의 canonical projection은 무엇인가? | Design + property tests |
| Candidate/target dbt workspace와 current artifact promotion을 어떻게 분리할 것인가? | Design |
| Target-state recheck와 mutation을 어떤 serialization primitive로 묶을 것인가? | Design |
