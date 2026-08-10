---
type: research
title: PR #48 이후 Reliability 다음 작업 리서치
description: PR #48의 volume-drop recovery MVP가 마무리된 뒤 어떤 작업을 다음 최소 단위로 진행할지 현재 repository evidence와 후속 위험을 비교한다.
status: "completed"
tags:
  - reliability
  - mvp
  - roadmap
  - null-spike
---

> [!NOTE]
> PR #48이 review와 validation을 통과해 merge되기 전에는 다음 구현을 시작하지 않는 것이 안전하다. 다만 후속 Research는 병렬로 진행할 수 있다. PR #48 이후 첫 substantive RPI 후보는 **`null_spike` recovery vertical slice**가 가장 적합하다. 기존 synthetic defect, detector, impact/remediation, exact approval, partition identity, dbt artifact safety와 reconciliation을 가장 많이 재사용하면서도 column-level quality recovery라는 새 의미를 검증한다. `schema_drift`는 그 다음, `freshness_delay`는 freshness 의미론 정리 뒤, Dagster reliability control-plane은 incident vertical slice 확장 뒤로 미룬다.

## Question

PR #48의 `volume_drop` recovery MVP가 완료된 다음, Project Pivot의 핵심 가치를 가장 적은 새 복잡도로 확장하는 다음 작업은 무엇이어야 하는가?

### Scope

- PR #48 current head와 OpenSpec completion 상태
- `docs/mvp.md`, `docs/vision.md`의 MVP 및 Beyond MVP 경계
- 기존 `null_spike`, `schema_drift`, `freshness_delay` detection/synthetic/remediation surface
- Foundation에 남은 reliability/orchestration risk
- 새 framework나 UI, cloud/production 범위는 제외

### Stop Condition

- PR #48 직후의 필수 정리와 다음 substantive 작업을 분리한다.
- 후보별 재사용 가능성, 새 contract 위험과 프로젝트 가치가 비교된다.
- 다음 RPI 진입점과 defer 대상이 결정된다.

## Evidence Snapshot

- `main@8ddf24184f08c30b292330328fe9062a9e49cc19`
- PR #48 head `85c5ecaf4f70d26f30286f4911ad36e2bcd2f32c`, open, 49 changed files
- PR #48 `tasks.md`: `41/41` 완료
- PR #48 `plan-review.md`: review loop 5, `status: approved`, reported full pytest `162 passed`
- GitHub에 제출된 기존 review는 이전 head에서 Major 3건을 지적했으며, 최신 head 이후의 새 submitted review는 이 조사 시점에 확인되지 않았다.

## Findings

### F1. 지금의 실행 우선순위는 여전히 PR #48의 review closure다

PR #48은 canonical MVP가 요구하는 `volume_drop` detection → approval-bound recovery → data/dbt verification → failure evidence를 직접 구현한다.[^mvp] 최신 PR head의 OpenSpec plan review는 이전 review에서 파생된 source immutability, artifact projection integrity, promotion serialization, reader/writer coherence와 post-mutation dbt failure까지 후속 task로 닫았고 `41/41` 완료를 기록한다.[^pr48_tasks][^pr48_review]

그러나 repository의 GitHub submitted review history는 이전 head에서 발견한 3건 이후 최신 head를 승인한 새 review를 아직 보여주지 않는다. 따라서 다음 source change를 병렬로 열기보다 다음 gate를 먼저 닫는 편이 안전하다.

1. 최신 PR #48 head 재-review
2. focused/full validation evidence 확인
3. unresolved finding이 없을 때 merge 판단

**Implication:** 후속 Research는 병렬 가능하지만 다음 implementation branch는 PR #48 merge 뒤에 시작한다.

### F2. PR #48 merge 직후에는 새 기능보다 Change lifecycle을 먼저 닫는다

PR #48은 새 OpenSpec Change를 포함하고 있으며, `main`에는 완료됐지만 active directory로 남은 runtime-settings/ingestion 관련 Change 4개가 이미 존재한다.[^active_changes] 새 reliability Change를 계속 쌓으면 어떤 delta가 current Spec에 반영됐고 어떤 artifact가 단순히 active 상태로 남은 것인지 해석 비용이 커진다.

PR #48 merge 뒤에는 최소한 해당 Change의 implementation/validation과 current Spec 일관성을 확인한 뒤 archive/sync 여부를 결정해야 한다. 기존 4개 active Change cleanup은 PR #48 archive와 독립적으로 검토할 수 있지만, 새 feature implementation과 섞지 않는다.

**Implication:** `merge → archive/sync 판단 → 다음 RPI`가 가장 낮은 해석 비용을 만든다.

### F3. 다음 substantive vertical slice는 `null_spike`가 가장 적합하다

`null_spike`는 이미 다음 기반을 가진다.

