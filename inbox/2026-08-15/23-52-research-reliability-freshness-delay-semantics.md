---
type: research
title: Freshness Delay 의미론과 Recovery Boundary 리서치
description: Project Pivot의 freshness_delay를 실제로 측정·복구 가능한 Reliability vertical slice로 확장하기 전에 시간 의미론, detection 공식, synthetic defect, recovery state와 validation oracle을 재검토한다.
status: "completed"
tags:
  - reliability
  - freshness-delay
  - recovery
  - hmda
---

> [!NOTE]
> 현재 `freshness_delay` detector와 synthetic helper는 존재하지만 그대로 vertical slice로 확장하면 안 된다. 현재 detector는 데이터의 절대 staleness가 아니라 baseline 대비 timestamp 역행을 측정하고, 기본 HMDA lifecycle은 `freshness_column=None`이라 실제 freshness를 측정하지 않는다. 현 Project Pivot 범위에서는 upstream publication freshness를 과장하지 말고 **Bronze ingestion freshness**를 첫 vertical slice의 의미로 제한하는 것이 가장 작고 검증 가능하다. 다만 `ingested_at`은 content identity에서 제외되므로 기존 recovery state만으로는 freshness-only mutation을 안전하게 표현할 수 없다. 구현 전 `content identity + temporal freshness state`의 이중 oracle을 Spec으로 정의해야 한다.

## Question

`freshness_delay`를 Project Pivot의 네 번째 Reliability vertical slice로 만들 때, 현재 저장소가 실제로 측정하고 복구할 수 있는 freshness 의미는 무엇이며 어떤 contract를 먼저 정리해야 하는가?

### Scope

- current `main@0860475dc1f299129a078b9d8577b2f43d97ff5d`
- profile snapshot, detection, synthetic defect, remediation, approved recovery 계약
- HMDA local source/Bronze boundary와 외부 HMDA update cadence
- source download, production monitoring, alerting, Dagster reliability control-plane은 제외

### Stop Condition

- freshness clock과 detection 공식을 하나의 권장안으로 수렴한다.
- 현재 synthetic/recovery primitive를 그대로 재사용할 수 없는 이유를 검증한다.
- vertical slice 구현 전에 필요한 최소 Spec 경계를 식별한다.

## Findings

### F1. 현재 detector는 staleness age가 아니라 baseline regression을 측정한다

현재 detector는 `baseline.freshness_at - current.freshness_at`을 delay로 계산한다. 따라서 current timestamp가 baseline보다 과거로 이동한 경우는 잡지만, timestamp가 그대로 멈춘 채 시간이 오래 지나 실제 데이터가 stale해지는 경우는 탐지하지 못한다.[^detector]

Canonical incident-detection Spec도 같은 baseline/current 비교 의미를 요구한다.[^detection_spec]

일반적인 freshness SLA의 질문은 "이 데이터가 마지막으로 갱신된 뒤 얼마나 지났는가"다. dbt도 source freshness에서 `max(loaded_at_field)`와 계산 시각을 사용해 SLA를 판단한다.[^dbt_freshness]

**Implication:** `freshness_delay`의 판정식은 baseline regression이 아니라 다음 age 모델로 바꾸는 것이 적합하다.

```text
freshness_age = observed_at - freshness_at
freshness_age >= max_age -> freshness_delay
```

Baseline은 trend/evidence로 남길 수 있지만 incident 발생 여부의 기준으로 사용하지 않는다.

### F2. 기본 HMDA lifecycle은 실제 freshness를 측정하지 않는다

`DataOperationRequest.freshness_column`의 기본값은 `None`이다.[^data_operation_request] Profile builder는 freshness column이 없거나 측정값이 없으면 `observed_at`을 `freshness_at`으로 fallback하고 `freshness_used_fallback=1`만 기록한다.[^profile_builder][^profile_spec]

이 상태에서 `observed_at`이 진행할수록 fallback snapshot은 오히려 더 fresh하게 보인다. 즉 **측정 불가능**과 **방금 갱신됨**을 같은 timestamp로 표현한다.

