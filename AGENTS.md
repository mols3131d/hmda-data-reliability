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
- 문서와 repository text의 언어 선택은 `docs/language.md`를 따른다.

## Guidance Ownership

| Area | Owner |
| --- | --- |
| 개발 환경, active tool choice, package layout, code convention | `DEVELOPMENT.md` |
| 시스템 흐름과 domain ownership guidance | `docs/ARCHITECTURE.md`, `docs/domains/OVERVIEW.md` |
| docs-wide writing, trust, lifecycle과 dashboard policy | `docs/AGENTS.md` |
| Git과 GitHub workflow | `docs/development/vcs-git/README.md` |
| `openspec/**` | `openspec/AGENTS.md` |
| `tests/**` | `tests/AGENTS.md` |
| `inbox/**` | `inbox/AGENTS.md` |

각 owner는 더 좁은 경로의 guide나 `AGENTS.md`에 세부 규칙을 위임할 수 있다. Root에는 그 세부 규칙을 반복하지 않는다.

### Agent Asset Authority

- Repository-owned agent asset은 Rulesync를 기본 canonical authoring source로 사용한다.
- 다른 tool 또는 framework가 CLI나 자체 lifecycle로 생성·관리하는 asset은 해당 tool의 canonical source가 계속 소유한다. 예를 들어 OpenSpec artifact를 Rulesync에 복제하거나 재정의하지 않고 owning OpenSpec surface로 route한다.
- 아직 Rulesync로 명시적으로 migration하지 않은 기존 non-Rule asset은 현재 owner를 유지한다. Generated target projection은 독립적인 authority가 아니다.

## Path Rules

Codex CLI는 glob-scoped Rule을 별도 path-scoped file로 자동 적용하지 않는다. Antigravity CLI는 `.agents/rules/`를 Antigravity IDE와 공유하지만 current Rulesync adapter의 non-root serialization이 다르므로 이 repository에서는 CLI-owned copy를 같은 path에 덮어쓰지 않는다.

두 CLI 모두 작업 대상이 아래 `Match`에 해당하면 **작업 전에** 연결된 canonical Rule을 읽고 적용한다. 여러 행이 일치하면 모두 적용한다. Target-specific Rule은 이 table에 넣지 않는다.

| Rule | Match |
| --- | --- |
| `.rulesync/rules/development.md` | `src/**/*` |
| `.rulesync/rules/python.md` | `src/**/*.py` |
| `.rulesync/rules/project.md` | `src/project_pivot/**/*` |
| `.rulesync/rules/dbt.md` | `dbt/**` |
| `.rulesync/rules/reliability.md` | `src/project_pivot/reliability/**`, `tests/reliability/**` |
| `.rulesync/rules/orchestration.md` | `src/project_pivot/orchestration/**`, `tests/orchestration/**` |
| `.rulesync/rules/markdown.md` | `**/*.md` |
