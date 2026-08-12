---
type: openspec-spec-driven-tdd-design
category: design
title: Reliability Null-Spike Recovery Vertical Slice Design
description: 기존 approved partition recovery를 유지하고 null-rate acceptance를 incident-specific evaluation에 배치한다.
tags:
  - "domain:reliability"
  - "capability:reliability-recovery-backfill"
  - "capability:reliability-evaluation-report"
  - "null-spike"
---

> [!NOTE]
> `evaluate_null_spike_vertical_slice()`가 controlled single-column defect, read-only lifecycle, candidate dbt validation, exact approval, 기존 recovery executor, replay와 target dbt verification을 조합한다. Recovery executor는 stable content identity를 계속 소유하고, evaluator가 baseline 대비 target column null-rate와 post-recovery incident 해소를 별도로 판정한다.

## Context

- **Current State:** `null_spike` synthetic, detector와 remediation draft는 구현되어 있다. Approved recovery는 incident type과 무관한 full-partition compare-and-replace와 content identity validation을 제공하지만 end-to-end evaluation은 `volume_drop`만 존재한다.
- **Constraints:** Incident lifecycle은 read-only이고 recovery와 evaluation은 별도 API다. Evaluation target은 caller의 existing database가 아닌 새 disposable database여야 한다. 새 mutation type, generic vertical-slice framework, approval UI와 Dagster control-plane을 추가하지 않는다.
- **Dependencies:** Stable partition content identity, exact recovery proposal, candidate/target dbt isolation, mutation-aware recovery result와 recovery safety case adapter를 재사용한다. Current Specs는 선행 volume-drop Change의 archive delta와 동기화되어야 한다. Candidate/target dbt callback은 기존 evaluator와 동일한 trusted caller boundary이며 structured attestation 확장은 별도 Change다.

## Goals / Non-Goals

| Goals | Non-Goals |
| --- | --- |
| Controlled single-column `null_spike`를 결정론적으로 재현한다. | Multi-column incident를 하나의 proposal에 묶는다. |
| Clean candidate를 기존 approved partition backfill로 적용한다. | Column-level partial repair API를 추가한다. |
| Content identity와 null-rate/incident-resolution oracle을 분리한다. | Recovery `validation_passed` semantics를 변경한다. |
| Replay와 pre/post-mutation failure evidence를 보존한다. | 모든 volume-drop helper를 공통 framework로 추출한다. |
| Candidate와 target dbt verification을 포함한다. | Remediation draft의 backfill recommendation을 변경한다. |

## Architecture

새 `reliability.evaluation.null_spike` module은 `volume_drop` evaluator와 같은 application composition pattern을 사용하되 defect parameters, incident selection과 acceptance만 `null_spike` 의미에 맞게 소유한다. Recovery package와 contracts에는 새 incident branch를 추가하지 않는다.

### Components

| Component | Responsibility | Change |
| --- | --- | --- |
| `hmda_data.null_spike` | Target column의 deterministic null injection | Existing API를 `sample_fraction=1.0`으로 사용한다. |
| `run_incident_lifecycle` | Baseline/current profile 비교, detection, impact와 draft | Existing read-only API를 그대로 사용한다. |
| `reliability.evaluation.null_spike` | End-to-end composition과 null-rate acceptance | New incident-specific evaluator와 result model을 추가한다. |
| `RecoveryProposal` / `execute_approved_backfill` | Exact approval gate, partition mutation과 content validation | Existing contracts와 executor를 변경 없이 재사용한다. |
| `build_recovery_evaluation_case` | Failure stage, mutation과 reconciliation evidence | Existing adapter를 재사용한다. |
| Reliability public exports | Evaluator 호출 surface | New evaluator와 result를 export한다. |

### Boundaries

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| Read-only lifecycle | Null-spike incident, evidence, impact와 remediation draft | Approval, mutation과 evaluation |
| Recovery executor | Approved candidate staging, compare-and-replace, profile evidence와 content identity | Detection threshold와 incident-resolution 판정 |
| Null-spike evaluator | Defect control, single incident selection, null-rate oracle, replay와 dbt evidence | Generic orchestration framework와 partial repair |
| External caller | Approval callback과 candidate/target dbt validation callback | Lifecycle 내부 자동 승인 |

Evaluator entry는 target, clean과 candidate database path가 존재하지 않고 서로 다른 physical path인지 하나의 preflight에서 확인한다. Preflight는 `root.mkdir()`을 포함한 directory/file/database 생성, source load, synthetic materialization과 external callback보다 먼저 완료한다. 이 제한은 synthetic defect setup을 recovery mutation과 혼동하지 않고 `target_mutated` evidence를 정확히 유지하며, `source_file` evaluation이 같은 연도의 다른 file population과 profile을 합치는 것을 방지한다.

## Data Flow

