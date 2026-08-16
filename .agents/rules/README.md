# Rules

`.agents/rules` contains **path-scoped, cross-cutting instructions** shared by
agent harnesses such as Antigravity and VS Code/Copilot.

Rules are not the primary place for project context. Prefer the narrowest
mechanism that naturally owns the context.

| Need | Prefer |
| --- | --- |
| Repository or directory subtree context | nearest `AGENTS.md` |
| Reusable procedure, knowledge, or capability | `.agents/skills/<name>/SKILL.md` |
| One constraint across files selected by path | `.agents/rules` |

Create a Rule only when the same instruction must follow files selected by a
`glob` and a single directory-scoped `AGENTS.md` is not a natural fit.

## Compatibility model

The files in this directory use a **project compatibility format**, not a
vendor-defined common schema. Keep one instruction body and carry the minimum
selector metadata needed by the harnesses that read the file directly.

Current pilot targets:

- Antigravity discovers workspace Rules from `.agents/rules` and uses
  `trigger: glob` with string `globs`.
- VS Code/Copilot discovers `*.instructions.md` from configured instruction
  locations and uses `applyTo`.

VS Code currently diagnoses Antigravity-only front-matter keys such as
`trigger` and `globs` as unsupported hints. This does not make them part of the
Copilot schema. Treat the direct shared-file approach as acceptable only while
those non-blocking diagnostics are an acceptable trade-off. If clean native
validation becomes a requirement, use harness-specific generated projections
instead of adding more compatibility fields here.

## File shape

Use:

```text
.agents/rules/<topic>.instructions.md
```

Keep front matter small:

```yaml
---
name: SQL Migrations
description: Constraints shared by SQL migration files.
trigger: glob
globs: "**/migrations/**/*.sql"
applyTo: "**/migrations/**/*.sql"
---
```

Then write the instruction as plain Markdown without harness-specific behavior:

```markdown
# SQL Migrations

- Keep migrations safe for rolling deployment.
- Avoid destructive changes without a compatibility phase.
- Consider lock duration when adding indexes.
```

## Contract

- `globs` is the project-semantic path selector and current Antigravity
  projection. Encode multiple patterns as one comma-separated string.
- `applyTo` is the VS Code/Copilot projection of `globs`; both MUST describe
  the same file set.
- `trigger` is `glob` for this pilot. Add another activation mode only when a
  real Rule use case cannot be expressed with `AGENTS.md` or a Skill.
- `name` is Copilot-facing display metadata; `description` describes the Rule
  without changing its semantics.
- Keep the body short, imperative, and independent of a specific harness.
- Do not repeat context already provided by an applicable `AGENTS.md` or Skill.
- Do not add metadata, aliases, or extensions until they are required.

VS Code does not discover `.agents/rules` by default. Workspace configuration
MUST include `.agents/rules` in `chat.instructionsFilesLocations` while these
Rules are expected to serve VS Code/Copilot directly.

## Good Rule scopes

Use Rules for cross-cutting patterns such as:

```text
**/*.sql
**/*.proto
apps/*/src/**/*.tsx
packages/*/migrations/**
```

A Rule can also join otherwise unrelated trees when they intentionally share
the same constraint:

```yaml
globs: "apps/*/src/**/*.tsx,packages/*/ui/**/*.tsx"
applyTo: "apps/*/src/**/*.tsx,packages/*/ui/**/*.tsx"
```

## Prefer another asset

Do not create a Rule just to scope instructions to one natural subtree:

```text
src/payments/**
```

Prefer:

```text
src/payments/AGENTS.md
```

Do not use a Rule for a reusable procedure such as testing, investigation, or
review. Prefer a Skill.

Do not use a Rule for repository-wide principles. Prefer the root `AGENTS.md`.

## Future harnesses

Treat `globs` as the semantic source of truth when adding another harness. Map
its native path selector to the same file set before extending this format.

Do not add another harness-specific field merely because a harness supports it.
Add compatibility metadata only when a real Rule needs it and direct shared-file
loading remains simpler than generated projections.

## Authoring check

Before adding or changing a Rule, verify:

1. A nearby `AGENTS.md` would not express the scope more naturally.
2. A Skill would not express the guidance more naturally.
3. The Rule is genuinely selected by file path.
4. `globs` and `applyTo` select the same files.
5. The body contains only the cross-cutting instruction.
