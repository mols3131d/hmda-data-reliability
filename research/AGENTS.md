# Research

Rules for agents working in `research/`.

Research artifacts are temporary investigation records used to answer a question, gather evidence, and support a decision. They are not canonical project documentation.

## Paths

```text
research/<domain>[-<subdomain>]-<topic>[-<sequence>].md
research/archive/<same-file-name>.md
```

- Use lowercase kebab-case.
- `domain` and `topic` are required.
- Add `subdomain` only when it improves identification.
- Omit the first sequence.
- Use `-02`, `-03`, etc. only for an independent re-investigation of the same question.
- Update the existing file when continuing the same investigation.
- Do not create topic directories.

## Template

- Use [`inbox/templates/research.md`](../inbox/templates/research.md) for new Research artifacts.
- `inbox/templates/` owns shared artifact templates. Do not create a local `research/templates/` copy.

## Lifecycle

Deletion is the default.

Keep Research only while it is actively needed to investigate a question or support a pending decision.

After the Research has served its purpose:

1. Transfer accepted conclusions to their owning artifacts.
1. Delete the Research.
1. The top-level Agent may propose archival when the Research has lasting reference value.
1. Archive only after explicit human approval.

Do not keep Research merely because it may be useful later.

Unclear approval is not approval.

## Archive

`research/archive/` is simple storage for explicitly preserved Research.

- Preserve the original file name when archiving.
- Do not treat archived Research as canonical, currently valid, or approved for implementation.
- Do not update archived Research as part of normal continued investigation.
- Revalidate archived Research against the current repository before reuse.
- If a question is investigated again, create or update the appropriate active Research artifact rather than treating the archive as current evidence.

## Related Agent Assets

| Agent Asset | Description |
| --- | --- |
| `.agents/skills/openspec-explore/SKILL.md` | Guides exploratory investigation used to understand a problem, constraints, alternatives, and evidence before committing to a change. |
| `.agents/skills/pivot-research-workspace/SKILL.md` | Evidence-backed research before specification, implementation, or technical decisions; covers current behavior, scope, dependencies, options, and failure investigation. |
