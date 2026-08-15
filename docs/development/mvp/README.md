# MVP: Volume-Drop Recovery Proof

> **목표:** 하나의 `volume_drop` incident를 탐지부터 승인된 recovery와 재검증까지 연결해 Project Pivot의 evidence-first, human-controlled Data Reliability 가치를 end-to-end로 증명한다.

MVP는 기능 범위를 넓히는 단계가 아니다. 결정론적으로 재현 가능한 하나의 failure를 안전하게 복구하고, 판단과 결과를 evidence로 설명할 수 있음을 증명한다.

## End-to-End Proof

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

## Milestone Model

이 directory에서 milestone은 **현재 MVP의 end-to-end proof를 나누는 고수준 proof gate**다. 구현 task 묶음이나 MVP 이후 capability roadmap을 의미하지 않는다.

`null_spike`, `schema_drift`, `freshness_delay` 같은 후속 incident 확장은 현재 MVP scope에 포함되지 않으며, MVP scope가 명시적으로 바뀌기 전에는 아래 milestone 목록에 추가하지 않는다.

## Proof Milestones

| Milestone | 증명하는 것 | 완료 신호 |
| --- | --- | --- |
| [01. Detect and Explain](milestone-01-detect-and-explain.md) | 이상을 안전하게 구분하고 영향과 조치 근거를 설명할 수 있다. | clean/defect case가 재현 가능하게 구분되고 분석이 current state를 바꾸지 않는다. |
| [02. Approve and Recover](milestone-02-approve-and-recover.md) | 검증과 외부 approval이 실제 recovery의 안전 경계로 작동한다. | 승인 범위를 벗어난 상태는 변경 전에 차단되고 승인된 recovery만 기대 상태를 복원한다. |
| [03. Verify and Evaluate](milestone-03-verify-and-evaluate.md) | 복구 결과와 failure/retry를 evidence로 검증할 수 있다. | recovery가 incident를 해소하고 end-to-end 결과와 다음 action이 재현 가능하게 남는다. |

Milestone 문서는 목표와 완료 경계만 소유한다. 세부 contract와 scenario는 OpenSpec, domain 문서와 tests가 소유하며 현재 진행 상태는 [`status.md`](status.md)에서 관리한다.

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

## Done

MVP는 세 milestone의 proof를 하나의 deterministic end-to-end acceptance로 연결하고 주요 failure path의 evidence까지 검증하면 완료한다.

OpenSpec planning과 구현은 이 고수준 목표를 구체화하며, repository의 `spec-driven-tdd` workflow와 현재 architecture boundary를 따른다.

## Development Tracking

| 문서 | 역할 |
| --- | --- |
| [`status.md`](status.md) | 현재 implementation/verification progress와 gap |
| [`hmda-data.md`](hmda-data.md) | HMDA Data MVP 목표 |
| [`data-platform.md`](data-platform.md) | Data Platform MVP 목표 |
| [`data-operations.md`](data-operations.md) | Data Operations MVP 목표 |
| [`reliability.md`](reliability.md) | Reliability MVP 목표 |
| [`orchestration.md`](orchestration.md) | Orchestration MVP 목표 |

## Reading Order

1. 이 문서에서 MVP 전체 proof와 milestone 순서를 확인한다.
1. 현재 단계의 `milestone-*.md`에서 목표와 완료 경계를 확인한다.
1. [`status.md`](status.md)에서 현재 implementation/verification 상태를 확인한다.
1. 관련 domain MVP 문서에서 domain별 목표와 비목표를 확인한다.
1. 구체적인 동작은 [`docs/domains`](../../domains/OVERVIEW.md), OpenSpec Spec과 tests에서 확인한다.

## References

- [`../../vision.md`](../../vision.md): 프로젝트 장기 비전과 원칙
- [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md): 시스템 및 execution boundary
- [`../../domains/reliability.md`](../../domains/reliability.md): 현재 reliability domain contract
- [`../../../inbox/archive/2026-08-08/reliability-mvp-volume-drop-vertical-slice.md`](../../../inbox/archive/2026-08-08/reliability-mvp-volume-drop-vertical-slice.md): MVP 범위와 safety behavior를 결정한 research
