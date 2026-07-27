---
name: Markdown
description: "Use when writing or editing Markdown docs, README, notes, or AGENTS-style guidelines. Covers GFM callouts, tables, mermaid, language, and link-not-embed."
applyTo: "**/*.md"
---

- Language: `ko`. Use `en` for headers, field names, and standard technical terms.
- Use GFM callouts, tables, or Mermaid when useful.
- Format: all `uv run rumdl fmt .`; file `uv run rumdl fmt path/to/file.md`; glob `uv run rumdl fmt 'docs/**/*.md'`.
- link-not-embed
