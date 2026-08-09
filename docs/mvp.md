# MVP: Volume-Drop Recovery Proof

> **목표:** 하나의 `volume_drop` incident를 탐지부터 승인된 recovery와 재검증까지 연결해 Project Pivot의 evidence-first, human-controlled Data Reliability 가치를 end-to-end로 증명한다.

MVP는 기능 범위를 넓히는 단계가 아니다. 결정론적으로 재현 가능한 하나의 failure를 안전하게 복구하고, 판단과 결과를 evidence로 설명할 수 있음을 증명한다.

## Proof

```text
clean baseline
→ controlled volume_drop
→ incident + impact + remediation draft
→ isolated candidate validation
→ human approval bound to recovery proposal
→ approved recovery
→ data + dbt verification
→ run evidence
```

MVP는 다음을 증명해야 한다.

- clean baseline은 incident와 remediation draft를 만들지 않고, controlled `volume_drop`은 evidence·downstream impact·remediation draft를 만든다.
- candidate validation은 current target과 shared current dbt artifact를 변경하지 않으며, 검증된 recovery proposal과 변하지 않은 target state에 결합된 approval만 target mutation을 허용한다.
- recovery는 expected stable partition content를 복원하고 incident를 해소하며 downstream dbt verification을 통과한다. 실패한 validation이나 recovery는 prior last-known-good dbt artifact를 파괴하지 않는다.
- failure와 retry 결과는 evidence로 남고 현재 state에 맞게 reconciliation되며 duplicate 또는 semantic drift를 만들지 않는다.

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

## Entry And Done

OpenSpec planning은 이 목표에서 시작할 수 있다. 구현 전에는 현재 의존 baseline을 다시 검증하고 겹치는 active change를 해소하며, implementation gate는 repository의 `spec-driven-tdd` workflow를 따른다.

MVP는 위 Proof를 deterministic end-to-end acceptance로 재현하고 실패 경로의 evidence까지 검증하면 완료한다.

## References

- [`vision.md`](vision.md): 프로젝트 장기 비전과 원칙
- [`ARCHITECTURE.md`](ARCHITECTURE.md): 시스템 및 execution boundary
- [`domains/reliability.md`](domains/reliability.md): 현재 reliability domain contract
- [`../inbox/archive/2026-08-08/reliability-mvp-volume-drop-vertical-slice.md`](../inbox/archive/2026-08-08/reliability-mvp-volume-drop-vertical-slice.md): MVP 범위와 safety behavior를 결정한 research
