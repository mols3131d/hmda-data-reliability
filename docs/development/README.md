# Development Documentation

이 directory는 현재 MVP의 목표·milestone·개발 현황과 repository 공통 test 실행·설계 기준을 관리한다.

## MVP

| Document | Role | Use when |
| --- | --- | --- |
| [MVP Development](mvp/README.md) | MVP 전체 목표, proof milestone, domain별 목표와 개발 현황 | 현재 MVP 범위, 단계, 상태와 다음 gate를 확인할 때 |

## Post-MVP Reliability

| Document | Role | Use when |
| --- | --- | --- |
| [Next Reliability Capability](reliability-next-milestone.md) | MVP 이후 다음 Reliability capability의 선택 근거와 safety boundary | MVP proof 이후 확장할 capability와 구현 전제 조건을 확인할 때 |

## Test Guides

| Document | Role | Use when |
| --- | --- | --- |
| [Testing Guide](testing.md) | pytest command, marker, report, coverage, tracing | test를 실행하거나 결과를 확인할 때 |
| [Test Design and Implementation](test-design-and-implementation.md) | OpenSpec requirement를 observable contract, scenario, oracle로 변환하는 기준 | test를 설계하거나 requirement를 추적할 때 |

## Document Boundary

- `mvp/`는 현재 MVP의 전체 목표, proof milestone, domain별 목표와 개발 상태를 소유한다.
- `reliability-next-milestone.md`는 현재 MVP scope를 변경하지 않고 post-MVP Reliability capability 선택과 구현 전 경계를 기록한다.
- `testing.md`는 **어떻게 test를 실행하는가**를 소유한다.
- `test-design-and-implementation.md`는 **무엇을 검증할지 어떻게 설계하는가**를 소유한다.
- `tests/AGENTS.md`는 **tests/에서 실제로 지켜야 하는 작성·fixture·validation 규칙**을 소유한다.
- [DEVELOPMENT.md](../../DEVELOPMENT.md)는 repository 전체의 개발 환경, package layout, formatting을 안내한다.

## Reading Order

1. [DEVELOPMENT.md](../../DEVELOPMENT.md)에서 repository 개발 환경을 확인한다.
1. 현재 MVP 작업이면 [MVP Development](mvp/README.md)에서 전체 목표, milestone과 상태를 확인한다.
1. post-MVP Reliability 확장이면 [Next Reliability Capability](reliability-next-milestone.md)에서 선택 근거와 safety boundary를 확인한다.
1. [Testing Guide](testing.md)에서 test command와 report 정책을 확인한다.
1. [Test Design and Implementation](test-design-and-implementation.md)에서 test 설계 기준을 확인한다.
1. [tests/AGENTS.md](../../tests/AGENTS.md)에서 test 작성과 validation 규칙을 확인한다.
