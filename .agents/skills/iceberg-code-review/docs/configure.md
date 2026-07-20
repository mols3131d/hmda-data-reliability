# Configuration Guide

Configure `iceberg-code-review`.

Hidden Workflow. Not exposed in `SKILL.md` to save tokens. Send prompts below to agent to update.

## `/user_data/config.json`

### Fields

- `reviews_dir`: Review save path
- `allow_extra_frontmatter`: Allow custom frontmatter (`true`/`false`)
- `allow_extra_sections`: Allow custom sections (`true`/`false`)

> `initialize.md` auto-creates `user_data/config.json` on first setup.

## Prompt

### config help

```text
Read `workflows/configurator.md` in `iceberg-code-review` skill and explain available settings.
```

### config set

````text
Read `workflows/configurator.md` in `iceberg-code-review` skill and apply below:

```
reviews_dir: [path]
allow_extra_frontmatter: [true|false]
allow_extra_sections: [true|false]
```
````