| Step | From | To | Data / Contract |
| ---: | --- | --- | --- |
| 1 | Clean source | Clean database | Baseline profile, fixture content identity와 clean lifecycle result |
| 2 | Clean source | Synthetic file | `target_column`, `null_fraction`, `sample_fraction=1.0` |
| 3 | Synthetic file | Target database | Same-row-count partition with requested null mutation |
| 4 | Target database | Read-only lifecycle | Achieved target-column null-rate delta, exact single incident와 target content identity |
| 5 | Original clean fixture | Candidate database | Fixture-equal expected recovery identity, baseline null rate와 isolated dbt projection |
| 6 | Candidate + target state | Recovery proposal | Incident, candidate, before/after identity, evidence와 actions |
| 7 | External approval | Recovery executor | Exact approved proposal와 staged clean candidate |
| 8 | Recovery executor | Evaluator | Content validation, profile snapshot, mutation state와 replay result |
| 9 | Recovered target | Read-only lifecycle | Post-recovery incident resolution과 target column null rate |
| 10 | Recovered target | Target dbt validation | Promoted or failed dbt projection evidence |

## Decisions

### D1. Existing full-partition recovery를 재사용한다

- **Decision** - Clean source candidate를 `overwrite_partition`과 `rerun_profile_snapshot` actions로 적용한다.
- **Rationale** - `null_spike`는 partition row shape를 유지한 content defect이며 stable identity와 exact approval이 이미 full content replacement를 보호한다.
- **Trade-off** - 새 mutation contract가 없지만 partial column repair보다 mutation 범위가 크다.
- **Alternatives** - Column-only update와 incident-specific recovery executor branch는 새 approval action과 reconciliation semantics가 필요해 제외한다.

### D2. Clean fixture exact restoration을 evaluator가 판정한다

- **Decision** - Recovery executor의 `validation_passed`는 content identity equality로 유지한다. Evaluator는 candidate identity가 original clean fixture identity와 같고 post-recovery target column null rate가 baseline null rate와 정확히 같은지 판정한다.
- **Rationale** - Mutation correctness와 incident semantics를 분리해야 다른 incident가 recovery executor contract를 재사용할 수 있다.
- **Trade-off** - Detection threshold 아래 residual defect도 실패하므로 이 vertical slice는 clean fixture 복원 proof에 한정된다.
- **Alternatives** - Null-rate threshold를 executor에 주입하면 detection config와 mutation boundary가 결합되므로 제외한다.

### D3. 전체 lifecycle incident를 정확히 하나로 제한한다

- **Decision** - Evaluator input은 하나의 `target_column`을 받고 profile columns에 해당 column이 포함되는지 검증한다. Synthetic generation은 `sample_fraction=1.0`을 사용하며 lifecycle 결과가 정확히 target-column `null_spike` 하나일 때만 proposal을 만든다. Zero, multiple 또는 unrelated incident는 mutation 전에 failure result로 종료한다.
- **Rationale** - `LifecycleResult`는 incident ID, type과 evidence의 구조적 대응을 보존하지 않으므로 복수 incident에서 안전하게 target ID를 선택할 수 없다. Full sample은 accidental volume-drop detection을 차단한다.
- **Trade-off** - Multi-column data quality incident는 후속 Change로 남는다.
- **Alternatives** - 첫 slice에서 모든 detected null-spike incidents를 묶는 방식은 현재 single proposal flow를 확장하므로 제외한다.

### D4. Synthetic defect는 achieved behavior로 확인한다

- **Decision** - Synthetic function의 requested fraction 자체를 incident 성립 근거로 삼지 않는다. Defect lifecycle의 observed row count, target column null-rate delta와 exact incident cardinality로 controlled case 성립을 확인한다.
- **Rationale** - Source에 기존 null이 있으면 requested null fraction과 achieved delta가 다를 수 있다.
- **Trade-off** - Incident threshold를 넘지 못하는 source/parameter 조합은 evaluation failure로 종료된다.
- **Alternatives** - Synthetic generator contract 자체를 변경하는 것은 HMDA data capability의 별도 범위이므로 이번 Change에서 제외한다.

### D5. Generic evaluator abstraction을 만들지 않는다

- **Decision** - New incident-specific module에서 existing public primitives를 직접 조합한다. 실제로 동일한 pure helper가 필요할 때만 최소 helper를 이동한다.
- **Rationale** - Volume-drop의 single-incident mapping과 required action을 공통 계약으로 잘못 고정하지 않는다.
- **Trade-off** - 일부 control flow 중복을 허용한다.
- **Alternatives** - Base class, strategy registry와 orchestration DSL은 현재 두 use case에 비해 비용이 크다.

### D6. Evaluation database는 distinct disposable isolation을 요구한다

