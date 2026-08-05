# Inbox

## Purpose

`inbox/` is a temporary, non-canonical workspace.

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
- Use `extensions` to distinguish or index artifacts.

## Frontmatter Recommendations

```yaml
title: <title>
description: <description>
tags: [] # Optional. Namespaced tags using `:` are allowed.
```

## Writing

- Write for human readability.
- Use `Summary` or `Overview` when useful.
- Use structured Markdown and visuals only when they improve comprehension.

## Archive

When `inbox/` reaches 8 date directories, move the oldest 4 to `inbox/archive/`.

- Count only date directories directly under `inbox/`.
- Do not update links when archiving.
- Humans may delete inbox or archived content at their discretion.

## Boundaries

- Do not treat `inbox/` as canonical context.
- Canonical artifacts must not depend on or link to it.
- Rewrite valuable content into its canonical destination.
- Delete obsolete or low-value content.
