---
type: research
title: Schema Drift 기능 완성 리서치
description: 현재 repository의 schema_drift 탐지·synthetic·recovery 계약과 DuckDB transaction semantics를 대조해 post-MVP 기능 완성을 위한 최소 안전 경계와 결정 지점을 조사한다.
status: "completed"
tags:
  - reliability
  - schema-drift
  - recovery
  - post-mvp
---

> [!NOTE]
> **결론:** 현재 `schema_drift`는 synthetic defect와 detection까지는 구현되어 있지만 recovery capability는 아직 없다. 가장 작은 올바른 후속 방향은 기존 partition backfill을 억지로 확장하거나 범용 migration engine을 만드는 것이 아니라, **table-wide schema/content state를 approval에 결합하고 검증된 complete-table candidate를 transaction 안에서 exact replacement한 뒤 schema/content/lifecycle/dbt evidence로 재검증하는 별도 recovery vertical slice**다.
>
> 현재 canonical MVP status는 volume-drop MVP를 `24/24 Implemented`, `24/24 Passing`으로 기록한다. 따라서 이전 research에 있던 “MVP 완료를 다시 승인받아야 schema_drift planning을 시작할 수 있다”는 repository gate는 제거한다. `schema_drift`가 다음 우선순위인지 여부만 인간이 결정하면 된다.[^mvp-status]

## Question

현재 Project Pivot의 architecture와 기존 recovery safety contract를 약화하지 않으면서 `schema_drift` 기능을 가장 작은 범위로 완성하려면 무엇이 필요한가?

### Scope

- 기준 revision: `main@740cdcbdf7780ee0d5421b70dd1d4f2450b1f297`
- current `schema_drift` synthetic case, profile schema identity와 detector
- current partition recovery approval, mutation, replay와 evaluation safety pattern
- HMDA full-table/partition ingestion primitive
- DuckDB transaction 및 table replacement semantics
- recovery 이후 schema/content/lifecycle/dbt verification
- 후속 OpenSpec에서 반드시 결정해야 할 boundary

### Out of Scope

- current MVP scope 변경
- 범용 schema migration planner
- arbitrary DDL 생성·실행 engine
- multi-table 또는 multi-database recovery
- production authorization, human approval UI, Dagster scheduling
- schema order/constraint/default/nullability drift까지 첫 slice에서 일반화
- `freshness_delay` recovery

## Evidence Discipline

이 research는 다음 evidence class를 구분한다.[^research-evidence]

| Class | Evidence | Use |
| --- | --- | --- |
| **Authoritative** | Architecture, current OpenSpec Spec, domain/MVP docs | 현재 의도와 boundary |
| **Observed** | source code와 tests | 실제 구현 behavior |
| **Supporting** | DuckDB official documentation | 구현 후보의 기술적 가능성 |
| **Unverified** | 아직 작성하지 않은 transaction/concurrency experiment | OpenSpec/RED에서 검증할 항목 |

현재 branch에서 test suite를 새로 실행하지 않았으므로 “현재 모든 test가 지금도 통과한다”는 주장은 하지 않는다. MVP completion은 canonical status 문서가 기록한 상태를 인용한다.[^mvp-status]

## Evidence Snapshot

