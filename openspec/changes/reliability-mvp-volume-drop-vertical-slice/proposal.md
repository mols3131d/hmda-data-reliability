---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Reliability MVP Volume-Drop Vertical Slice
description: volume_drop detection부터 승인된 recovery와 재검증까지의 최소 안전 vertical slice를 정의한다.
tags:
  - "domain:reliability"
  - "capability:reliability-recovery-backfill"
  - "capability:data-operations-stage-execution"
  - "capability:data-operations-incident-lifecycle"
  - "capability:hmda-data-ingestion"
  - "capability:reliability-evaluation-report"
  - "mvp"
  - "volume-drop"
---

> [!NOTE]
> 첫 reliability MVP를 deterministic HMDA `volume_drop` case 하나로 제한하고, read-only analysis 이후 isolated candidate validation, exact proposal approval, stale-state 차단, approved recovery와 post-recovery verification을 하나의 재현 가능한 흐름으로 연결한다.

## Overview

| Why | What | Capabilities |
| --- | --- | --- |
| 승인된 recovery라는 핵심 가치를 가장 작은 end-to-end 흐름으로 증명해야 한다. | `volume_drop`의 candidate validation, bound approval, content-level recovery, dbt evidence 보존과 reconciliation 계약을 추가한다. | `reliability-recovery-backfill`, `data-operations-stage-execution`, `data-operations-incident-lifecycle`, `hmda-data-ingestion`, `reliability-evaluation-report` |

> [!IMPORTANT]
> Read-only incident lifecycle과 approval 이후 recovery 경계는 유지한다. Apply 전에는 최신 `main`에서 관련 baseline을 재검증하고 완료됐지만 active인 관련 Change를 archive/sync하거나 delta 비중첩을 확인해야 한다.

## Why

현재 시스템은 `volume_drop`을 탐지하고 remediation draft를 만들며 승인된 partition backfill을 실행할 수 있지만, approval이 검증된 candidate와 target state에 결합되지 않는다. Recovery correctness도 row count 중심이고 candidate/recovery dbt failure가 shared artifact를 파괴할 수 있으며 partition mutation 이후 실패를 구분하는 reconciliation 계약이 없다. 이 간극을 그대로 두면 승인 시점의 evidence와 실제 mutation 대상이 달라도 실행될 수 있고 실패한 recovery를 안전하게 재개하거나 재현하기 어렵다.

## What Changes

- **Add:** deterministic clean/`volume_drop` synthetic case를 detection, impact, candidate validation, approval, recovery와 verification까지 실행하고 evidence로 평가한다.
- **Modify:** recovery approval을 incident, target partition, validated candidate, validation evidence, approved target state와 target mutation action에 결합한다.
- **Modify:** 첫 target mutation 직전에 target state를 재확인하고 승인된 before/after state에 따른 reconciliation 결과를 제공한다.
- **Modify:** partition recovery의 최종 oracle로 duplicate semantics를 보존하는 stable content identity를 사용한다.
- **Modify:** candidate dbt 실행을 current target과 shared current artifact에서 격리하고, target dbt failure 시 prior last-known-good artifact와 failed-run evidence를 보존한다.
- **Modify:** post-mutation verification failure를 성공과 구분하고 downstream verification을 안전하게 재개할 수 있게 한다.

## Boundaries

| In Scope | Out of Scope |
| --- | --- |
| `volume_drop` 단일 synthetic vertical slice와 clean baseline | 다른 incident type의 end-to-end recovery |
| isolated candidate validation과 exact proposal approval | approval UI, external identity provider, security-grade signature와 RBAC |
| target-state freshness, content identity와 local single-writer serialization | distributed lock, cloud deployment와 concurrent multi-writer architecture |
| dbt run isolation, last-known-good promotion과 failed-run evidence | 장기 artifact retention service와 external catalog |
| mutation-aware failure와 reconciliation | 여러 system에 걸친 rollback 보장 |
| 직접 application API와 deterministic acceptance | Dagster job, schedule, sensor 또는 운영 UI |

## Capabilities

### Modified Capabilities

#### `reliability-recovery-backfill`

- Exact recovery proposal에 결합된 approval, stale-state 차단, content-level post-recovery validation과 mutation-aware reconciliation을 보장한다.

#### `data-operations-stage-execution`

- Candidate와 target dbt run을 격리하고 성공한 target run만 current artifact로 승격하며 실패 evidence와 prior last-known-good artifact를 보존한다.

#### `data-operations-incident-lifecycle`

- `volume_drop` case에서 recovery proposal이 요구하는 target, candidate와 evidence identity를 read-only 결과로 전달할 수 있게 한다.

#### `hmda-data-ingestion`

- Recovery가 비교할 stable partition content identity를 제공하고 target-state 확인과 partition replacement 사이의 local serialization 경계를 보장한다.

#### `reliability-evaluation-report`

- Clean baseline과 `volume_drop` vertical slice의 detection, recovery와 verification 결과를 deterministic acceptance evidence로 집계한다.

## Impact

| Area | Impact |
| --- | --- |
| Code / Systems | reliability approval/recovery/evaluation, HMDA partition ingestion, dbt stage runner와 application composition이 변경된다. |
| Data / Contracts | Approval과 recovery result에 proposal/evidence/state identity가 추가되고 partition content identity 계약이 생긴다. |
| Interfaces / APIs | 기존 read-only lifecycle은 유지하며 별도 candidate validation과 approved recovery 호출 surface가 확장된다. |
| Operations / Dependencies | local DuckDB와 filesystem artifact workspace만 사용하며 새로운 external dependency는 추가하지 않는다. |

## Appendix

### Alternatives

| Alternative | Why Rejected |
| --- | --- |
| 여러 incident recovery를 함께 구현 | Incident별 oracle과 remediation 차이로 첫 slice의 범위와 failure surface가 커진다. |
| Dagster control-plane부터 구현 | Core reliability contract보다 orchestration이 앞서고 recovery safety를 증명하지 못한다. |
| Detection과 report까지만 구현 | 승인된 recovery라는 프로젝트 핵심 가치를 end-to-end로 증명하지 못한다. |

### Trade-offs

| Choice | Gain | Cost |
| --- | --- | --- |
| Local single-writer serialization | 최소 구현으로 stale approval과 mutation race를 차단한다. | 분산 writer와 높은 동시성은 지원하지 않는다. |
| Content identity 기반 reconciliation | 동일 row count의 semantic drift와 unsafe replay를 검출한다. | Canonical projection 계산 비용과 contract 관리가 추가된다. |