**Implication:** freshness measurement가 unavailable이면 이를 fresh로 판정해서는 안 된다. 최소한 `freshness_used_fallback`인 snapshot은 `freshness_delay` 판정에서 제외하거나 explicit unavailable 상태로 처리해야 한다. dbt 역시 viable freshness timestamp가 없으면 일반적으로 freshness를 계산하지 않는 방향을 취한다.[^dbt_freshness]

### F3. 현재 Project Pivot은 upstream publication freshness를 직접 증명하지 못한다

HMDA source contract는 local CSV/Parquet 발견과 Bronze 적재를 소유하지만 source 다운로드는 범위 밖이다. Bronze가 추가하는 시간 metadata는 local `ingested_at`이다.[^hmda_domain]

공식 HMDA Dynamic National Loan-Level Dataset은 주간, 월요일 cadence로 갱신된다.[^hmda_publication] 그러나 현재 Project Pivot은 그 upstream publication timestamp를 source row나 별도 contract로 보존하지 않는다. 따라서 현 상태에서 `freshness_at`을 "CFPB/FFIEC가 데이터를 마지막으로 게시한 시각"이라고 부르면 repository evidence보다 강한 주장이 된다.

**Implication:** 첫 freshness vertical slice는 **Bronze ingestion freshness**로 제한하는 것이 가장 작고 검증 가능하다.

- `observed_at`: reliability가 Bronze를 검사한 시각
- `freshness_at`: 대상 Bronze partition의 최신 `ingested_at`
- `freshness_age`: `observed_at - freshness_at`
- `max_age`: 명시적으로 제공되는 평가/SLA threshold

Upstream publication freshness는 source acquisition/update metadata를 소유하는 별도 capability가 생긴 뒤 확장한다.

### F4. 현재 synthetic `freshness_delay()`는 순수 freshness defect가 아니다

현재 helper는 원본 HMDA row에 오래된 `observed_at` column을 새로 추가한다.[^synthetic] 기본 Bronze source contract에는 `observed_at` column이 없으므로 이 case는 실제 target에 적용할 때 freshness defect와 schema shape change를 섞을 수 있다.[^hmda_domain]

**Implication:** Bronze ingestion freshness를 선택한다면 synthetic case는 새 business/source column을 만들지 않아야 한다. 격리된 evaluation database에서 이미 존재하는 Bronze `ingested_at`을 결정론적으로 과거로 이동시키는 방식이 더 정확하다. 이 결함 주입은 source-data content defect가 아니라 **data-plane temporal defect**로 취급해야 한다.

### F5. 기존 content identity만으로는 freshness recovery를 표현할 수 없다

`PartitionContentIdentity`는 같은 logical content를 재적재한 시각 차이로 stale 처리하지 않기 위해 `ingested_at`을 명시적으로 제외한다.[^content_identity]

이는 content recovery에는 올바른 선택이지만 freshness-only recovery에는 중요한 결과를 만든다.

```text
before: same rows, old ingested_at
 after: same rows, new ingested_at

PartitionContentIdentity(before) == PartitionContentIdentity(after)
```

현재 recovery executor는 target identity가 `expected_after_identity`와 같으면 `already_recovered`로 보고 overwrite를 건너뛴다. 그 다음에야 `approved_before_identity`를 확인한다.[^recovery_executor]

따라서 freshness-only before/after의 content identity가 같으면 실제로 stale해도 첫 branch에서 `already_recovered`가 되어 recovery mutation이 실행되지 않을 수 있다.

**Implication:** freshness recovery는 기존 `approved_before_identity / expected_after_identity`만 재사용해서는 안 된다. **Temporal target state가 content state와 별도로 approval, mutation gate, replay와 validation에 참여해야 한다.**

### F6. Recovery는 content oracle과 temporal oracle을 분리해야 한다

Canonical recovery Spec은 content identity를 correctness의 최종 oracle로 두면서 incident-specific metric을 별도 profile evidence로 허용한다.[^recovery_spec] `null_spike`가 content identity와 null-rate evidence를 분리한 선례다.

Freshness도 같은 원칙을 따르되 temporal state가 mutation 여부 자체에 영향을 준다는 점이 다르다.

권장 conceptual model은 다음과 같다.

```text
Content state
- candidate content identity
- target logical content identity

Temporal state
- freshness_at
- observed_at
- max_age
- freshness_age
- measured / unavailable
```