| Area | Current evidence | `schema_drift` completion status |
| --- | --- | --- |
| Synthetic defect | `schema_drift()`가 기본 `loan_amount`를 `VARCHAR`로 cast한다. | ✅ Existing |
| Detection | baseline/current `schema_hash`가 다르면 `schema_drift` incident를 만든다. | ✅ Existing |
| Schema identity | `DESCRIBE table`의 **column name + type**만 name-sort 후 hash한다. | ✅ Existing, limited semantics |
| Incident scope | `Incident.partition`은 필수지만 schema hash는 table-wide다. | ⚠️ Scope mismatch |
| Approval contract | `RecoveryProposal`은 partition + `PartitionContentIdentity` before/candidate/after에 묶인다. | ❌ Table state 없음 |
| Recovery mutation | `execute_approved_backfill()`은 partition row compare-and-replace만 수행한다. | ❌ Schema restoration 불가 |
| Full-table load | `load_hmda_loans()`는 `CREATE OR REPLACE TABLE`을 사용한다. | ⚠️ Candidate primitive only |
| Evaluation model | `EvaluationCaseResult`와 report surface는 generic하다. | ✅ Reusable |
| Recovery evaluation adapter | `build_recovery_evaluation_case()`는 `BackfillValidationResult`와 `partition_changed`에 결합된다. | ⚠️ Partition-specific |
| MVP gate | canonical status는 volume-drop MVP 완료를 기록한다. | ✅ Post-MVP planning 가능 |

## Answer

현재 evidence로 가장 신뢰할 수 있는 answer는 다음 7개다.

1. **Detection을 다시 만들 필요가 없다.** 현재 first slice의 detection semantics는 column-name/type schema hash mismatch로 충분하다.
1. **Mutation scope는 partition이 아니라 table이다.** 현재 backfill executor를 incident type만 바꿔 재사용할 수 없다.
1. **기존 safety pattern은 재사용하되 기존 contract shape는 보존한다.** candidate preflight, exact approval binding, before/after reconciliation, post-mutation verification은 재사용할 가치가 있지만 `RecoveryProposal`/`ApprovedBackfillRequest`를 table recovery 의미로 억지로 일반화하지 않는다.
1. **Approval은 schema와 content를 함께 묶어야 한다.** schema hash만 복원되어도 content가 달라지면 성공이 아니며, content만 같아도 schema가 drift된 상태면 성공이 아니다.
1. **첫 mutation 전략의 leading candidate는 validated complete-table replacement다.** reverse `ALTER COLUMN TYPE`보다 exact clean candidate를 staging/preflight한 뒤 explicit transaction에서 target을 교체하는 방향이 현재 use case에 더 맞다. 실제 SQL pattern과 concurrency behavior는 RED test로 확정해야 한다.
1. **첫 slice는 generic schema migration이 아니다.** `loan_amount: numeric → VARCHAR` controlled type drift 하나를 clean state로 되돌리는 exact restoration proof로 제한한다.
1. **기능 완료는 evaluator까지 포함한다.** detection 성공만이 아니라 invalid candidate, stale/diverged target, rollback, replay, post-recovery dbt failure까지 structured evidence로 남아야 한다.

## Findings

### F1. Post-MVP 진입을 막는 repository completion gate는 현재 없다

`docs/development/mvp/status.md`는 volume-drop MVP의 모든 domain implementation/verification을 완료 상태로 기록한다. `docs/development/mvp/README.md`는 `schema_drift`를 current MVP 밖의 후속 incident 확장으로 정의한다.[^mvp][^mvp-status]

이 두 사실은 다음을 함께 의미한다.

- `schema_drift`를 MVP 안으로 끌어들일 이유는 없다.
- 반대로 MVP가 미완성이라 schema_drift planning을 보류해야 한다고 볼 현재 canonical evidence도 없다.

**Implication:** 이 research 이후 human priority 결정만 있으면 focused OpenSpec Research/Plan으로 진입할 수 있다.

### F2. 현재 `schema_drift`는 “모든 schema drift”가 아니라 name/type identity drift다

`calculate_schema_hash()`는 DuckDB `DESCRIBE` 결과에서 column `name`과 `type`만 사용하고 column name 기준으로 정렬해 hash한다.[^profile]

따라서 현재 detection이 직접 표현하는 것은 다음이다.

- column 추가/삭제로 name set이 달라짐
- 같은 column의 type이 달라짐

반대로 첫 slice에서 다음까지 지원한다고 해석하면 안 된다.

- column order 변화
- nullability
- default
- primary/check/unique constraint
- 기타 DuckDB catalog metadata

