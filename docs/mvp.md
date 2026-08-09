# MVP: Volume-Drop Recovery Proof

> **목표:** 하나의 `volume_drop` incident를 탐지부터 승인된 recovery와 재검증까지 연결해 Project Pivot의 evidence-first, human-controlled Data Reliability 가치를 end-to-end로 증명한다.

MVP는 기능 수를 늘리는 단계가 아니다. 결정론적으로 재현 가능한 하나의 failure를 안전하게 복구하고, 그 판단과 결과를 evidence로 설명할 수 있음을 증명한다.

## Outcome

MVP가 완료되면 다음 흐름을 하나의 deterministic acceptance case로 재현할 수 있어야 한다.

```text
clean baseline
→ controlled volume_drop
→ incident + impact + remediation draft
→ isolated candidate validation
→ proposal-bound human approval
→ approved recovery
→ data + dbt verification
→ run evidence
```

성공 기준은 다음과 같다.

- clean baseline에서는 incident와 remediation draft가 생성되지 않는다.
- controlled `volume_drop`은 기대한 evidence와 downstream impact를 가진 incident와 remediation draft를 생성한다.
- candidate validation은 target database와 current dbt artifact에서 격리되며, invalid candidate는 approval/recovery에 진입하지 못한다.
- 검증된 recovery proposal과 target state에 결합된 approval만 target mutation을 허용하며, incomplete approval 또는 stale target은 mutation 전에 차단된다.
- recovery 이후 partition은 row count가 아니라 stable content 기준으로 expected state와 일치하고 `volume_drop` incident가 해소되며 downstream dbt verification이 통과한다.
- 실패한 recovery dbt 실행은 prior last-known-good artifact를 파괴하지 않고 failure evidence를 남긴다.
- target mutation 이후 실패는 성공으로 보고되지 않으며, 현재 state를 다시 확인한 뒤 recovery verification을 재개하거나 새 approval을 요구한다.
- recovery 재실행은 duplicate 또는 semantic drift를 만들지 않는다.

세부 requirement와 behavior는 OpenSpec change가 소유하고, 이를 검증하는 scenario와 oracle은 test에서 구체화한다.

## Scope

**In scope**

- HMDA local pipeline의 `volume_drop` 단일 incident
- detection → impact → remediation draft → candidate validation → approval → recovery → verification
- recovery correctness에 필요한 partition identity, dbt evidence 보존과 failure/reconciliation behavior

**Out of scope**

- `null_spike`, `schema_drift`, `freshness_delay` recovery 확장
- Dagster reliability control-plane과 approval UI
- cloud deployment, production SLO, security-grade authorization
- 승인 없는 자동 recovery와 범용 RCA

## Delivery Gate

- **Planning:** 시작할 수 있다.
- **Apply:** 최신 `main`에서 MVP가 의존하는 baseline을 다시 검증하고, 겹치는 active OpenSpec change와 sequencing을 확인한다.
- **Done:** 위 Outcome을 deterministic end-to-end acceptance로 통과하고 실패 경로의 evidence까지 확인한다.

## References

- [`vision.md`](vision.md): 프로젝트 장기 비전과 원칙
- [`ARCHITECTURE.md`](ARCHITECTURE.md): 시스템 및 execution boundary
- [`domains/reliability.md`](domains/reliability.md): 현재 reliability domain contract
- [`../inbox/archive/2026-08-08/reliability-mvp-volume-drop-vertical-slice.md`](../inbox/archive/2026-08-08/reliability-mvp-volume-drop-vertical-slice.md): MVP 범위와 safety behavior를 결정한 research
