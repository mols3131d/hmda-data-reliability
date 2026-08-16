# Development Guides

이 directory는 **phase와 무관하게 유지되는 repository 개발 방법과 운영 규칙**을 관리한다. 제품 phase의 목표, 진행 상태와 historical readiness는 여기서 소유하지 않는다.

## Guides

| Document | Role | Use when |
| --- | --- | --- |
| [Testing Guide](testing.md) | pytest command, marker, report, coverage, tracing | test를 실행하거나 결과를 확인할 때 |
| [Test Design and Implementation](test-design-and-implementation.md) | requirement를 observable contract, scenario와 oracle로 변환하는 기준 | test를 설계하거나 requirement를 추적할 때 |
| [Version Control and GitHub](vcs-git/README.md) | branch, commit, Pull Request와 review 운영 규칙 | Git/GitHub 작업을 수행할 때 |

## Boundary

- 현재 active product goal과 acceptance는 [`../mvp.md`](../mvp.md)가 소유한다.
- 시스템 구조와 domain contract는 [`../ARCHITECTURE.md`](../ARCHITECTURE.md), [`../domains/**`](../domains/OVERVIEW.md)가 소유한다.
- 인간용 상태 snapshot은 [`../dashboard.md`](../dashboard.md)에만 두며 일반 개발 작업에서 자동 갱신하지 않는다.
- 완료된 Foundation 같은 phase bundle은 이 directory에 보존하지 않는다. Durable knowledge를 canonical owner로 승격한 뒤 삭제한다.
- [`../../DEVELOPMENT.md`](../../DEVELOPMENT.md)는 repository 전체 개발 환경과 active tool choices를 안내한다.

## Reading Order

1. [`../../DEVELOPMENT.md`](../../DEVELOPMENT.md)에서 repository 개발 환경을 확인한다.
2. 작업의 현재 목표가 필요하면 [`../mvp.md`](../mvp.md)의 scope와 acceptance를 확인한다.
3. 세부 system/domain contract는 canonical owner를 직접 읽는다.
4. test 또는 Git 작업이면 해당 guide를 읽는다.

Dashboard는 인간 편의 문서이므로 agent의 작업 context나 evidence source로 사용하지 않는다.