`schema_drift()` synthetic case도 이 boundary와 일치하게 `loan_amount` type을 `VARCHAR`로 바꾼다.[^synthetic]

**Implication:** 첫 capability의 실제 proof는 **column-name/type schema restoration**이다. 더 넓은 schema semantics는 별도 확장이다.

### F3. Detection evidence는 table-wide지만 Incident contract는 partition-scoped다

Profile snapshot은 특정 partition row metrics와 **table-wide schema hash**를 한 객체에 담는다.[^profile] Detection Spec은 같은 asset/partition profile pair를 비교하고 schema hash가 다르면 incident를 만든다.[^detection-spec]

동시에 `Incident.partition`은 필수 field다.[^incident]

따라서 현재 구조에서는 같은 table schema drift가 partition별 lifecycle에서 반복 관찰될 수 있고, incident의 `partition`이 실제 schema mutation target처럼 오해될 수 있다.

**Implication:** 후속 OpenSpec은 최소한 다음 의미를 분리해야 한다.

- `incident.partition`: 어느 profile/lifecycle observation에서 발견됐는가
- `recovery target`: 실제로 변경해야 하는 table은 무엇인가

Incident contract를 지금 바로 table-level로 일반화할 필요는 없지만, **partition label을 mutation scope로 재사용하면 안 된다.**

### F4. 현재 partition recovery로는 table schema를 복원할 수 없다

`load_hmda_loans_partition()`은 existing table을 `CREATE TABLE IF NOT EXISTS`로 유지한 뒤 staging rows를 검증하고 transaction 안에서 target partition을 `DELETE + INSERT`한다.[^partition]

즉 drifted target이 다음 상태라면:

```text
raw.hmda_loans.loan_amount = VARCHAR
                  ↓
        partition DELETE + INSERT
                  ↓
raw.hmda_loans.loan_amount = VARCHAR
```

clean row를 다시 넣어도 existing table schema는 바뀌지 않는다.

**Implication:** `execute_approved_backfill()`에 `schema_drift` incident를 전달하는 것만으로는 recovery가 아니다. Canonical `reliability-recovery-backfill` Spec도 명시적으로 HMDA **partition recovery**를 소유한다.[^recovery-spec]

### F5. 기존 recovery에서 재사용해야 할 것은 API가 아니라 safety invariants다

현재 backfill recovery는 다음 safety sequence를 이미 증명하는 구조다.[^executor][^recovery-spec]

```text
approval exactness
→ candidate staging / validation
→ current target = approved before | expected after | third state
→ approved before만 mutation
→ expected after면 mutation 없이 verification resume
→ third state면 new validation/approval
→ post-mutation profile validation
```

이 pattern은 schema recovery에도 매우 가치가 있다. 그러나 현재 `RecoveryProposal` 자체는 `source_year`, `source_file`, 세 개의 `PartitionContentIdentity`를 강제한다.[^proposal]

**Implication:** safety semantics는 재사용하되, partition contract를 table recovery contract로 변형해 기존 public meaning을 흐리지 않는다.

### F6. Schema recovery에는 explicit composite table state가 필요하다

`PartitionContentIdentity`는 row order와 `ingested_at`에 독립적이며 logical values와 duplicate multiplicity를 hash한다. 하지만 반드시 `source_year`와 optional `source_file` scope를 가진다.[^partition-identity]

Schema recovery approval에는 최소한 다음 state를 비교할 수 있어야 한다.

- target table identity
- observed before schema identity
- expected after schema identity
- before content state
- candidate/expected-after content state
- candidate validation evidence
- exact mutation action

#### Content-state alternatives

| Alternative | 장점 | 약점 | Research view |
| --- | --- | --- | --- |
| New monolithic whole-table row digest | 하나의 값으로 비교 | 기존 identity logic 중복, 큰 table 비용과 새 semantics | ⚠️ 가능하지만 우선순위 낮음 |
| **Schema hash + sorted partition identities** | 기존 stable identity 재사용, partition별 audit 가능 | complete population enumeration 계약 필요 | ✅ Leading candidate |
| Schema hash + source path/file manifest | 구현 단순 | actual logical content equality를 증명하지 못함 | ❌ 불충분 |

