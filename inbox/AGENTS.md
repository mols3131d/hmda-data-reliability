# Inbox

`inbox/` stores temporary, non-canonical artifacts produced during investigation, review, discussion, and decision support.

`AGENTS.md`, `_guidelines/`, and `_templates/` are operating assets, not inbox artifacts.

## Workflow

1. Identify the artifact's primary purpose and type.
1. Read only the relevant type guideline when one exists.
1. Write the artifact under the current date directory.

## Artifact Contract

Artifact types are open-ended. Use the clearest purpose-based lowercase kebab-case type. When no clearer type applies, use `report` for long-form work and `brief` for short-form work.

Use the same type in the filename and frontmatter.

```yaml
---
type: <artifact-type>
title: <title>
description: <description>
tags: [] # Optional
---
```

`type` is required. Other fields are optional when they improve identification or retrieval.

## Paths

```text
inbox/YYYY-MM-DD/HH-MM-<type>-<domain>[-<subdomain>][-<capability>]-<short-title>[-<extensions>].md
inbox/YYYY-MM-DD/HH-MM-<type>-<domain>[-<subdomain>][-<capability>]-<short-title>[-<extensions>]/*
```

- Resolve date and time in `Asia/Seoul`.
- Use lowercase kebab-case.
- `type`, `domain`, and `short-title` are required.
- Add optional components only when they improve identification or indexing.

## Routing

| Type | Guideline |
| --- | --- |
| `research` | [Research](_guidelines/research.md) |
| `review` | [Review](_guidelines/review.md) |

Other artifact types use this common contract unless dedicated guidance exists. Add a guideline only when a recurring type needs a distinct contract.

For writes to the dedicated `inbox` branch, follow [Inbox Branch](../docs/development/vcs-git/branch.md#inbox-branch).

## Writing

- Write for human readability and low interpretation cost.
- Separate verified facts, inference, assumptions, and unresolved uncertainty when material.
- Use structure or visuals only when they improve comprehension.
- Do not store secrets, full generated output, or large logs.

## Lifecycle

- Dated and archived inbox artifacts are non-canonical; canonical artifacts must not depend on or link to them.
- Rewrite accepted content into its canonical owner. Delete obsolete or low-value content.
- Use an owning workflow's artifact instead of creating competing authority in `inbox/`.
- At 8 date directories, move the oldest 4 to `inbox/archive/` without updating links.
- Humans may delete inbox or archived content at their discretion.
