---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Reliability Freshness Delay Semantics
description: Bronze ingestion freshness를 측정 가능한 age contract와 승인된 recovery boundary로 전환한다.
tags:
  - "domain:reliability"
  - "capability:reliability-data-contracts"
  - "capability:reliability-profile-snapshots"
  - "capability:reliability-incident-detection"
  - "capability:reliability-remediation-draft"
  - "capability:data-operations-incident-lifecycle"
  - "capability:hmda-data-ingestion"
  - "capability:hmda-data-synthetic-defects"
  - "capability:reliability-recovery-backfill"
  - "capability:reliability-evaluation-report"
  - "freshness-delay"
  - "post-mvp"
---

> [!NOTE]
> `freshness_delay`를 baseline timestamp regression이 아니라 Bronze partition의 실제 ingestion age로 판정하고, content identity와 별개의 freshness state를 approval, mutation, validation과 replay에 결합한다.

## Overview

| Why | What | Capabilities |
| --- | --- | --- |
| 현재 fallback profile은 측정 불가능을 fresh로 표현하고 content identity는 `ingested_at` 변화를 구분하지 못한다. | Nullable freshness measurement, age-based detection, temporal compare-and-replace와 deterministic recovery evaluation을 정의한다. | `reliability-profile-snapshots`, `reliability-incident-detection`, `reliability-recovery-backfill`, `reliability-evaluation-report` 외 관련 contract |

> [!IMPORTANT]
> 첫 vertical slice의 freshness clock은 대상 Bronze partition의 `max(ingested_at)`이다. Upstream HMDA publication freshness를 의미하지 않는다.

> [!IMPORTANT]
> 이 Change는 완료된 volume-drop MVP 이후의 capability extension이다. `docs/development/mvp`의 scope, milestone과 status를 변경하거나 다시 열지 않는다.

> [!CAUTION]
> `ProfileSnapshot` serialization, `DetectionThresholds`, `RecoveryProposal`과 HMDA synthetic public API에 호환되지 않는 변경이 포함된다.

## Why

현재 detector는 `baseline.freshness_at - current.freshness_at`을 사용하므로 timestamp가 멈춘 채 오래된 partition을 탐지하지 못한다. Freshness column이 없으면 profile은 `observed_at`을 fallback으로 기록하여 측정 불가능한 상태를 방금 갱신된 상태처럼 표현한다.

HMDA Bronze의 `ingested_at`은 logical content identity에서 의도적으로 제외된다. 따라서 동일 content의 오래된 partition과 다시 적재된 partition은 content identity만으로 구분할 수 없고, 현재 replay 분기는 stale target을 이미 복구된 상태로 오판할 수 있다. 측정 상태, age threshold와 temporal target state를 canonical contract로 정리한 뒤에만 freshness recovery를 안전하게 구현할 수 있다.

## What Changes

- **Add:** Measured/unavailable freshness 상태, Bronze ingestion age evidence, freshness recovery binding, transaction 내부 temporal target gate와 deterministic freshness recovery evaluation을 추가한다.
- **Modify:** Detection을 `observed_at - freshness_at >= max_age`로 전환하고 lifecycle threshold 전달, remediation wording, recovery reconciliation과 result evidence를 freshness semantics에 맞춘다.
- **Remove:** Source HMDA row에 synthetic `observed_at` column을 추가하는 `freshness_delay()` API와 해당 contract를 제거한다.
- **BREAKING:** `freshness_at`은 nullable이 되고 explicit status를 요구한다. `freshness_delay_minutes`는 `freshness_max_age_minutes`로 교체하며 compatibility alias를 제공하지 않는다. `RecoveryProposal`은 `incident_type`을 요구한다.

## Boundaries

| In Scope | Out of Scope |
| --- | --- |
| Post-MVP freshness capability extension | Current volume-drop MVP scope, milestone과 status 변경 |
| Bronze `max(ingested_at)` measurement와 unavailable 상태 | Upstream HMDA publication timestamp와 source download |
| Age-based `freshness_delay` detection과 evidence | Dagster scheduling, polling, alerting과 production monitoring |
| Content + freshness approval, atomic target gate와 replay | Generic temporal recovery framework와 schema-drift recovery |
| Disposable DuckDB 기반 deterministic defect/recovery evaluation | Actual-source weekly cadence validation과 production SLO |

## Capabilities

### Modified Capabilities

#### `reliability-data-contracts`

- `ProfileSnapshot`이 nullable freshness timestamp와 explicit measurement status를 교환하도록 변경한다.

#### `reliability-profile-snapshots`

- 실제 freshness timestamp가 없으면 fallback을 만들지 않고 unavailable measurement를 반환하도록 변경한다.

#### `reliability-incident-detection`

- Current observation의 Bronze ingestion age를 explicit max-age threshold와 비교하며 unavailable measurement를 freshness incident로 판정하지 않도록 변경한다.

#### `reliability-remediation-draft`

- Freshness action이 upstream publication을 주장하지 않고 Bronze ingestion과 partition reload 검토를 가리키도록 변경한다.

#### `data-operations-incident-lifecycle`

- Caller가 명시한 detection thresholds를 current profile detection에 전달할 수 있도록 변경한다.

#### `hmda-data-ingestion`

- Content identity와 expected `max(ingested_at)`을 같은 partition replacement transaction에서 확인할 수 있도록 변경한다.

#### `hmda-data-synthetic-defects`

- Source schema를 바꾸는 기존 freshness case를 제거하고 temporal defect 책임을 isolated reliability evaluation으로 이전한다.

#### `reliability-recovery-backfill`

- Freshness-specific approved before/expected after state를 proposal, candidate staging, mutation gate, validation과 replay에 결합한다.

#### `reliability-evaluation-report`

- Controlled Bronze ingestion delay, approved recovery, replay와 freshness evidence 보존을 검증하는 vertical-slice evaluation을 추가한다.

## Impact

| Area | Impact |
| --- | --- |
| Code / Systems | Profile, detector, lifecycle, remediation, ingestion, recovery와 incident-specific evaluator가 변경된다. |
| Data / Contracts | `freshness_at`, measurement status, max-age evidence와 freshness recovery state의 serialization이 바뀐다. |
| Interfaces / APIs | `DetectionThresholds`, `RecoveryProposal`, `BackfillValidationResult`, lifecycle threshold input과 public evaluation export가 변경된다. |
| Operations / Dependencies | 새 외부 dependency나 orchestration 경계 변경은 없다. Evaluation database는 계속 disposable local path만 사용한다. |

## Appendix

### Alternatives

| Alternative | Why Rejected |
| --- | --- |
| Baseline freshness regression 유지 | 멈춘 timestamp의 실제 staleness를 탐지하지 못한다. |
| Upstream publication freshness | 현재 source acquisition boundary가 publication timestamp를 보존하지 않는다. |
| 범용 temporal recovery state | 첫 time-based incident에 비해 contract 범위가 크고 schema-drift work와 불필요하게 결합된다. |
| Freshness 전용 proposal/executor | Existing exact approval과 partition recovery safety gate를 중복한다. |

### Trade-offs

| Choice | Gain | Cost |
| --- | --- | --- |
| Nullable timestamp + explicit status | 측정 불가능과 fresh를 분리한다. | 기존 fixture와 serialized consumer를 갱신해야 한다. |
| Freshness binding on existing proposal | 기존 approval과 mutation safety를 재사용한다. | Generic proposal에 incident-specific optional state가 추가된다. |
| Exact candidate timestamp + age acceptance | Candidate immutability와 replay 판정을 함께 검증한다. | Temporal metadata staging과 transaction gate가 추가된다. |
