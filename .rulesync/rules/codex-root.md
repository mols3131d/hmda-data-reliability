---
root: true
targets:
  - antigravity-ide
  - antigravity-cli
  - codexcli
description: "Repository-wide global instructions with fallback routing for cross-cutting Rulesync rules."
---

<!-- Canonical source: `.rulesync/rules/codex-root.md`. -->

# Project Rules

Root `AGENTS.md`는 repository-wide **전역 지침이자 agent 전용 entrypoint**다.
더 가까운 `AGENTS.md`가 있으면 해당 subtree의 지침을 추가로 적용하고, 충돌하면 더 구체적인 지침을 우선한다.

Harness가 native로 지원하는 instruction loading이나 discovery는 root에서 반복하지 않는다. Root entrypoint에는 전역 규칙과 harness가 직접 지원하지 않는 compatibility routing만 둔다.

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
| Agent instruction ownership과 중복 최소화 | `docs/development/agent-instructions.md` |
| Git과 GitHub workflow | `docs/development/vcs-git/README.md` |
| `openspec/**` | `openspec/AGENTS.md` |
| `tests/**` | `tests/AGENTS.md` |
| `inbox/**` | `inbox/AGENTS.md` |

각 owner는 더 좁은 경로의 guide나 `AGENTS.md`에 세부 규칙을 위임할 수 있다. Root에는 그 세부 규칙을 반복하지 않는다.

## Rule Routing

현재 Codex CLI와 Antigravity CLI의 Rulesync projection에서는 아래 cross-cutting Rule만 root fallback으로 route한다. Directory/subtree 지침은 가장 가까운 `AGENTS.md`가 소유하며 이 table에 넣지 않는다.

| Rule | Match |
| --- | --- |
| `.rulesync/rules/python.md` | `src/**/*.py` |
| `.rulesync/rules/markdown.md` | `**/*.md` |
