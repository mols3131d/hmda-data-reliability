# Placeholder Rules

LLM writes values replacing `{{name}}` in templates.

## Syntax

```text
{{name}}
```

- Allowed chars: English, underscore (`_`)
- Length: ≥ 1
- Not allowed: Spaces, numbers, hyphens, newlines

Regex:

```regex
{{[A-Za-z_]+}}
```

## Examples

Match:

```text
{{title}}
{{file_path}}
```

Exclude:

```text
{{}}
{{ title }}
{{title-slug}}
{{123}}
`{{` ... `}}`
```

Parser ignores Markdown context. Placeholders inside code blocks are counted.

## Validation Functions

- `count_placeholders(path)`: Returns count of remaining placeholders
- `has_no_placeholders(path)`: Returns `True` if 0
