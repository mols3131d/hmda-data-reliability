---
type: research
title: PR #48 이후 Reliability 다음 작업 리서치
description: merge 완료된 PR #48의 volume-drop recovery MVP를 기준으로 다음 최소 Reliability 작업 순서와 후속 위험을 현재 repository evidence로 갱신한다.
status: "completed"
tags:
  - reliability
  - mvp
  - roadmap
  - null-spike
---

> [!NOTE]
> 2026-08-11 기준 PR #48은 `main`에 merge되었고 OpenSpec tasks는 `49/49`, Plan Review는 loop 8 `approved` 상태다. 따라서 현재 첫 gate는 PR #48 review closure가 아니라 **해당 OpenSpec Change의 sync/archive lifecycle 정리**다. 그 다음 실질적 RPI 후보는 **`null_spike` recovery vertical slice**가 가장 적합하다. `schema_drift`는 그 다음, `freshness_delay`는 freshness 의미론 정리 뒤, Dagster reliability control-plane은 incident vertical slice 확장 뒤로 미룬다.

## Question

`volume_drop` recovery MVP가 `main`에 merge된 현재, Project Pivot의 핵심 가치를 가장 적은 새 복잡도로 확장하는 다음 작업은 무엇이어야 하는가?

### Scope

- 현재 `main`과 merge된 PR #48의 최종 상태
- PR #48 OpenSpec Change lifecycle
- `docs/development/mvp/README.md`, `docs/vision.md`의 MVP 및 Beyond MVP 경계
- 기존 `null_spike`, `schema_drift`, `freshness_delay` detection/synthetic/remediation surface
- 새 framework, UI, cloud/production 범위는 제외

### Stop Condition

- PR #48 이후 즉시 정리할 작업과 다음 기능 작업을 분리한다.
- 후보별 재사용 가능성, 새 contract 위험과 프로젝트 가치를 비교한다.
- 다음 RPI 진입점과 defer 대상을 결정한다.

## Evidence Snapshot

- `main@02aa81fbd9e3ca55cfb3b3eacddfbea70db4fd80`
- PR #48: merged, final head `736732b7940b90486185dc93200161f8ae09a542`
- PR #48 `tasks.md`: `49/49` 완료, 최종 full default pytest evidence `177 passed`[^pr48_tasks]
- PR #48 `plan-review.md`: review loop 8, `status: approved`[^pr48_review]
- `openspec/changes/reliability-mvp-volume-drop-vertical-slice/`는 아직 active directory에 존재한다.[^active_changes]

## Findings

### F1. 지금의 실행 우선순위는 PR #48 OpenSpec lifecycle 정리다

PR #48은 merge되어 canonical MVP의 `volume_drop` detection → approval-bound recovery → data/dbt verification → failure evidence 구현을 `main`에 반영했다.[^mvp][^pr48]

그러나 해당 OpenSpec Change는 아직 active directory에 남아 있다. 새 reliability Change를 바로 추가하면 current Spec에 반영된 delta와 완료됐지만 active인 artifact의 구분 비용이 커진다.

**Implication:** 다음 기능 branch보다 먼저 PR #48 Change의 current Spec 일관성을 확인하고 sync/archive 여부를 결정한다.

### F2. 다음 실질적 vertical slice는 `null_spike`가 가장 적합하다

`null_spike`는 이미 다음 기반을 가진다.

- synthetic defect: 특정 column의 Null 비율을 결정론적으로 높이는 `null_spike(...)`[^hmda]
- detection: baseline/current null rate delta와 target column evidence[^detection]
- remediation: null 관련 quality test suggestion[^remediation]
- PR #48이 추가한 공통 safety primitive: stable partition identity, exact recovery proposal, approval binding, staged source validation, dbt artifact isolation/promotion, reconciliation[^pr48_tasks]

따라서 새 핵심 문제는 recovery infrastructure 자체가 아니라 **column-level quality incident가 어떤 candidate와 validation oracle을 요구하는가**다. `volume_drop`과 다른 의미를 추가하면서 기존 safety primitive를 가장 많이 재사용할 수 있다.

**Implication:** OpenSpec lifecycle 정리 후 `null_spike` focused Research → Plan을 다음 RPI로 진행한다.