- synthetic defect: 특정 column의 Null 비율을 결정론적으로 높이는 `null_spike(...)`[^hmda]
- detection: baseline/current null rate delta와 target column evidence[^detection]
- remediation: null 관련 quality test suggestion[^remediation]
- PR #48이 추가하는 공통 safety primitive: stable partition identity, exact recovery proposal, approval binding, staged source validation, dbt artifact isolation/promotion, reconciliation[^pr48_tasks]

따라서 새로 풀 핵심 문제는 "안전한 recovery infrastructure" 자체가 아니라 **column-level quality incident가 어떤 candidate와 validation oracle을 요구하는가**다. 이는 `volume_drop`과 다른 의미를 추가하면서도 mutation/artifact safety를 재사용한다.

또한 PR #48의 evaluation composition이 `volume_drop.py`에 구체적으로 존재하므로, 두 번째 incident를 구현하면 어떤 부분이 실제 공통 orchestration이고 어떤 부분이 incident-specific인지 처음으로 근거 있게 판단할 수 있다.[^volume_drop]

**Implication:** generic incident recovery framework를 먼저 만들지 않는다. `null_spike` 두 번째 use case에서 실제 중복이 확인될 때만 공통 부분을 추출한다.

### F4. `schema_drift`는 두 번째 확장 후보지만 `null_spike`보다 새 위험이 크다

`schema_drift` synthetic case와 detector는 이미 존재하지만, 결함 자체가 column type을 변경한다.[^hmda][^detection] 이는 단순 row/content replacement뿐 아니라 raw schema, dbt source contract, model compilation/materialization과 recovery 이후 schema restoration 의미까지 건드릴 수 있다.

PR #48의 partition content identity와 backfill recovery를 그대로 재사용할 수 있는지 먼저 검증해야 하며, 잘못 일반화하면 "content recovery"와 "schema recovery"가 같은 contract인 것처럼 섞일 수 있다.

**Implication:** `null_spike`로 두 번째 vertical slice를 먼저 확보한 뒤 별도 Research로 schema recovery boundary를 정의한다.

### F5. `freshness_delay`는 freshness 의미론 부채를 먼저 해결해야 한다

Foundation readiness는 freshness semantics를 non-gating risk로 명시한다. 현재 profile은 실제 freshness 측정이 없는 경우 `observed_at` fallback을 사용하며, "미측정"과 "관측 시각"의 의미가 분리되지 않았다.[^readiness]

이 상태에서 freshness recovery vertical slice를 만들면 detector/evidence/recovery의 기준 시각 자체가 흔들릴 수 있다. synthetic `freshness_delay`가 존재한다는 사실만으로 recovery contract가 준비된 것은 아니다.[^hmda]

**Implication:** freshness는 `미측정 상태`, source freshness와 observation time의 ownership을 먼저 Research/Spec으로 정리한 뒤 확장한다.

### F6. Dagster reliability control-plane은 다음 단계가 아니다

Architecture는 Dagster를 Bronze → dbt data plane으로 한정하고 reliability lifecycle, approval, recovery와 evaluation을 graph 밖에 둔다.[^architecture][^orchestration] Vision도 Dagster reliability control-plane을 Beyond MVP로 두지만 incident expansion과 함께 후속 후보로만 제시한다.[^vision]

현재 Foundation readiness의 orchestration risk도 실제 dbt-enabled pipeline materialization evidence가 부족한 문제이지, reliability control-plane을 지금 도입해야 한다는 요구는 아니다.[^readiness]

**Implication:** control-plane 확장은 최소 두 incident vertical slice에서 application boundary가 안정된 뒤 검토하는 편이 KISS에 맞다.

### F7. 실제 HMDA 기반 evidence run은 유용하지만 다음 feature와 구분한다

Canonical MVP 완료 조건은 deterministic end-to-end acceptance와 failure evidence다.[^mvp] PR #48은 synthetic fixture를 사용해 이 proof를 반복 가능하게 만드는 방향이다. 실제 HMDA input으로 동일 lifecycle을 실행해 portfolio/demo evidence를 추가하는 것은 가치가 있지만 새 capability requirement는 아니다.

**Implication:** PR #48 merge 후 실제-source reliability run은 optional validation/evidence lane으로 수행할 수 있다. 이것을 `null_spike` implementation과 결합하지 않는다.

## Options

| Candidate | Existing reuse | New contract risk | Value after PR #48 | Decision |
| --- | --- | --- | --- | --- |
| `null_spike` recovery slice | High | Medium | 두 번째 incident로 recovery 일반성 검증 | **Next** |
| `schema_drift` recovery slice | Medium | High | schema-level failure/recovery 확장 | After `null_spike` |
| `freshness_delay` recovery slice | Medium | High | time semantics 확장 | Semantics fix first |
| Dagster reliability control-plane | Low | Very High | 운영 흐름 확장 | Defer |
| Actual-source reliability evidence | High | Low | demo/evidence 강화 | Optional parallel validation |

