<!-- Canonical source: `.rulesync/rules/codex-root.md`. -->

# Project Rules

이 파일은 저장소 대부분의 작업에 공통으로 적용되는 **최소 규칙**만 소유한다.
더 가까운 `AGENTS.md`가 있으면 해당 subtree의 규칙을 추가로 적용하고, 충돌하면 더 구체적인 지침을 우선한다.

## Common Rules

- 요청한 목적과 직접 관련된 파일만 수정한다.
- 작업 전 요청과 직접 관련된 owning guidance만 확인하고, 무관한 지침을 context에 추가하지 않는다.
- 사실, 구현 상태와 검증 결과는 owning source와 확인 가능한 evidence에 근거하며, 실행하지 않은 validation을 성공으로 기록하지 않는다.
- Owning source가 충돌하면 임의로 해소하지 말고 drift와 근거를 보고한다.
- 기존 architecture와 domain ownership boundary를 존중하고 불필요하게 책임을 넘나들지 않는다.
- KISS, DRY, YAGNI를 우선하고 필요하지 않은 abstraction과 중복을 만들지 않는다.
- 한국어를 기본으로 사용하되 code identifier, API name과 established technical term은 자연스러운 원문을 유지한다.

## Guidance Ownership

| Area | Owner |
| --- | --- |
| 개발 환경, active tool choice, package layout, code convention | [`DEVELOPMENT.md`](DEVELOPMENT.md) |
| 시스템 흐름과 domain ownership guidance | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/domains/`](docs/domains/OVERVIEW.md) |
| docs-wide writing, trust, lifecycle과 dashboard policy | [`docs/AGENTS.md`](docs/AGENTS.md) |
| Git과 GitHub workflow | [`docs/development/vcs-git/`](docs/development/vcs-git/README.md) |
| `openspec/**` | [`openspec/AGENTS.md`](openspec/AGENTS.md) |
| `tests/**` | [`tests/AGENTS.md`](tests/AGENTS.md) |
| `inbox/**` | [`inbox/AGENTS.md`](inbox/AGENTS.md) |

각 owner는 더 좁은 경로의 guide나 `AGENTS.md`에 세부 규칙을 위임할 수 있다. Root에는 그 세부 규칙을 반복하지 않는다.

## Path Rules

Codex CLI는 glob-scoped Rule을 별도 파일로 자동 적용하지 않는다. 작업 대상이 아래 `Match`에 해당하면 **작업 전에** 연결된 canonical Rule을 읽고 적용한다. 여러 행이 일치하면 모두 적용한다.

| Rule | Match |
| --- | --- |
| [Development](.rulesync/rules/development.md) | `src/**/*` |
| [Python](.rulesync/rules/python.md) | `src/**/*.py` |
| [Project Pivot](.rulesync/rules/project.md) | `src/project_pivot/**/*` |
| [dbt](.rulesync/rules/dbt.md) | `dbt/**` |
| [Reliability](.rulesync/rules/reliability.md) | `src/project_pivot/reliability/**`, `tests/reliability/**` |
| [Orchestration](.rulesync/rules/orchestration.md) | `src/project_pivot/orchestration/**`, `tests/orchestration/**` |
| [Markdown](.rulesync/rules/markdown.md) | `**/*.md` |
| [Local Mermaid Diagrams](.rulesync/rules/mermaid.md) | `**/*.md`, `**/*.mmd`, `**/*.mermaid` |
