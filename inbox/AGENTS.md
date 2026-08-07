# Inbox

`inbox/` is a workspace for temporary, non-canonical artifacts produced during investigation, review, discussion, and decision support.

`AGENTS.md`, `_guidelines/`, and `_templates/` are operating assets for this workspace, not inbox artifacts.

## Workflow

1. Identify the artifact's primary purpose.
1. Choose the most specific useful artifact type when the purpose is clear.
1. Read only the relevant guideline, template, and skill for the current work.
1. Write the artifact under the current date directory.
1. Transfer accepted conclusions, decisions, or actions to their owning artifacts.
1. Delete obsolete or low-value inbox content.

## Artifact Types

Artifact types are open-ended. `research` and `review` are common types, not a whitelist.

- Use a clear purpose-based type such as `research` or `review` when it fits.
- Use another concise lowercase kebab-case type when the artifact has a different clear purpose.
- Do not force an artifact into an existing type only because guidance or a template exists for it.
- When no clearer type applies, use `report` for long-form work and `brief` for short-form work.

Record the same type in the filename and frontmatter.

```yaml
---
type: <artifact-type>
title: <title>
description: <description>
tags: [] # Optional. Namespaced tags using `:` are allowed.
---
```

`type` is required. Other fields are recommended when they improve identification or retrieval.

## Paths

```python
name = "-".join(
    filter(
        None,
        [artifact_type, domain, subdomain, capability, short_title, *extensions],
    )
)
```

```text
inbox/{created_at:%Y-%m-%d}/{created_at:%H-%M}-{name}.md
inbox/{created_at:%Y-%m-%d}/{created_at:%H-%M}-{name}/*
```

Equivalent filename shape:

```text
HH-MM-<type>-<domain>[-<subdomain>][-<capability>]-<short-title>[-<extensions>]
```

Examples:

```text
15-20-research-hmda-eda-scope-reset.md
15-40-review-data-platform-test-design.md
16-00-report-reliability-foundation-status.md
16-20-brief-eda-next-step.md
```

- Resolve `created_at` in `Asia/Seoul`.
- Use lowercase kebab-case.
- `artifact_type`, `domain`, and `short_title` are required.
- `subdomain`, `capability`, and `extensions` are optional.
- `artifact_type` must match frontmatter `type`.
- Use `extensions` only when they improve identification or indexing.

## Progressive Disclosure

Read only the resources needed for the current work. Do not preload every guideline, template, or skill.

For writes to the dedicated `inbox` branch, read [Inbox Branch](_guidelines/branch.md).

| Type | Guideline | Template |
| --- | --- | --- |
| `research` | [Research](_guidelines/research.md) | [research.md](_templates/research.md) |
| `review` | [Review](_guidelines/review.md) | [review.md](_templates/review.md) |

Other artifact types follow this file unless dedicated guidance exists. Templates are starting structures, not a whitelist or mandatory shape. Add guidance or a template only when a recurring artifact type benefits from a distinct contract.

## Skill Routing

Use these tables for skill discovery only. Read a skill's `SKILL.md` only when its description matches the current task.

### Research

| Name | Description |
| --- | --- |
| `pivot-research-workspace` | Conduct evidence-backed research before specification, implementation, or technical decisions. Use to understand current behavior, bound scope, verify dependencies, compare meaningful options, or investigate failures. |

### Review

| Name | Description |
| --- | --- |
| `pivot-review-code` | Review implementation and test changes for intended behavior, correctness, regressions, reachable failure paths, maintainability risks, and validation evidence. Use for diffs, files, commits, pull requests, or working-tree changes. |

## Writing

- Write for human readability and low interpretation cost.
- Separate verified facts, inference, assumptions, and unresolved uncertainty when material.
- Use structured Markdown and visuals only when they improve comprehension.
- Do not store secrets, full generated output, or large logs.

## Archive

When `inbox/` reaches 8 date directories, move the oldest 4 to `inbox/archive/`.

- Count only date directories directly under `inbox/`.
- Do not update links when archiving.
- Humans may delete inbox or archived content at their discretion.

## Boundaries

- Do not treat dated or archived inbox artifacts as canonical project context.
- Canonical artifacts must not depend on or link to dated or archived inbox artifacts.
- If another workflow defines an owning canonical artifact, use that artifact instead of duplicating authority in `inbox/`.
- Rewrite valuable content into its canonical destination rather than promoting an inbox artifact by implication.