**Inference:** 첫 OpenSpec에서는 새로운 거대한 hash를 바로 만들기보다 **table schema identity + complete set의 existing partition content identities**를 composite after-state로 표현할 수 있는지 먼저 검증하는 편이 KISS/DRY에 가깝다. 이 선택은 아직 canonical design이 아니다.

### F7. Candidate completeness가 schema recovery의 핵심 추가 위험이다

Partition backfill은 승인된 한 partition만 바꾸면 된다. 하지만 exact table replacement는 candidate가 **target table 전체 population**을 대표해야 한다.

Candidate source 일부가 빠진 상태에서 schema만 정상이라면 table replacement는 schema를 고치면서 다른 partition data를 삭제할 수 있다.

따라서 candidate preflight는 단순히 다음만 보면 부족하다.

- required columns 존재
- target schema hash 정상
- 일부 partition content 정상

**Implication:** eventual proposal/evidence는 **candidate population completeness**를 검증할 수 있어야 한다. 앞의 sorted partition identity set이 유력한 이유도 여기에 있다.

### F8. 기존 full-load는 mutation primitive의 재료지만 그대로 recovery에 쓰면 안 된다

`load_hmda_loans()`는 모든 source를 `CREATE OR REPLACE TABLE`로 materialize하므로 clean input에서 schema를 되돌릴 수 있는 primitive를 이미 가진다.[^full-load]

그러나 현재 함수는 required-column validation을 **target replacement 이후** 실행하고, validation failure에서도 새 target table이 남을 수 있다고 docstring에 명시한다.[^full-load]

이는 current recovery의 다음 invariant와 충돌한다.

- invalid candidate는 zero mutation
- approval mismatch는 source access/target mutation 전 차단
- stale target은 first mutation 전 차단

**Implication:** full-load를 그대로 호출하지 않는다. Candidate는 별도 database/table에서 먼저 완성·검증해야 한다.

### F9. DuckDB semantics는 exact replacement 전략의 기술적 가능성을 뒷받침한다

DuckDB 공식 문서는 ACID transaction과 rollback을 지원한다고 명시한다. `CREATE OR REPLACE TABLE`은 기존 table을 drop하고 새 table을 만드는 shorthand다. 또한 `ALTER TABLE`은 transactional semantics를 따르지만, `ALTER COLUMN TYPE`은 table에 과거 conflicting value가 존재한 경우 실패할 수 있고 문서는 table copy를 workaround로 제시한다.[^duckdb-transaction][^duckdb-create][^duckdb-alter]

이 evidence는 다음 hypothesis를 강화한다.

```text
isolated complete candidate
→ preflight schema + content + dbt
→ BEGIN TRANSACTION
→ re-check approved before-state
→ exact table replacement from validated candidate
→ verify in-transaction state
→ COMMIT
```

다만 official docs는 Project Pivot의 exact connection/concurrency pattern을 증명하지 않는다.

**Implication:** OpenSpec/RED에서 반드시 다음을 직접 검증한다.

- candidate staging object와 target replacement가 같은 transaction에서 rollback되는가
- stale-state check와 first mutation 사이에 허용하지 않은 writer가 끼어들 수 없는가
- injected failure가 target before-state를 보존하는가

### F10. Reverse `ALTER COLUMN TYPE`은 첫 slice의 기본 전략으로 부적합하다

첫 defect가 `loan_amount → VARCHAR` 하나이므로 `ALTER COLUMN TYPE`으로 되돌리는 것이 가장 작은 것처럼 보일 수 있다.

하지만 이 접근은 다음 문제를 가진다.

