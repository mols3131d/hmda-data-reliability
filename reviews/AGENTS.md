# Reviews

Rules for agents working in `reviews/`.

## Paths

```text
reviews/<target>-<review-topic>[-<sequence>].md
reviews/archive/<same-file-name>.md
```

- Use lowercase kebab-case.
- `target` and `review-topic` are required.
- Reuse an existing stable identifier such as an OpenSpec Change ID when available.
- Omit the first sequence.
- Use `-02`, `-03` for subsequent review attempts of the same target and purpose.
- Do not overwrite an existing review verdict.
- Do not create target directories.

## Template

- Use [`inbox/templates/review.md`](../inbox/templates/review.md) for new Review artifacts.
- `inbox/templates/` owns shared artifact templates. Do not create a local `reviews/templates/` copy.

## Scope

Review may cover code, tests, documentation, architecture, workflow, process or their consistency.

OpenSpec Plan Review belongs in the Change `plan-review.md`, not `reviews/`.

## Review

- Identify the target, scope and reviewed revision.
- Support findings with location, evidence, impact and required action.
- Separate verified facts, inference, defects, risks and optional improvements.
- Record performed validation, omitted validation and remaining risk.
- Do not store secrets, full generated output or large logs.
- Apply accepted changes to their owning artifacts; Review is not canonical.

## Lifecycle

Deletion is the default.

After the Review has served its purpose:

1. Transfer accepted findings to their owning artifacts.
1. Transfer required validation, remaining risk and follow-up work to a PR, Issue or canonical artifact when needed.
1. Confirm that later work does not require the Review file.
1. Delete the Review.
1. The top-level Agent may propose archival when the Review has lasting reference value.
1. Archive only after explicit human approval.

Unclear approval is not approval.

## Archive

`reviews/archive/` is simple storage.

Archived Review is not canonical, currently valid or approved for implementation. Revalidate it against the current repository before reuse.
