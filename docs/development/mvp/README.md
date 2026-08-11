# MVP Development

이 directory는 현재 MVP의 domain별 목표와 개발 현황을 관리한다.

- [`docs/mvp.md`](../../mvp.md)는 MVP 전체 목표와 end-to-end proof를 소유한다.
- 각 domain 문서는 MVP에서 해당 domain이 맡는 목표와 비목표를 설명한다.
- [`status.md`](status.md)와 [`status.yml`](status.yml)은 현재 구현·검증 상태의 snapshot을 기록한다.
- 세부 runtime contract는 OpenSpec Spec과 [`docs/domains`](../../domains/OVERVIEW.md)가 소유한다.

## Scope

| Domain | MVP focus |
| --- | --- |
| [HMDA Data](hmda-data.md) | controlled `volume_drop`, partition content identity, safe replacement |
| [Data Platform](data-platform.md) | dbt evidence isolation과 projection integrity |
| [Data Operations](data-operations.md) | candidate dbt run, explicit promotion, lifecycle identity handoff |
| [Reliability](reliability.md) | detection → approval → recovery → verification → evaluation |
| [Orchestration](orchestration.md) | reliability control-plane을 Dagster data plane 밖에 유지 |
| [Status](status.md) | domain별 구현·검증 현황과 다음 gate |

Subdomain 문서는 독립적으로 추적할 MVP 목표가 생기고 domain 문서 하나로 관리하기 어려울 때만 추가한다.

## Reading Order

1. [`docs/mvp.md`](../../mvp.md)에서 MVP 전체 proof와 완료 경계를 확인한다.
1. [`status.md`](status.md)에서 현재 개발 상태를 확인한다.
1. 관련 domain MVP 문서에서 이번 phase의 목표와 비목표를 확인한다.
1. 구체적인 동작은 [`docs/domains`](../../domains/OVERVIEW.md), OpenSpec Spec과 tests에서 확인한다.