- candidate clean content가 없어도 DDL만 승인하는 별도 mutation semantics가 생긴다.
- content corruption과 schema corruption을 하나의 exact after-state로 검증하기 어렵다.
- DuckDB 자체도 historical conflicting values 때문에 type alteration이 실패할 수 있음을 문서화한다.[^duckdb-alter]
- 이후 column add/drop/rename 요구를 만나면 migration engine 방향으로 쉽게 팽창한다.

**Implication:** first slice는 migration instruction 생성보다 **validated clean-state restoration**에 집중하는 것이 Project Pivot의 evidence-first recovery model과 더 일치한다.

### F11. Evaluation surface는 일부만 generic하다

`EvaluationCaseResult`는 incident, evidence, mutation 여부, failure stage, reconciliation action을 일반적으로 표현한다.[^evaluation-case]

반면 `build_recovery_evaluation_case()`는 입력으로 `BackfillValidationResult`를 받고 `mutation_state == "partition_changed"`인지 검사한다.[^evaluation-recovery-case]

**Implication:** schema recovery가 새 result contract를 가지면 기존 adapter를 그대로 재사용할 수 없다.

첫 slice에서 미리 generic recovery framework를 만들지 않는다. 권장 순서는 다음이다.

1. `EvaluationCaseResult`와 report surface는 재사용한다.
1. schema-specific evaluation adapter/result를 먼저 만든다.
1. partition/schema 두 mutation family의 실제 중복이 확인된 뒤 최소 공통 abstraction을 검토한다.

### F12. dbt failure는 defect oracle이 아니라 downstream verification evidence다

Raw `loan_amount` type이 `VARCHAR`여도 dbt staging의 cast behavior나 실제 값에 따라 build가 반드시 실패한다고 단정할 수 없다.

**Implication:** first slice에서 primary correctness oracle은 다음이다.

1. expected schema identity equality
1. expected complete content state equality
1. post-recovery lifecycle에서 `schema_drift` 해소

DBT는 candidate와 recovered target의 downstream compatibility를 증명하는 별도 evidence다. “schema drift가 있으면 dbt가 반드시 실패해야 한다”를 acceptance requirement로 만들지 않는다.

## False-Proof Traps

다음 구현은 test가 녹색이어도 실제 schema recovery proof가 아닐 수 있다.

### Trap 1. Drifted source를 existing clean table에 partition load한다

Existing table schema는 유지되므로 source `VARCHAR`가 target type으로 coercion되거나 insert 실패할 뿐, **table schema drift 자체가 만들어지지 않을 수 있다.**

**Guard:** defect target은 drifted source schema로 새 table을 materialize해 실제 target schema hash가 baseline과 다른지 먼저 증명한다.

### Trap 2. 한 partition만 있는 table로 whole-table recovery를 증명한다

Single-partition fixture는 candidate completeness와 unaffected-partition preservation 문제를 숨긴다.

**Guard:** 가능하면 first acceptance fixture에 최소 하나의 sentinel partition을 두고, recovery 후 모든 partition identity set이 expected after-state와 같은지 확인한다.

### Trap 3. Schema hash만 맞으면 성공 처리한다

Schema는 복원됐지만 일부 partition row가 유실되거나 달라질 수 있다.

**Guard:** schema identity와 complete content state를 모두 final oracle에 포함한다.

### Trap 4. `CREATE OR REPLACE TABLE` 후 candidate validation한다

현재 full-load의 기존 위험을 그대로 recovery에 복사한다.

**Guard:** target mutation 전 isolated candidate schema/content/dbt validation을 완료한다.

### Trap 5. dbt 실패 여부로 schema drift를 판정한다

DBT가 drift를 허용하거나 cast할 수 있어 false negative/false assumption이 생긴다.

**Guard:** schema hash mismatch를 defect oracle로 유지한다.

## Options

