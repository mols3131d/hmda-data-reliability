# Development

이 directory는 repository의 **phase-independent development guides**와 사람이 빠르게 보는 **development dashboard**를 둔다. Dashboard는 위치상 development에 속하지만 개발 규칙이나 canonical state를 소유하지 않는 비권위 projection이다.

## Documents

| Document | Role | Use when |
| --- | --- | --- |
| [Development Dashboard](dashboard.md) | human-only development status snapshot | 사람이 개발 진행 상태와 gap을 빠르게 확인할 때 |
| [Testing Guide](testing.md) | pytest command, marker, report, coverage, tracing | test를 실행하거나 결과를 확인할 때 |
| [Test Design and Implementation](test-design-and-implementation.md) | requirement를 observable contract, scenario와 oracle로 변환하는 기준 | test를 설계하거나 requirement를 추적할 때 |
| [Version Control and GitHub](vcs-git/README.md) | branch, commit, Pull Request와 review 운영 규칙 | Git/GitHub 작업을 수행할 때 |

## Boundary

- Current capability의 normative contract는 [`../../openspec/specs/`](../../openspec/specs/)가 소유한다.
- 시스템 구조와 domain ownership guidance는 [`../ARCHITECTURE.md`](../ARCHITECTURE.md), [`../domains/**`](../domains/OVERVIEW.md)가 설명한다.
- Active product goal은 [`../mvp.md`](../mvp.md)가 소유한다.
- [`dashboard.md`](dashboard.md)는 위 source들을 대체하지 않는 인간용 projection이며 일반 개발 작업의 side effect로 갱신하지 않는다.
- 완료된 phase bundle이나 historical readiness는 이 directory에 보존하지 않는다.
- [`../../DEVELOPMENT.md`](../../DEVELOPMENT.md)는 repository 전체 개발 환경과 active tool choices를 안내한다.

## Dashboard Refresh

Dashboard refresh는 **별도 명시적 작업**으로 수행한다.

- Installed `mols-markdown-dashboard` skill을 따른다.
- Canonical Spec, source, tests와 matching-revision 실행 evidence를 다시 조사한다.
- Project dashboard의 `Development Progress`, `Implementation Gaps`, `Verification Gaps` 구조와 근거 기반 `n/n`을 사용한다.
- 상태나 denominator를 추측하지 않는다.
- 기본 repository artifact는 Markdown으로 유지하며 별도 요청 없이 YAML dashboard SSOT를 저장하지 않는다.

## Reading Order

1. [`../../DEVELOPMENT.md`](../../DEVELOPMENT.md)에서 repository 개발 환경을 확인한다.
2. test 또는 Git 작업이면 해당 guide를 읽는다.
3. 사람이 현재 개발 dashboard를 확인하려는 경우에만 [`dashboard.md`](dashboard.md)를 읽는다.
4. 제품 목표나 project document navigation이 필요하면 [`../README.md`](../README.md)에서 owning document를 찾는다.

Phase-independent guide는 current phase가 바뀌어도 가능한 한 수정 없이 유지한다. Dashboard는 이 원칙의 예외이며 별도 refresh lifecycle을 따른다.