### F3. 두 번째 incident 전에 generic recovery framework를 만들지 않는다

현재 recovery/evaluation composition은 `volume_drop`이라는 첫 실제 use case에서 만들어졌다. 이 시점에 공통 framework를 먼저 추출하면 incident-specific 동작을 공통 계약으로 잘못 일반화할 위험이 있다.

`null_spike`를 두 번째 vertical slice로 구현하면 어떤 부분이 실제 공통 orchestration이고 어떤 부분이 incident-specific인지 비교할 근거가 생긴다.

**Implication:** `volume_drop`과 `null_spike`에서 실제 중복이 확인된 뒤에만 공통 abstraction을 검토한다.

### F4. `schema_drift`는 `null_spike` 다음이 적합하다

`schema_drift` synthetic case와 detector는 이미 존재하지만 결함 자체가 column type을 변경한다.[^hmda][^detection] 이는 content replacement뿐 아니라 raw schema, dbt source contract, model compilation/materialization과 recovery 이후 schema restoration 의미까지 건드릴 수 있다.

**Implication:** `null_spike`로 두 번째 content-quality recovery를 확보한 뒤 별도 Research에서 schema recovery boundary를 먼저 정의한다.

### F5. `freshness_delay`는 freshness 의미론을 먼저 정리해야 한다

현재 canonical profile Spec은 freshness 값을 측정할 수 없으면 `observed_at`을 `freshness_at`으로 fallback하도록 요구한다.[^profile] fallback 여부를 metric으로 식별할 수 있지만, 실제 source freshness와 observation time을 같은 `freshness_at` field로 표현한다.

이 상태에서 freshness recovery까지 확장하면 detector/evidence/recovery의 시간 기준을 추가로 해석해야 한다.

**Implication:** `freshness_delay` vertical slice 전에 미측정 상태와 source freshness/observation time ownership을 Research/Spec에서 정리한다.

### F6. Dagster reliability control-plane은 아직 다음 단계가 아니다

Architecture는 Dagster `pipeline_job`을 Bronze → dbt data plane으로 한정하고 reliability lifecycle, approval, recovery와 evaluation을 별도 경계로 둔다.[^architecture][^orchestration] Vision도 다른 incident 유형과 Dagster reliability control-plane을 Beyond MVP로 둔다.[^vision]

**Implication:** 최소 두 incident vertical slice에서 application boundary가 안정된 뒤 control-plane 확장을 검토한다.

### F7. 실제 HMDA 기반 evidence run은 별도 validation lane으로 둔다

Canonical MVP 완료 조건은 deterministic end-to-end acceptance와 failure evidence다.[^mvp] 실제 HMDA input으로 같은 lifecycle을 실행하는 것은 portfolio/demo evidence를 강화하지만 새 capability requirement는 아니다.

**Implication:** actual-source run은 `null_spike` implementation과 결합하지 않고 optional validation으로 분리한다.

## Options

| Candidate | Existing reuse | New contract risk | Value after PR #48 | Decision |
| --- | --- | --- | --- | --- |
| PR #48 OpenSpec lifecycle | High | Low | 완료 Change와 current Spec 정리 | **Now** |
| `null_spike` recovery slice | High | Medium | 두 번째 incident로 recovery 일반성 검증 | **Next** |
| `schema_drift` recovery slice | Medium | High | schema-level failure/recovery 확장 | After `null_spike` |
| `freshness_delay` recovery slice | Medium | High | time semantics 확장 | Semantics first |
| Dagster reliability control-plane | Low | Very High | 운영 흐름 확장 | Defer |
| Actual-source reliability evidence | High | Low | demo/evidence 강화 | Optional |

## Conclusion

현재 권장 순서는 다음과 같다.

1. **PR #48 OpenSpec Change의 current Spec 일관성을 확인하고 sync/archive lifecycle을 정리한다.**
2. **`null_spike` recovery vertical slice를 다음 RPI 대상으로 focused Research → Plan한다.**
3. 두 번째 slice에서 실제 중복이 확인된 뒤에만 `volume_drop`/`null_spike` recovery/evaluation의 공통 추출을 검토한다.
4. 이후 `schema_drift` boundary Research → vertical slice를 진행한다.
5. freshness 의미론을 정리한 뒤 `freshness_delay`를 다룬다.
6. incident application boundary가 안정된 뒤 Dagster reliability control-plane을 검토한다.