- **Decision** - `request.database_path`, workspace clean database와 candidate database가 이미 존재하거나 서로 같은 physical path를 식별하면 모든 load와 callback 전에 거부한다.
- **Rationale** - Synthetic case setup이 caller의 기존 partition을 변경하면 pre-mutation safety evidence가 거짓이 되고 file-scoped profile population도 오염될 수 있다.
- **Trade-off** - Existing operational database를 직접 대상으로 평가할 수 없다.
- **Alternatives** - Existing database를 snapshot/copy하는 방식은 이번 local vertical slice에 불필요한 storage와 lifecycle complexity를 추가한다.

## Testability

| Boundary / Behavior | Test Strategy | Evidence |
| --- | --- | --- |
| Controlled defect | Integration | Row count 보존, achieved target column null-rate delta와 exact single `null_spike` detection |
| Approved recovery | Integration | `partition_changed`, content identity equality와 restored profile null rate |
| Residual-null candidate | Integration | Threshold 아래 residual null-rate candidate도 fixture identity/null-rate mismatch로 mutation 전에 실패한다. |
| Replay | Integration | Successful replay와 replay profile/divergence failure에서 first recovery evidence가 보존된다. |
| Safety failures | Existing component tests + focused evaluator integration | Invalid candidate, incomplete approval, stale/diverged target, pre/post-mutation dbt failure와 artifact re-observation evidence |
| Read-only boundary | Regression | Lifecycle 호출만으로 approval, mutation과 report write가 발생하지 않는다. |
| Public API | Unit/import smoke | Reliability package에서 evaluator와 result import 가능 |
| Target isolation | Integration | Existing 또는 aliased database path를 entry preflight에서 거부하고 workspace와 original content에 side effect가 없음을 확인한다. |
| Quality acceptance | Integration | Baseline/recovery/replay null-rate evidence와 `validation_passed` failure mapping |
| Callback failure | Integration | Candidate/target `ValueError`의 pre/post-mutation structured evidence |

- **TDD Boundary:** Happy path 전에 controlled defect가 row count를 보존하면서 전체 lifecycle incident를 target-column `null_spike` 하나로 제한하고, residual-null candidate가 clean fixture identity/null-rate mismatch로 mutation 전에 차단되는 RED를 먼저 고정한다.
- **Failure Signals:** Unexpected incident, zero or multiple incident, missing target column profile, unresolved post-recovery incident, baseline과 다른 null rate, wrong mutation state, lost first recovery evidence, changed prior artifact projection과 incorrect reconciliation action을 명시적으로 실패시킨다.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Fixture가 `volume_drop`과 `null_spike`를 함께 탐지한다. | Single incident proposal 생성이 실패한다. | `sample_fraction=1.0`과 stable source scope를 강제하고 detected types를 검증한다. |
| Existing null 때문에 requested defect delta가 성립하지 않는다. | Controlled case가 incident를 만들지 못한다. | Requested parameters가 아니라 observed null-rate delta와 exact incident cardinality를 확인하고 pre-mutation failure로 종료한다. |
| Profile columns에 target column이 없다. | Null-rate oracle이 silently 누락된다. | Evaluator entry에서 target column 포함 여부를 검증한다. |
| Approved candidate가 여전히 spiked 상태다. | Content identity만 통과하는 false-green이 생긴다. | Post-recovery lifecycle와 baseline-relative null-rate를 독립 acceptance로 확인한다. |
| Existing target database를 synthetic setup이 덮어쓴다. | Safety failure가 원래 data를 변경하면서 `target_mutated=False`로 보고된다. | Existing target/clean/candidate database path를 side effect 전에 거부한다. |
| New database path가 서로 alias된다. | Candidate setup이 approval 전에 target을 clean content로 덮어쓴다. | 세 path의 resolved physical identity가 pairwise distinct인지 확인한다. |
| Volume-drop evaluator를 복사하며 bug fix가 분산된다. | Safety behavior가 incident별로 달라질 수 있다. | Existing recovery/safety adapters를 재사용하고 pure helper만 확인된 중복에 한해 공유한다. |
| Remediation draft가 backfill을 제안하지 않는다. | Draft와 demonstration recovery 사이에 product ambiguity가 남는다. | 이번 Change에서는 현재 draft contract를 보존하고 후속 product decision으로 분리한다. |

## Migration

| Phase | Change | Verification |
| ---: | --- | --- |
| 1 | Current Specs를 archived volume-drop delta와 동기화한다. | `openspec validate --all` |
| 2 | Null-spike evaluator와 public export를 추가한다. | Focused integration 및 import tests |
| 3 | Domain documentation에 beyond-MVP null-spike evaluation surface를 반영한다. | Markdown format과 link check |

- **Compatibility:** Existing recovery request/result와 volume-drop evaluator API를 변경하지 않는 additive change다.
- **Rollback:** New evaluator, exports와 documentation만 제거하면 기존 runtime behavior로 복원된다.
