# Research

Rules for agents working in `research/`.

## Paths

```text
research/<domain>[-<subdomain>]-<topic>[-<sequence>].md
research/archive/<same-file-name>.md
```

- Use lowercase kebab-case.
- `domain` and `topic` are required.
- Omit the first sequence.
- Use `-02`, `-03` only for an independent re-investigation of the same question.
- Update the existing file for continued work.
- Do not create topic directories.

## Template

- Use `research/templates/research.md` for new Research artifacts.
- Keep Research templates under `research/templates/`.
- Templates are workspace guidance and are excluded from Research lifecycle rules.

## Lifecycle

Deletion is the default.

After the Research has served its purpose:

1. Transfer accepted conclusions to their owning artifacts.
1. Delete the Research.
1. The top-level Agent may propose archival when the Research has lasting reference value.
1. Archive only after explicit human approval.

Unclear approval is not approval.

## Archive

`research/archive/` is simple storage.

Archived Research is not canonical, currently valid or approved for implementation. Revalidate it against the current repository before reuse.