| Option | Reuse | Safety/semantic cost | Decision |
| --- | --- | --- | --- |
| Existing partition backfill contract 확장 | 코드 재사용 많아 보임 | table-wide scope와 partition semantics 충돌 | ❌ Reject |
| Reverse `ALTER COLUMN TYPE` recovery | DDL 한 번으로 작아 보임 | migration semantics, conversion/history risk, content oracle 약함 | ❌ First slice 비권장 |
| Existing full-load 직접 호출 | 구현량 적음 | mutation-before-validation | ❌ Reject |
| Generic schema migration engine | 장기 확장성 큼 | YAGNI, approval/action surface 급증 | ❌ Reject |
| **Separate approval-safe exact table restoration** | current safety invariants + schema hash + identity 재사용 | table state와 replacement contract 필요 | ✅ Recommend |
| Detection + containment only | mutation risk 없음 | “recovery feature completion” 목표를 달성하지 못함 | ⚠️ Recovery를 의도적으로 defer할 때만 |

## Recommended First Slice

> [!IMPORTANT]
> 아래는 research가 권장하는 **최소 proof boundary**다. 실제 requirement/class/API 이름은 후속 OpenSpec이 소유한다.

```text
complete clean HMDA candidate
        ↓
controlled loan_amount type drift target
        ↓
schema_drift detection
        ↓
impact + remediation draft (read-only)
        ↓
complete candidate preflight
  ├─ schema identity
  ├─ complete content state
  └─ candidate dbt evidence
        ↓
external approval
  ├─ exact table target
  ├─ before schema/content state
  ├─ expected after schema/content state
  └─ exact mutation actions
        ↓
transactional exact table restoration
        ↓
post-recovery verification
  ├─ schema identity restored
  ├─ complete content restored
  ├─ schema_drift resolved
  └─ target dbt evidence
        ↓
replay / failure evidence
```

### Explicit first-slice limits

- one HMDA table: `raw.hmda_loans`
- one controlled drift family: existing `loan_amount → VARCHAR`
- schema semantics: column name/type identity only
- exact clean-state restoration; no forward migration planning
- approval remains external
- lifecycle remains read-only
- no automatic repair
- no multi-table cascade recovery

## OpenSpec Decision Gates

다음 5개를 결정하지 않고 implementation task를 만들면 scope가 다시 흔들릴 가능성이 높다.

### D1. Recovery capability ownership

**Question:** table-schema recovery를 existing `reliability-recovery-backfill`에 넣는가, 별도 capability로 두는가?

**Research recommendation:** 별도 capability. Existing Spec은 partition backfill을 명시적으로 소유한다.[^recovery-spec]

### D2. Composite table state

**Question:** approval/replay/stale check에서 table before/after state를 어떻게 표현하는가?

**Leading candidate:** schema hash + complete sorted partition identity set.

**Must reject:** schema hash only, source path manifest only.

### D3. Observation scope vs mutation scope

**Question:** partition-scoped Incident가 발견한 table-wide drift를 recovery target에 어떻게 연결하는가?

**Need:** incident partition을 table mutation scope로 오해하지 않는 explicit mapping.

### D4. Transactional replacement primitive

**Question:** validated candidate를 어떤 exact SQL/transaction sequence로 target에 적용하는가?

**Need:** stale check, replacement, final identity verification과 rollback behavior를 RED test로 증명.

### D5. Recovery/evaluation result contract

**Question:** `BackfillValidationResult`와 별도 schema recovery result 중 무엇을 사용하는가?

**Research recommendation:** partition-specific result를 억지로 확장하지 말고 schema recovery result를 먼저 구체화한 뒤 공통 abstraction을 검토.

## Suggested Validation Matrix

후속 OpenSpec이 acceptance를 구체화할 때 아래 evidence가 빠지면 false-green 가능성이 높다.