Recovery 성공은 최소 다음을 함께 만족해야 한다.

1. approved content scope와 실제 target content가 일치한다.
2. freshness measurement가 fallback이 아닌 실제 measurement다.
3. `observed_at - freshness_at < max_age`다.
4. post-recovery lifecycle에서 `freshness_delay`가 해소된다.

Replay는 content identity가 같다는 이유만으로 `already_recovered`가 되어서는 안 되고, temporal state가 이미 acceptable한 경우에만 mutation을 생략해야 한다.

### F7. Freshness 때문에 Dagster나 source downloader를 끌어들이지 않는다

Architecture는 Dagster `pipeline_job`을 Bronze → dbt data plane으로 한정하고 reliability lifecycle, approval, recovery와 evaluation을 별도 API에 둔다.[^architecture]

Freshness의 의미를 정리하는 데 scheduler delay, upstream polling, production alerting이 필요한 것은 아니다. dbt도 freshness SLA와 check cadence를 별도 개념으로 다룬다.[^dbt_job]

**Implication:** 첫 vertical slice는 local deterministic evaluation으로 끝내고, orchestration/monitoring은 incident contract가 안정된 뒤 검토한다.

## Options

| Model | 현재 측정 가능성 | Recovery 복잡도 | 의미 정확성 | 결정 |
| --- | --- | --- | --- | --- |
| 현재 baseline regression | 높음 | 낮음 | 낮음 | Reject |
| Upstream publication freshness | 낮음 | 높음 | 높음 | Defer |
| Bronze ingestion freshness | 높음 | 중간 | 현재 scope에서 높음 | **Recommend** |
| HMDA row event-time freshness | 낮음 | 중간 | dataset 적합성 낮음 | Reject |

Bronze ingestion freshness는 "원천이 최신인가"가 아니라 "Project Pivot의 Bronze가 SLA 안에서 다시 적재되었는가"를 증명한다. 이 한계를 문서와 evidence에 명시하면 현재 repository boundary와 가장 잘 맞는다.

## Conclusion

`freshness_delay`는 바로 recovery implementation으로 들어갈 상태가 아니다. 먼저 freshness 의미론을 **Bronze ingestion freshness**로 좁히고 다음 contract를 정리해야 한다.

1. `freshness_at`은 현재 vertical slice에서 `max(ingested_at)` 의미로 고정한다.
2. detection은 `observed_at - freshness_at`과 explicit `max_age`를 비교한다.
3. fallback measurement는 fresh로 해석하지 않고 unavailable로 다룬다.
4. synthetic defect는 새 `observed_at` column을 추가하지 않고 isolated Bronze의 `ingested_at`을 지연시킨다.
5. recovery proposal/state에는 content identity와 별개의 temporal state가 필요하다.
6. replay는 content equality와 temporal acceptance를 함께 확인한 뒤 mutation 생략 여부를 결정한다.
7. upstream HMDA publication freshness와 Dagster scheduling/alerting은 후속 capability로 남긴다.

이 경계를 먼저 고정하면 `volume_drop`/`null_spike`에서 만든 approval, candidate staging, dbt verification, structured failure evidence는 상당 부분 재사용하면서도 freshness 특유의 false-green을 피할 수 있다.

### Next Step

다음 RPI는 source implementation이 아니라 **freshness semantics Spec 정리**로 시작하는 것이 적절하다.

최소 planning 질문은 다음 네 가지다.

- `ProfileSnapshot`이 measured freshness와 unavailable freshness를 어떻게 구분할 것인가?
- `DetectionThresholds`의 `freshness_delay_minutes`를 `max_age` 의미로 유지할지 이름까지 바꿀 것인가?
- `RecoveryProposal`에 temporal before/expected state를 추가할지 freshness 전용 approved action을 둘 것인가?
- freshness evaluator의 deterministic defect/recovery/replay acceptance를 어떤 evidence field로 고정할 것인가?

이 질문이 해결된 뒤에만 `freshness_delay` recovery vertical slice를 구현한다.

## RPI Review Summary

