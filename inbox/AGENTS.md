# Inbox

`inbox/` stores working, non-canonical artifacts produced during investigation, review, discussion, and decision support.

Routine artifacts are created on the dedicated `inbox` branch. Artifacts that remain useful for current or follow-up work may also exist under `main:/inbox/**` after promotion.

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

For writes to the dedicated `inbox` branch and promotion to `main`, follow [Inbox Branch](../docs/development/vcs-git/branch.md#inbox-branch).

## Writing

- Write for human readability and low interpretation cost.
- Separate verified facts, inference, assumptions, and unresolved uncertainty when material.
- Use structure or visuals only when they improve comprehension.
- Do not store secrets, full generated output, or large logs.

## Lifecycle

- Dated and archived inbox artifacts are non-canonical regardless of branch.
- Routine artifacts are created on the `inbox` branch. Promote only artifacts that remain useful for current or follow-up work.
- Promoted artifacts may be referenced as evidence, but canonical contracts and decisions must remain self-contained in their owning artifacts.
- Rewrite accepted normative content into its canonical owner. A promoted inbox artifact may remain while it has independent work or evidence value.
- On the `inbox` branch, at 8 date directories, archive the oldest routine artifacts without updating links. Do not rotate paths that are also present under `main:/inbox/**`.
- Promoted `main:/inbox/**` artifacts are deleted or archived through normal review when their work value ends, not solely by age.
- Use an owning workflow's artifact instead of creating competing authority in `inbox/`.
- Humans may delete inbox or archived content at their discretion.