| Scenario | Expected mutation | Required evidence |
| --- | :---: | --- |
| Clean baseline | No | no `schema_drift`, baseline schema/content state |
| Controlled type drift | Setup only | schema hash differs, expected `schema_drift` detected |
| Candidate schema mismatch | No | rejected before target mutation |
| Candidate content mismatch | No | rejected before target mutation |
| Candidate incomplete population | No | missing partition/population evidence, rejected |
| Incomplete/mismatched approval | No | approval gate rejection |
| Target schema changed after approval | No | stale/diverged target |
| Target content changed after approval | No | stale/diverged target |
| Failure during replacement transaction | Rollback | exact before-state preserved |
| Approved before-state | Yes | exact after schema + content state |
| Post-recovery lifecycle | No extra mutation | `schema_drift` resolved |
| Post-recovery dbt failure | Already mutated | failure evidence + `resume_verification` candidate |
| Exact after-state replay | No | no duplicate replacement, verification resumed |
| Third state replay | No | new validation/approval required |
| Sentinel unaffected partition | Replacement includes it | identity unchanged from expected candidate |

## Implementation Handoff

Research가 implementation을 확정하지는 않지만, 다음 작업이 어디서 시작되어야 하는지는 충분히 좁혀졌다.

1. **OpenSpec Research/Proposal:** table-schema recovery를 별도 capability로 다룰지 D1~D5를 확정한다.
1. **Design:** composite table state와 candidate completeness, transaction sequence를 정의한다.
1. **RED:** candidate mismatch, stale/diverged state, rollback, replay부터 고정한다.
1. **GREEN:** validated complete candidate exact replacement의 최소 primitive를 구현한다.
1. **Integration:** lifecycle은 read-only로 유지하고 external approval 뒤 별도 recovery API를 연결한다.
1. **Evaluation:** schema-specific vertical slice와 failure/replay evidence를 추가한다.
1. **Review:** partition backfill public semantics가 변하지 않았는지 별도로 검증한다.

## Remaining Uncertainty

| Uncertainty | Current answer | Resolve by |
| --- | --- | --- |
| Composite table content identity shape | sorted partition identities가 leading candidate | OpenSpec Design + RED |
| Candidate population enumeration | complete source/partition set 필요 | HMDA ingestion contract review |
| Exact DuckDB replacement SQL | explicit transaction + exact replacement가 viable hypothesis | focused integration test |
| Concurrent writer behavior | official snapshot isolation만으로 repo pattern을 확정할 수 없음 | multi-connection RED test |
| Incident partition semantics | observation scope로 유지 가능하나 mutation scope와 분리 필요 | OpenSpec Design |
| Evaluation adapter abstraction | generic report는 재사용, recovery adapter는 partition-specific | schema slice 구현 후 비교 |

## Conclusion

`schema_drift` 기능 완성의 본질은 anomaly detector 확장이 아니다.

현재 저장소에는 이미:

- deterministic type-drift synthetic input
- table-wide name/type schema hash
- schema hash mismatch detector
- read-only impact/remediation lifecycle
- approval-bound partition recovery에서 검증된 safety invariants
- generic evaluation/report primitives

가 존재한다.

부족한 것은 **table-level recovery state와 mutation contract**다.

따라서 가장 작은 고품질 방향은 다음이다.

```text
existing detection
        ↓
explicit table-level schema/content state
        ↓
approval-safe complete candidate
        ↓
transactional exact table restoration
        ↓
schema + content + lifecycle + dbt verification
        ↓
replay / failure evidence
```

기존 partition backfill contract는 그대로 보존한다. 범용 migration engine도 만들지 않는다. 첫 proof는 **한 table / existing type-drift family / exact clean-state restoration**으로 제한한다.

### Next Decision

**이 research를 기준으로 `schema_drift`를 다음 post-MVP capability로 선택할지 결정한다.** 선택한다면 첫 OpenSpec의 핵심은 구현 task가 아니라 D1~D5 contract decision이다.

## Evidence

