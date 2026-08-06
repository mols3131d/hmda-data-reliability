# Reviews

Rules for agents working in `reviews/`.

## Paths

```text
reviews/<target>-<review-topic>[-<sequence>].md
```

- Use lowercase kebab-case.
- `target` and `review-topic` are required.
- Omit the first sequence.
- Use `-02`, `-03` for subsequent review attempts.
- Do not overwrite an existing review verdict.
- Do not create target directories.
- Reuse an existing stable identifier such as an OpenSpec Change ID when available.

## Scope

Review may cover code, tests, documentation, architecture, workflow, process or their consistency.

OpenSpec Plan Review belongs in the Change `plan-review.md`, not `reviews/`.

## Review

- Identify the target, scope and reviewed revision.
- Support findings with location, evidence, impact and required action.
- Separate verified facts, inference, defects, risks and optional improvements.
- Record performed validation, omitted validation and remaining risk.
- Do not store secrets, full generated output or large logs.

## Lifecycle

Review is a snapshot of the judgment made against a specific revision.

After review:

1. Apply accepted changes to their owning artifacts.
1. Create a new sequence for re-review.
1. Preserve earlier attempts without changing their verdict.

Review artifacts are not canonical or necessarily current. Revalidate them against the current repository before reuse.
