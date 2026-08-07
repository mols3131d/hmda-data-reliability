# Review

Use `review` when the artifact's primary purpose is to evaluate an identified target against an intended contract, baseline, or quality expectation and produce evidence-backed findings.

## Scope

Review may cover code, tests, documentation, architecture, workflow, process, or consistency between them.

If another workflow defines an owning review artifact, such as an OpenSpec `plan-review.md`, use that artifact instead of creating a competing inbox authority.

## Contract

- Identify the target, scope, and reviewed revision or baseline when available.
- Verify candidate findings against the actual target and existing safeguards.
- Support material findings with location, evidence, impact, and required action.
- Separate verified facts, inference, defects, risks, and optional improvements when material.
- Record performed validation, omitted validation, and remaining risk.
- Prefer a small number of well-supported findings over speculative volume.

## Template

Use [`inbox/templates/review.md`](../templates/review.md) when a reusable structure helps. Adapt or omit sections that do not serve the review.

## Output

Lead with the review result or highest-impact findings. Keep evidence close to the finding it supports and distinguish required action from optional improvement.

## Boundaries

- Do not create findings from style preference alone.
- Do not broaden the review into unrelated existing defects or redesign.
- Do not claim validation, reproduction, or verification that was not performed.
- Do not treat the Review artifact as the canonical fix, decision, or requirement.
- Follow the lifecycle, path, frontmatter, and canonical-boundary rules in `inbox/AGENTS.md`.