[^mvp-status]: `docs/development/mvp/status.md` — 현재 문서는 volume-drop MVP를 implementation `24/24`, verification `24/24` 완료 상태로 기록한다. Snapshot 표기는 2026-08-13이므로 live test execution 증거로 확대 해석하지 않는다.
[^mvp]: `docs/development/mvp/README.md` — current MVP는 `volume_drop` 단일 end-to-end proof이며 `schema_drift` 등은 MVP 밖 후속 확장이다.
[^architecture]: `docs/ARCHITECTURE.md` — lifecycle은 read-only, external approval 이후 recovery와 evaluation은 별도 API다.
[^reliability-domain]: `docs/domains/reliability.md` — current recovery는 approved partition backfill이며 volume/null-spike evaluation surface를 정의한다.
[^profile]: `src/project_pivot/reliability/profiling/profile_snapshot_builder.py#calculate_schema_hash` — table `DESCRIBE`의 column name/type만 name-sort 후 SHA-256한다.
[^detection-spec]: `openspec/specs/reliability-incident-detection/spec.md` — baseline/current schema hash mismatch를 `schema_drift`로 정의한다.
[^incident]: `src/project_pivot/reliability/contracts/incident.py#Incident` — `partition`이 required field다.
[^synthetic]: `src/project_pivot/hmda_data/synthetic/cases.py#schema_drift`, `tests/hmda_data/test_synthetic.py::test_synthetic_cases_expose_expected_defect_statistics` — 기본 target column을 `VARCHAR`로 변환하고 type을 검증한다.
[^proposal]: `src/project_pivot/reliability/contracts/recovery_proposal.py#RecoveryProposal` — `source_year/source_file`과 `PartitionContentIdentity` before/candidate/after를 강제한다.
[^partition-identity]: `src/project_pivot/hmda_data/ingestion/identity.py#PartitionContentIdentity`, `partition_content_identity` — row order/`ingested_at` 독립 logical partition identity이며 duplicate multiplicity를 포함한다.
[^partition]: `src/project_pivot/hmda_data/ingestion/partition.py#load_hmda_loans_partition`, `_replace_partition_in_transaction` — existing table schema를 유지하고 partition row를 transaction 안에서 compare-and-replace한다.
[^executor]: `src/project_pivot/reliability/recovery/executor.py#ApprovalBackfillValidator.execute` — exact approval, candidate staging, before/after/third-state reconciliation과 profile verification.
[^full-load]: `src/project_pivot/hmda_data/ingestion/full_load.py#load_hmda_loans` — `CREATE OR REPLACE TABLE` 후 required columns를 검증하므로 invalid candidate의 zero-mutation guarantee가 없다.
[^recovery-spec]: `openspec/specs/reliability-recovery-backfill/spec.md` — approved HMDA **partition** recovery, content identity, freshness, reconciliation contract.
[^evaluation-case]: `src/project_pivot/reliability/evaluation/case_result.py#EvaluationCaseResult` — generic case evidence model.
[^evaluation-recovery-case]: `src/project_pivot/reliability/evaluation/recovery_case.py#build_recovery_evaluation_case` — `BackfillValidationResult`와 `partition_changed` mutation state에 결합된다.
[^research-evidence]: `.agents/skills/pivot-research-workspace/references/evidence.md` — Authoritative/Observed/Supporting/Assumption evidence 분류와 traceability 기준.
[^duckdb-transaction]: DuckDB, “Transaction Management”, https://duckdb.org/docs/current/sql/statements/transactions — ACID transaction, commit/rollback과 snapshot isolation. Accessed 2026-08-16.
[^duckdb-create]: DuckDB, “CREATE TABLE Statement”, https://duckdb.org/docs/current/sql/statements/create_table — `CREATE OR REPLACE TABLE`은 existing table overwrite를 위한 drop+create shorthand. Accessed 2026-08-16.
[^duckdb-alter]: DuckDB, “ALTER TABLE Statement”, https://duckdb.org/docs/lts/sql/statements/alter_table — ALTER transaction semantics와 historical conflicting values에서 type alteration failure limitation. Accessed 2026-08-16.
