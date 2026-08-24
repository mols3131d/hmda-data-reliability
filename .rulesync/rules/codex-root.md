---
root: true
targets:
  - antigravity-ide
  - antigravity-cli
  - codexcli
description: "Minimal project-wide AGENTS instructions with CLI fallback routing for cross-cutting Rules."
---

<!-- Canonical source: `.rulesync/rules/codex-root.md`. -->

# Project Rules

- 문서와 repository text의 언어 선택은 `docs/language.md`를 따른다.
- Directory 또는 subtree context는 가장 가까운 `AGENTS.md`가 소유한다. Root에 하위 규칙을 반복하지 않는다.
- Rulesync source와 projection lifecycle은 `.rulesync/README.md`가 소유한다.

## Cross-cutting Rule Routing

Codex CLI와 Antigravity CLI에서 아래 cross-cutting Rule의 target path가 일치하면 작업 전에 canonical Rule을 읽고 적용한다. Directory-scoped context는 이 table로 route하지 않는다.

| Rule | Match |
| --- | --- |
| `.rulesync/rules/python.md` | `src/**/*.py` |
| `.rulesync/rules/markdown.md` | `**/*.md` |
