---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Reliability Null-Spike Recovery Vertical Slice
description: 기존 승인 기반 partition recovery를 재사용해 null-spike 탐지부터 품질 회복 검증까지 연결한다.
tags:
  - "domain:reliability"
  - "capability:reliability-recovery-backfill"
  - "capability:reliability-evaluation-report"
  - "null-spike"
---

> [!NOTE]
> Controlled `null_spike`를 서로 다른 isolated disposable target, clean과 candidate database에서 탐지하고 clean partition candidate를 외부 승인에 결합해 기존 full-partition backfill로 복구한 뒤, stable content identity와 target column null-rate 및 incident 해소를 함께 검증한다. 새 mutation type이나 범용 recovery framework는 추가하지 않는다.

## Overview

| Why | What | Capabilities |
| --- | --- | --- |
| `volume_drop` 이후 두 번째 incident에서 recovery primitive의 재사용 가능성과 incident-specific acceptance를 검증해야 한다. | 기존 approved partition backfill을 재사용한 deterministic `null_spike` recovery evaluation을 추가한다. | `reliability-recovery-backfill`, `reliability-evaluation-report` |

> [!IMPORTANT]
> Read-only lifecycle과 approval 이후 별도 recovery API 경계를 유지한다. Recovery executor의 `validation_passed`는 stable content identity oracle로 유지하고, null-rate 회복은 evaluation이 소유한다.

## Why

현재 `null_spike` synthetic defect, detection과 remediation draft는 존재하지만 approved recovery와 post-recovery quality acceptance까지 연결된 vertical slice는 없다. 기존 recovery executor는 incident type과 무관하게 검증된 candidate로 partition을 교체하고 expected content identity와 actual target을 비교할 수 있으므로 새 column-level mutation API는 필요하지 않다.

Expected recovery state는 original clean fixture에서 유도해야 한다. Residual null을 가진 candidate는 clean expected identity와 다르므로 approval과 mutation 전에 차단하고, 성공한 recovery에서는 target column null-rate와 post-recovery incident 해소를 profile/evaluation evidence로 명시해야 한다.

## What Changes

- **Modify:** Controlled single-column `null_spike` case가 clean candidate, exact approval과 기존 partition overwrite를 사용해 recovery를 실행할 수 있도록 한다.
- **Modify:** Existing database 또는 서로 alias된 target/clean/candidate path는 workspace directory와 synthetic artifact 생성을 포함한 모든 side effect 전에 하나의 preflight에서 거부하고 distinct evaluation-owned disposable database만 허용한다.
- **Modify:** `null_spike` evaluation은 candidate가 clean fixture expected identity와 null-rate에 일치하는지 mutation 전에 검증하고, 성공 후 target column null-rate 회복과 incident 해소를 evidence로 확인한다.
- **Modify:** Candidate validation, approval, recovery, replay와 downstream dbt verification의 domain/validation failure를 기존 safety evidence 형식으로 집계한다.

## Boundaries

| In Scope | Out of Scope |
| --- | --- |
| Single target column의 deterministic `null_spike` | Multi-column 또는 multi-incident recovery proposal |
| Distinct new disposable target/clean/candidate database에서의 synthetic evaluation | Existing operational database 직접 평가 또는 database path alias |
| Clean source를 사용한 full-partition approved backfill | Column-level partial repair와 새 mutation type |
| Null-rate 및 incident-resolution evaluation oracle | Recovery executor의 content-identity oracle 변경 |
| Existing recovery/evaluation primitive 재사용 | Generic vertical-slice framework 또는 base class |
| Candidate와 target dbt verification, replay evidence | Remediation draft의 backfill recommendation 변경 |
| Read-only lifecycle와 외부 approval 경계 유지 | Dagster control-plane, approval UI와 audit integration |

## Capabilities

### Modified Capabilities

#### `reliability-recovery-backfill`

- Exact approved clean candidate를 기존 partition overwrite로 적용해 `null_spike` content를 복원할 수 있어야 한다.
- Recovery result는 stable content identity와 post-backfill profile snapshot을 제공하되 incident-specific null-rate pass/fail을 mutation oracle에 결합하지 않는다.

#### `reliability-evaluation-report`

- Deterministic clean/`null_spike` case의 detection, candidate validation, approval, recovery, replay와 downstream verification을 집계해야 한다.
- Recovery acceptance는 target column null-rate 회복과 post-recovery `null_spike` 해소를 포함해야 한다.
- Clean fixture identity 또는 null-rate와 다른 candidate를 approval과 mutation 전에 성공으로 판정해서는 안 된다.

## Impact

| Area | Impact |
| --- | --- |
| Code / Systems | Reliability evaluation에 incident-specific null-spike runner와 result가 추가된다. |
| Data / Contracts | 기존 partition identity와 profile snapshot contract를 재사용하고 null-rate evidence를 evaluation에 추가한다. |
| Interfaces / APIs | Reliability package가 `evaluate_null_spike_vertical_slice`를 공개한다. |
| Operations / Dependencies | 새 dependency 없이 local DuckDB, dbt와 기존 approval callback을 사용한다. |

## Appendix

### Alternatives

| Alternative | Why Rejected |
| --- | --- |
| Column-level null repair API | Clean partition overwrite로 복구 가능하며 새 mutation semantics와 approval action이 불필요하다. |
| Null-rate를 recovery `validation_passed`에 결합 | Detection threshold와 incident semantics가 mutation executor에 침투한다. |
| Generic recovery/evaluation framework 선행 | 두 incident의 실제 차이를 확인하기 전에 volume-drop assumptions를 공통 계약으로 고정할 위험이 있다. |
| Remediation draft에 backfill action 추가 | Recovery feasibility와 독립적인 product decision이며 이번 vertical slice의 최소 범위를 넓힌다. |

### Trade-offs

| Choice | Gain | Cost |
| --- | --- | --- |
| Incident-specific evaluator | 기존 primitive를 그대로 재사용하고 null-spike semantics를 명확히 유지한다. | Volume-drop evaluator와 일부 composition 중복이 남는다. |
| Full-partition recovery | Existing approval, identity와 reconciliation safety를 재사용한다. | Partial column repair보다 mutation 범위가 크다. |
| Evaluation-owned null-rate oracle | Recovery executor의 범용 content contract를 유지한다. | Recovery result 하나만으로 incident 해소를 판정할 수 없다. |