## Conclusion

PR #48 다음의 권장 순서는 다음과 같다.

1. **PR #48 review/validation을 닫고 merge 여부를 결정한다.**
2. **PR #48 OpenSpec Change의 archive/sync lifecycle을 정리한다.**
3. **`null_spike` recovery vertical slice를 다음 RPI 대상으로 Research → Plan한다.**
4. 두 번째 slice에서 실제 중복이 확인된 뒤에만 `volume_drop`/`null_spike` evaluation과 recovery composition의 공통 추출을 검토한다.
5. 이후 `schema_drift` boundary Research → vertical slice를 진행한다.
6. freshness 의미론을 정리한 뒤 `freshness_delay`를 다룬다.
7. incident application boundary가 안정된 뒤 Dagster reliability control-plane을 검토한다.

이 순서는 새 infrastructure를 선행 구축하지 않고, 이미 구현한 safety primitive를 재사용하면서 incident 의미만 한 단계씩 늘린다.

### Next Step

PR #48 review가 닫히는 동안에는 **`null_spike` recovery vertical slice의 focused Research**를 다음 병렬 작업으로 준비한다. 이 Research는 구현이 아니라 아래 세 질문만 먼저 닫으면 충분하다.

- `null_spike`의 approved recovery action은 기존 partition backfill로 충분한가?
- candidate validation oracle은 expected content identity 외에 target column null-rate 회복을 별도로 요구하는가?
- 두 번째 vertical slice에서 `volume_drop` evaluation composition과 실제로 공유되는 최소 경계는 무엇인가?

## TODO

- [ ] PR #48 최신 head의 review와 validation을 닫는다.
- [ ] Merge 후 PR #48 OpenSpec Change의 sync/archive lifecycle을 정리한다.
- [ ] `null_spike` recovery vertical slice focused Research를 진행한다.
- [ ] `null_spike` 완료 후 실제 중복을 기준으로 공통 abstraction 필요성을 재검토한다.
- [ ] 이후 `schema_drift` → freshness semantics → `freshness_delay` → Dagster reliability control-plane 순서를 검토한다.

## Open Questions

| Question | Why It Matters | Next Step |
| --- | --- | --- |
| Null spike recovery를 partition backfill로 제한할 수 있는가? | 새 mutation type 도입 여부를 결정한다. | clean source 복원 case와 partial-column repair를 비교한다. |
| Null-rate oracle과 content identity의 역할을 어떻게 나눌 것인가? | false-green과 과도한 중복 validation을 방지한다. | detector/profile/recovery contract를 교차검토한다. |
| PR #48 merge 후 actual-source evidence가 필요한가? | MVP 완료와 portfolio evidence를 구분한다. | deterministic MVP proof 완료 후 별도 validation 가치만 평가한다. |

[^mvp]: `docs/mvp.md` — MVP는 `volume_drop` 단일 proof이며 deterministic acceptance와 failure evidence를 완료 조건으로 둔다.
[^vision]: `docs/vision.md` — Beyond MVP로 다른 incident 유형과 Dagster reliability control-plane을 제시한다.
[^architecture]: `docs/ARCHITECTURE.md` — reliability lifecycle과 recovery/evaluation을 Dagster data plane과 분리한다.
[^orchestration]: `docs/domains/orchestration.md` — `pipeline_job` 범위에서 reliability lifecycle, approval, backfill, evaluation을 제외한다.
[^readiness]: `docs/development/foundation/readiness.md` — freshness semantics와 orchestration을 non-gating risk로 기록한다.
[^hmda]: `docs/domains/hmda-data.md` — `null_spike`, `schema_drift`, `freshness_delay` synthetic defect API를 이미 정의한다.
[^detection]: `openspec/specs/reliability-incident-detection/spec.md` — 네 incident의 rule-based detection과 evidence를 정의한다.
[^remediation]: `openspec/specs/reliability-remediation-draft/spec.md` — `null_spike`에 null quality test suggestion을 요구한다.
[^active_changes]: `main:/openspec/changes/` — 조사 시점에 archive 외 `data-operations-centralize-runtime-settings`, `data-platform-require-database-path`, `hmda-data-align-ingestion-contracts`, `orchestration-consume-runtime-settings`가 active directory로 존재한다.
[^pr48_tasks]: PR #48 `openspec/changes/reliability-mvp-volume-drop-vertical-slice/tasks.md` @ `85c5ecaf` — 41/41 tasks 완료 및 review follow-up 7.1–7.16.
[^pr48_review]: PR #48 `openspec/changes/reliability-mvp-volume-drop-vertical-slice/plan-review.md` @ `85c5ecaf` — review loop 5 approved, reported full pytest 162 passed.
[^volume_drop]: PR #48 `src/project_pivot/reliability/evaluation/volume_drop.py` @ `85c5ecaf` — volume-drop-specific deterministic evaluation composition.
