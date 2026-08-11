# MVP Development

이 directory는 현재 MVP의 domain별 목표와 개발 현황을 관리한다.

- [`docs/mvp.md`](../../mvp.md)는 MVP 전체 목표와 end-to-end proof를 소유한다.
- 각 domain 문서는 이번 MVP에서 해당 domain이 달성해야 할 결과와 비목표를 설명한다.
- [`status.md`](status.md)는 현재 구현·검증 상태와 다음 gate를 기록한다.
- 세부 runtime contract는 OpenSpec Spec과 [`docs/domains`](../../domains/OVERVIEW.md)가 소유한다.

## Scope

| Domain | MVP focus |
| --- | --- |
| [HMDA Data](hmda-data.md) | controlled `volume_drop`과 안전한 partition 복원 근거 |
| [Data Platform](data-platform.md) | candidate와 current dbt evidence의 일관성 보존 |
| [Data Operations](data-operations.md) | validation과 current-state 변경의 실행 경계 |
| [Reliability](reliability.md) | detection → approval → recovery → verification → evidence |
| [Orchestration](orchestration.md) | reliability control-plane을 Dagster data plane 밖에 유지 |
| [Status](status.md) | 전체 gate와 domain별 개발 현황 |

Subdomain 문서는 독립적으로 추적할 MVP 목표가 생기고 domain 문서 하나로 관리하기 어려울 때만 추가한다.

## Reading Order

1. [`docs/mvp.md`](../../mvp.md)에서 MVP 전체 proof와 완료 경계를 확인한다.
1. [`status.md`](status.md)에서 현재 개발 상태와 다음 gate를 확인한다.
1. 관련 domain MVP 문서에서 이번 phase의 목표와 비목표를 확인한다.
1. 구체적인 동작은 [`docs/domains`](../../domains/OVERVIEW.md), OpenSpec Spec과 tests에서 확인한다.
