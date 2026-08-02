# Development Documentation

이 directory는 test 실행 정책과 test design 기준을 관리한다.

## Documents

| Document | Role | Use when |
| --- | --- | --- |
| [Testing Guide](testing.md) | pytest command, marker, report, coverage, tracing | test를 실행하거나 결과를 확인할 때 |
| [Test Design and Implementation](test-design-and-implementation.md) | OpenSpec requirement를 observable contract, scenario, oracle로 변환하는 기준 | test를 설계하거나 requirement를 추적할 때 |

## Document Boundary

- `testing.md`는 **어떻게 test를 실행하는가**를 소유한다.
- `test-design-and-implementation.md`는 **무엇을 검증할지 어떻게 설계하는가**를 소유한다.
- `tests/AGENTS.md`는 **tests/에서 실제로 지켜야 하는 작성·fixture·validation 규칙**을 소유한다.
- [DEVELOPMENT.md](../../DEVELOPMENT.md)는 repository 전체의 개발 환경, package layout, formatting을 안내한다.

## Reading Order

1. [DEVELOPMENT.md](../../DEVELOPMENT.md)에서 repository 개발 환경을 확인한다.
1. [Testing Guide](testing.md)에서 test command와 report 정책을 확인한다.
1. [Test Design and Implementation](test-design-and-implementation.md)에서 test 설계 기준을 확인한다.
1. [tests/AGENTS.md](../../tests/AGENTS.md)에서 test 작성과 validation 규칙을 확인한다.
