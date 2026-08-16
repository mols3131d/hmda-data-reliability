# `.agents/rules` Superset Spec

Version: `0.2`

A small, source-first rule format for **Antigravity Rules** and **VS Code / GitHub Copilot Instructions**.

## Purpose

`.agents/rules` is intentionally narrow.

Use rules only for **cross-cutting constraints that must be selected by file path**, such as:

- a file extension or language family
- a framework-specific file pattern
- multiple subdirectories that share the same rule

Prefer other context mechanisms whenever possible:

1. **`AGENTS.md`** for directory- or subtree-specific project context
2. **Skills** for reusable procedures, knowledge, or task-specific guidance
3. **Rules** only when path/glob selection is the natural way to express applicability

Do not use `.agents/rules` as a general-purpose instruction dump.

## Location

```text
.agents/
└── rules/
    └── **/*.instructions.md
```

`.instructions.md` is preferred because VS Code/Copilot recognizes it natively while it remains a normal Markdown rule under `.agents/rules`.

## Design rule

A rule SHOULD normally use `activation: glob`.

If the desired scope can be represented naturally by a nearby `AGENTS.md` or by a skill, prefer that instead.

Examples:

```text
src/payments/**
```

Prefer:

```text
src/payments/AGENTS.md
```

instead of a rule scoped only to `src/payments/**`.

But for rules such as:

```text
**/*.sql
**/*.proto
apps/*/src/**/*.tsx
packages/*/migrations/**
```

a glob rule is appropriate because the same constraint cuts across otherwise unrelated directories.

## Front matter

```yaml
---
name: TypeScript
description: Shared constraints for TypeScript source files.

activation: glob

globs:
  - "**/*.ts"
  - "**/*.tsx"

applyTo: "**/*.ts,**/*.tsx"
---
```

## Fields

| Field | Required | Meaning |
|---|---:|---|
| `name` | no | Human-readable rule name. Defaults to filename. |
| `description` | recommended | Short explanation of the rule's purpose. |
| `activation` | yes | Normally `glob`. Other modes are reserved for exceptional cases. |
| `globs` | for `glob` | Canonical file selectors. |
| `applyTo` | for direct Copilot use | Copilot projection derived from `globs`. |
| `extensions` | no | Reserved for future harness-specific data. |

## Activation

### `glob`

The normal and preferred mode.

```yaml
activation: glob

globs:
  - "**/*.sql"
```

Use when applicability is fundamentally determined by file path.

### `always`

Allowed but discouraged.

Repository-wide or subtree-wide persistent context usually belongs in `AGENTS.md`.

### `model`

Allowed but discouraged.

Task- or capability-oriented guidance usually belongs in a skill.

### `manual`

Allowed but discouraged.

Explicit reusable procedures usually belong in a skill or workflow.

## Normalization

`activation` and `globs` are canonical.

`applyTo` is a materialized Copilot alias and MUST represent the same selectors as `globs`.

```yaml
activation: glob

globs:
  - "**/*.ts"
  - "**/*.tsx"

applyTo: "**/*.ts,**/*.tsx"
```

A validator SHOULD reject conflicting values.

## Extensions

Do not add a generic field until at least two harnesses need the same semantic concept.

Harness-only data goes under a namespaced extension:

```yaml
extensions:
  google.antigravity: {}
  github.copilot: {}
```

`extensions` is an escape hatch, not a dumping ground.

A compiler MAY strip it from generated native files if a target does not tolerate unknown front-matter keys.

## Body

Everything after the front matter is the rule itself.

Keep it short and cross-cutting.

```markdown
# TypeScript

- Avoid `any` unless required by an external boundary.
- Keep public API types explicit.
- Add tests for new behavior.
```

Do not duplicate context that already lives in an applicable `AGENTS.md` or skill.

## Appropriate examples

### Language-wide

```yaml
globs:
  - "**/*.py"
```

### File-type specific

```yaml
globs:
  - "**/*.sql"
  - "**/*.proto"
```

### Shared convention across multiple trees

```yaml
globs:
  - "apps/*/src/**/*.tsx"
  - "packages/*/ui/**/*.tsx"
```

### Cross-cutting migration rule

```yaml
globs:
  - "**/migrations/**/*.sql"
```

## Inappropriate examples

### Single subtree

```yaml
globs:
  - "src/payments/**"
```

Prefer:

```text
src/payments/AGENTS.md
```

### General testing procedure

Prefer a skill such as:

```text
.agents/skills/testing/SKILL.md
```

### Repository-wide engineering principles

Prefer root:

```text
AGENTS.md
```

## Complete example

```markdown
---
name: SQL Migrations
description: Shared constraints for SQL migration files.
activation: glob

globs:
  - "**/migrations/**/*.sql"

applyTo: "**/migrations/**/*.sql"
---

# SQL Migrations

- Migrations must be safe for rolling deployment.
- Avoid destructive changes without an explicit compatibility phase.
- Add indexes deliberately and consider lock duration.
```

## Compatibility model

The spec distinguishes semantics from serialization:

```text
globs
  │
  ├─ Antigravity → glob-based rule selection
  ├─ Copilot     → applyTo
  └─ future      → adapter/compiler
```

The rule body remains plain Markdown.

## Rule selection principle

Use the narrowest appropriate mechanism:

```text
directory / subtree context
        → AGENTS.md

task / capability / procedure
        → Skill

cross-cutting path pattern
        → Rule
```

This is the primary design constraint of `.agents/rules`.