이 순서는 새 infrastructure를 선행 구축하지 않고 이미 구현된 safety primitive를 재사용하면서 incident 의미를 한 단계씩 확장한다.

### Next Step

**PR #48 OpenSpec lifecycle을 먼저 닫은 뒤 `null_spike` focused Research를 시작한다.** Research에서는 구현을 시작하기 전에 아래 세 질문만 우선 해결하면 충분하다.

- `null_spike`의 approved recovery action은 기존 partition backfill로 충분한가?
- candidate validation oracle은 expected content identity 외에 target column null-rate 회복을 별도로 요구하는가?
- 두 번째 vertical slice에서 `volume_drop` evaluation composition과 실제로 공유되는 최소 경계는 무엇인가?

## TODO

- [x] PR #48 review/validation과 merge를 완료한다.
- [ ] PR #48 OpenSpec Change의 sync/archive lifecycle을 정리한다.
- [ ] `null_spike` recovery vertical slice focused Research를 진행한다.
- [ ] `null_spike` 완료 후 실제 중복을 기준으로 공통 abstraction 필요성을 재검토한다.
- [ ] 이후 `schema_drift` → freshness semantics → `freshness_delay` → Dagster reliability control-plane 순서를 검토한다.

## Open Questions

| Question | Why It Matters | Next Step |
| --- | --- | --- |
| Null spike recovery를 partition backfill로 제한할 수 있는가? | 새 mutation type 도입 여부를 결정한다. | clean source 복원과 partial-column repair를 비교한다. |
| Null-rate oracle과 content identity의 역할을 어떻게 나눌 것인가? | false-green과 중복 validation을 방지한다. | detector/profile/recovery contract를 교차검토한다. |
| Actual-source evidence가 지금 필요한가? | MVP 완료와 portfolio evidence를 구분한다. | 별도 validation 가치만 평가한다. |

[^mvp]: `docs/development/mvp/README.md` — MVP는 `volume_drop` 단일 proof이며 deterministic acceptance와 failure evidence를 완료 조건으로 둔다.
[^vision]: `docs/vision.md` — Beyond MVP로 다른 incident 유형과 Dagster reliability control-plane을 제시한다.
[^architecture]: `docs/ARCHITECTURE.md` — reliability lifecycle과 recovery/evaluation을 Dagster data plane과 분리한다.
[^orchestration]: `docs/domains/orchestration.md` — `pipeline_job` 범위에서 reliability lifecycle, approval, backfill, evaluation을 제외한다.
[^hmda]: `docs/domains/hmda-data.md` — `null_spike`, `schema_drift`, `freshness_delay` synthetic defect API를 정의한다.
[^profile]: `openspec/specs/reliability-profile-snapshots/spec.md` — freshness 미측정 시 `observed_at` fallback과 fallback metric을 정의한다.
[^detection]: `openspec/specs/reliability-incident-detection/spec.md` — 네 incident의 rule-based detection과 evidence를 정의한다.
[^remediation]: `openspec/specs/reliability-remediation-draft/spec.md` — `null_spike`에 null quality test suggestion을 요구한다.
[^active_changes]: `main:/openspec/changes/` — PR #48 merge 후에도 `reliability-mvp-volume-drop-vertical-slice`와 기존 runtime-settings/ingestion 관련 Change가 active directory에 존재한다.
[^pr48]: PR #48 — `736732b7940b90486185dc93200161f8ae09a542`가 merge commit `02aa81fbd9e3ca55cfb3b3eacddfbea70db4fd80`으로 `main`에 반영됐다.
[^pr48_tasks]: `openspec/changes/reliability-mvp-volume-drop-vertical-slice/tasks.md` @ `main@02aa81fb` — `49/49` 완료, 최종 full default pytest evidence `177 passed`.
[^pr48_review]: `openspec/changes/reliability-mvp-volume-drop-vertical-slice/plan-review.md` @ `main@02aa81fb` — review loop 8, `status: approved`.
