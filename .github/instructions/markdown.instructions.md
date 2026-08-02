---
name: Markdown
description: "Use when writing or editing Markdown docs, README, notes, or AGENTS-style guidelines. Covers GFM callouts, tables, mermaid, language, and link-not-embed."
applyTo: "**/*.md"
---

- Language: `ko`. Use `en` for headers, field names, and standard technical terms.
- Use GFM callouts, tables, or Mermaid when useful.
- Format: all `uv run rumdl fmt .`; file `uv run rumdl fmt path/to/file.md`; glob `uv run rumdl fmt 'docs/**/*.md'`.
- link-not-embed

---

- 인간과 에이전트 가독성을 고려하여 작성한다.
- 인간 가독성 개선
  - `/human-facing-markdown`
  - `/mermaid-chart`
  - `/mermaid-diagram`