1. **Semantics loop** — baseline regression이 일반적인 freshness SLA를 표현하지 못함을 확인하고 age-based model로 수정했다.
2. **Scope loop** — Project Pivot이 upstream publication timestamp를 소유하지 않음을 확인해 source freshness 주장을 Bronze ingestion freshness로 축소했다.
3. **Recovery loop** — `ingested_at`이 content identity에서 제외되므로 기존 before/after identity가 freshness mutation을 구분하지 못한다는 blocker를 추가했다.
4. **KISS/DRY loop** — Dagster, downloader, alerting, production SLO를 제외하고 profile/detection/recovery/evaluation contract만 남겼다.

최종 Review에서 현재 vertical slice 진입 전에 추가로 해결해야 할 material research finding은 남지 않았다. 구현·runtime test는 이 research 범위에서 수행하지 않았다.

## Open Questions

| Question | Why It Matters | Next Step |
| --- | --- | --- |
| `ingested_at`을 HMDA freshness의 canonical clock으로 둘 것인가? | 현재 slice의 의미와 portfolio 설명을 결정한다. | freshness semantics Spec에서 Bronze ingestion freshness로 명시한다. |
| Temporal state를 generic recovery proposal에 넣을 것인가? | 다른 시간 기반 incident로 확장 가능한 공통 boundary를 결정한다. | schema_drift 작업과 섞지 말고 freshness Change에서 최소 contract를 검증한다. |
| 실제 Dynamic HMDA weekly cadence를 evaluation threshold로 사용할 것인가? | synthetic acceptance와 real-source evidence를 구분해야 한다. | synthetic은 deterministic explicit threshold, actual-source validation은 별도 lane으로 둔다. |

[^detector]: `src/project_pivot/reliability/detection/detector.py` — `_detect_freshness_delay()`가 `baseline.freshness_at - current.freshness_at`을 사용한다.
[^detection_spec]: `openspec/specs/reliability-incident-detection/spec.md` — freshness delay를 baseline/current profile 비교로 정의한다.
[^data_operation_request]: `src/project_pivot/data_operations/request.py` — `freshness_column: str | None = None`.
[^profile_builder]: `src/project_pivot/reliability/profiling/profile_snapshot_builder.py` — freshness column이 없거나 값이 없으면 `observed_at`을 fallback하고 metric flag를 기록한다.
[^profile_spec]: `openspec/specs/reliability-profile-snapshots/spec.md` — missing freshness measurement의 observed_at fallback 계약.
[^hmda_domain]: `docs/domains/hmda-data.md` — source download는 out of scope이며 Bronze는 `source_file`, `source_file_name`, `source_year`, `ingested_at`을 추가한다.
[^synthetic]: `src/project_pivot/hmda_data/synthetic/cases.py` — `freshness_delay()`가 오래된 `observed_at` column을 추가한다.
[^content_identity]: `src/project_pivot/hmda_data/ingestion/identity.py` — `_VOLATILE_COLUMNS = {"ingested_at"}`이고 logical content identity에서 ingestion time을 제외한다.
[^recovery_executor]: `src/project_pivot/reliability/recovery/executor.py` — current identity가 expected-after이면 mutation 없이 `already_recovered` / `resume_verification`으로 분기한다.
[^recovery_spec]: `openspec/specs/reliability-recovery-backfill/spec.md` — content identity를 final correctness oracle로 유지하고 incident-specific metric evidence를 별도로 허용한다.
[^architecture]: `docs/ARCHITECTURE.md` — Dagster data plane과 reliability lifecycle/recovery/evaluation 경계를 분리한다.
[^dbt_freshness]: dbt Developer Hub, "Add sources to your DAG" / Source data freshness, https://docs.getdbt.com/docs/build/sources — `max(loaded_at_field)`와 계산 시각, SLA를 이용한 freshness 모델과 timestamp가 없을 때 계산하지 않는 경계를 설명한다. 2026-08-06 갱신본 확인.
[^dbt_job]: dbt Developer Hub, "Source freshness", https://docs.getdbt.com/docs/deploy/source-freshness — freshness SLA와 check frequency를 별도로 설명한다. 2026-08-06 갱신본 확인.
[^hmda_publication]: FFIEC/CFPB HMDA Data Publication, https://ffiec.cfpb.gov/data-publication/ — Dynamic National Loan-Level Dataset은 weekly on Mondays로 갱신된다고 명시한다. 2026-08-15 확인.
