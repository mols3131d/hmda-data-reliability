---
name: prj-load-context-review
description: >-
  Load repository context and orchestration for top-level independent review of a bounded
  technical change or artifact, including pull requests, diffs, files, commits, working
  tree changes, implementation, tests, runtime, or code-facing configuration. In VS Code,
  route dual-perspective review through review-lead when available. Do not use inside
  review-lead, review-quality, or review-adversarial, or for implementation self-review.
targets: [claudecode, codexcli, copilot, copilotcli, antigravity-ide, antigravity-cli]
---

# Review Context

Load only the repository context needed to start and consume a bounded independent review. Detailed review methodology, VCS policy, artifact lifecycle, and finding routing remain with their existing owners.

## Load Context

- For implementation or test changes, use `prj-review-code` for review methodology and evidence criteria.
- For a Pull Request or other Git/GitHub review surface, use `prj-vcs-git-github` for repository review policy, templates, and mutable GitHub state when material.
- If Review findings must be routed into an OpenSpec `spec-driven-tdd` change, use `prj-spec-driven-tdd-rpi` after the findings are established; do not preload OpenSpec context for unrelated reviews.
- If a durable inbox review artifact is requested, follow `inbox/AGENTS.md` and the review guideline. Review persistence remains with the caller or downstream workflow, not the reviewer subagents.

Stop loading when the review target, contract, scope, and result consumer are sufficiently identified.

## Independent Review Entry

At a top-level review boundary, do not perform a dual-perspective review in the same context when the repository's `review-lead` subagent is available.

1. Delegate the bounded review to `review-lead` with the target/revision or observable state, intended behavior, scope, applicable contract, and known validation evidence.
1. Do not call `review-quality` or `review-adversarial` directly; their access is intentionally mediated by `review-lead` in VS Code.
1. Consume the lead's `Reviewed` state, `Assessment`, findings, validation, coverage gaps, and unknowns without silently upgrading incomplete coverage.
1. If the reviewed state changes materially, treat the prior assessment as stale and review the new state when a current independent assessment is required.

When `review-lead` or required subagent capabilities are unavailable, use the applicable review methodology only within the caller's authority and report that the dual-perspective independent orchestration was not performed. Do not describe a same-context fallback as equivalent independent review.

## Boundary

- This Skill selects review context and the top-level review entrypoint; it does not own code-review methodology, severity policy, VCS lifecycle, OpenSpec planning, or review artifact format.
- Do not re-delegate when already executing as `review-lead`, `review-quality`, or `review-adversarial`.
- Do not turn a review request into implementation or modify the reviewed target.
- Do not require OpenSpec, GitHub, or an inbox artifact when the actual review target does not need them.
- VS Code-specific subagent access control does not imply equivalent enforcement in other runtimes.
