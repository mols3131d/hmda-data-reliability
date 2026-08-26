---
name: prj-load-context-development
description: >-
  Load repository development context for code-facing implementation work: writing or
  changing application code or tests, refactoring, debugging implementation behavior,
  changing runtime or code-facing configuration, package/module structure, dependencies,
  or other implementation behavior. Use alongside more specific context Skills such as
  testing or Git/GitHub when those concerns also apply. Do not use for review-only,
  research-only, documentation-only, or repository administration work with no
  implementation surface.
targets: [claudecode, codexcli, copilot, antigravity-ide, antigravity-cli]
---

# Development Context

Load the smallest repository development context needed for the active implementation task. Canonical repository documents own detailed architecture, tooling, testing, and workflow rules; this Skill selects only the context that materially affects implementation.

## Load Context

- Read [`DEVELOPMENT.md`](../../../DEVELOPMENT.md) for active runtime, package layout, tool choices, code convention, and development commands that affect the task.
- Read [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md) when the change touches system boundaries, domain ownership, orchestration, persistence, cross-package dependencies, or placement of new responsibility.
- Read [`docs/mvp.md`](../../../docs/mvp.md) only when current MVP scope or acceptance can change the implementation decision.
- For test design, test implementation, pytest execution, or validation details, use `prj-load-context-testing`; do not duplicate its testing contract here.
- For branch, commit, Pull Request, review delivery, merge, or mutable GitHub state, use `prj-vcs-git-github`; do not duplicate VCS policy here.
- For each known target path, keep applicable path-scoped `AGENTS.md` and Rule context in force through the repository's normal routing mechanism.

Stop loading when additional context is unlikely to change the next implementation decision.

## Implementation Defaults

- Prefer an existing domain, package, abstraction, dependency, and project-native mechanism before creating a new owner.
- Keep changes inside the requested behavior and any governing accepted plan. Do not widen scope for adjacent cleanup or speculative architecture.
- Preserve existing public contracts unless the task explicitly changes them.
- Use the repository's active toolchain rather than introducing an alternative for convenience.
- Apply KISS, DRY, and YAGNI; add indirection only when it removes a concrete responsibility or duplication problem.

## Independent Review Gate

For code-facing implementation, test, runtime, or code-facing configuration changes, self-review by an implementation context does not count as independent Review.

The agent or workflow that owns the **final implementation completion decision** performs this gate. A bounded implementation specialist may return its handoff to that owner without starting another review workflow itself.

Before declaring the implementation complete, when the runtime supports subagents:

1. delegate one bounded review to `review-lead` in a separate subagent context;
1. pass only the target/revision or observable state, intended behavior, active scope, applicable contract, and validation already performed;
1. let `review-lead` coordinate its own specialist reviewers and return the reconciled assessment;
1. route material findings back to the implementation owner, then invoke a fresh `review-lead` review after material fixes when Review is still required.

Do not call `review-quality` or `review-adversarial` directly from the implementation workflow when `review-lead` is available. If `review-lead` or required nested subagent invocation is unavailable, report the independent-review coverage gap instead of presenting self-review as independent Review.

## Boundary

- This Skill loads and anchors implementation context; it does not replace architecture, testing, VCS, OpenSpec, or review methodology owners.
- Loading context does not expand write authority or task scope.
- Do not copy detailed rules from canonical documents into this Skill merely to avoid loading them.
- Do not require every development document for every implementation task.
- Do not claim runtime delegation, validation, or reviewer independence that was not actually observed.
- The intended `review-lead`-only specialist route is a workflow contract, not a per-parent access-control guarantee; do not infer stronger runtime isolation than the active harness provides.
