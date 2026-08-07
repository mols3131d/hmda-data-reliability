# Inbox

`inbox/` is a temporary, non-canonical workspace for artifacts produced during investigation, review, discussion, and decision support.

## Workflow

1. Identify the artifact's primary purpose.
1. Choose the most specific useful artifact type when the purpose is clear.
1. Read only the relevant guideline under `inbox/guidelines/`.
1. Write the artifact under the current date directory.
1. Transfer accepted conclusions, decisions, or actions to their owning artifacts.
1. Delete obsolete or low-value inbox content.

## Artifact Types

Artifact types are open-ended. `research` and `review` are common types, not a whitelist.

- Use a clear purpose-based type such as `research` or `review` when it fits.
- Use another concise lowercase kebab-case type when the artifact has a different clear purpose.
- Do not force an artifact into an existing type only because a guideline exists for it.
- When no clearer type applies, use `report` for long-form work and `briefing` for short-form work.

Record the type in frontmatter.

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
        [domain, subdomain, capability, short_title, *extensions],
    )
)
```

```text
inbox/{created_at:%Y-%m-%d}/{created_at:%H-%M}-{name}.md
inbox/{created_at:%Y-%m-%d}/{created_at:%H-%M}-{name}/*
```

- Resolve `created_at` in `Asia/Seoul`.
- Use lowercase kebab-case.
- `domain` and `short_title` are required.
- `subdomain`, `capability`, and `extensions` are optional.
- Use `extensions` only when they improve identification or indexing.

## Progressive Disclosure

Read only the guidance needed for the current artifact. Do not preload every guideline.

| Need | Guideline |
| --- | --- |
| Answer a question by gathering and validating evidence | [Research](guidelines/research.md) |
| Evaluate a target and produce evidence-backed findings | [Review](guidelines/review.md) |

Other artifact types follow this file unless a dedicated guideline exists. Add a new guideline only when a recurring artifact type needs a distinct contract.

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

- Do not treat `inbox/` as canonical project context.
- Canonical artifacts must not depend on or link to inbox content.
- If another workflow defines an owning canonical artifact, use that artifact instead of duplicating authority in `inbox/`.
- Rewrite valuable content into its canonical destination rather than promoting an inbox file by implication.
