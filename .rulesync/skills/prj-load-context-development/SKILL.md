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
---

# Development Context

Load the smallest repository development context needed for the active implementation task. Canonical repository documents own detailed architecture, tooling, testing, and workflow rules; this Skill selects only the context that materially affects implementation.

## Load Context

- Read [`DEVELOPMENT.md`](../../../DEVELOPMENT.md) for active runtime, package layout, tool choices, code convention, and development commands that affect the task.
- Read [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md) when the change touches system boundaries, domain ownership, orchestration, persistence, cross-package dependencies, or placement of new responsibility.
- Read [`docs/mvp.md`](../../../docs/mvp.md) only when current MVP scope or acceptance can change the implementation decision.
- For test design, test implementation, pytest execution, or validation details, use `prj-testing-context`; do not duplicate testing context routing here.
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

Before declaring the implementation complete, when the runtime supports the repository's review subagents:

1. load `prj-load-context-review` for caller-owned finding admission and assessment policy, then delegate one bounded review to `mols-review-dualvantage` in a separate subagent context;
1. pass only the target/revision or observable state, intended behavior, active scope, applicable contract, and validation already performed;
1. let `mols-review-dualvantage` coordinate its own Verifier and Challenger and adjudicate technical candidate claims, then apply `prj-load-context-review` to classify findings and produce the caller-owned `Assessment`;
1. admit review output against the current task authority before any remediation:
   - `current_required` — remediate only when the action stays inside the current user boundary and governing plan/contract;
   - `scope_decision` — do not mutate. Route to the workflow that owns Scope Control when one exists; otherwise require the authority that owns the affected Goal, scope or contract;
   - `follow_up` or `unrelated` — do not absorb into the current implementation;
   - `unknown` — gather only evidence needed to decide the current Goal when that uncertainty blocks completion; otherwise preserve it as a limitation;
1. handle the assessment after admission:
   - `clear` — the independent review gate is satisfied for the exact reviewed state, subject to reported limitations;
   - `changes_required` — remediate admitted `current_required` findings, then obtain a fresh DualVantage handoff and caller assessment only if the reviewed state materially changed;
   - `blocked` — this assessment takes precedence for completion, so the independent review gate remains unsatisfied. Resolve or route the identified evidence, coverage or scope-authority blocker. A confirmed `current_required` item may still receive bounded remediation before blocker resolution only when its validity does not depend on that blocker and the action stays fully inside current authority; otherwise preserve it for the next admissible implementation step.

If bounded remediation occurs while the same blocker still prevents gate closure, do not re-run independent review solely because that state changed. Resolve the blocker first, then review the resulting state once when a current independent assessment can materially change the completion decision.

If a review output lacks an explicit disposition, the completion owner must classify each finding against the active scope and authority before mutation. `changes_required` alone is not permission to implement every returned item.

A user-defined `Out of scope`, explicit no-expansion instruction, Goal or Acceptance boundary cannot be widened by reviewer discovery. Review may expose a necessary scope decision, but only the owning authority or workflow may admit that expansion.

Any post-review change that can affect reviewed behavior, contract, validation evidence or finding disposition invalidates the prior assessment for completion purposes. Conversely, do not re-run independent review merely for additional confidence when no such material state change occurred.

A repeated or rephrased candidate that adds no new material evidence, creates no admitted `current_required` finding and does not change the current blocker is not a reason for another remediation/re-review cycle. Preserve non-blocking follow-ups separately and stop the automatic review loop at the current gate state.

Do not call `mols-review-dualvantage-verifier` or `mols-review-dualvantage-challenger` directly. They belong to the DualVantage Root; runtime capability restrictions may differ. If `mols-review-dualvantage`, its specialist delegation, or required nested subagent invocation is unavailable, report the independent-review coverage gap instead of presenting self-review as independent Review.

## Boundary

- This Skill loads and anchors implementation context; it does not replace architecture, testing, VCS, OpenSpec, or review methodology owners.
- Loading context does not expand write authority or task scope.
- Do not copy detailed rules from canonical documents into this Skill merely to avoid loading them.
- Do not require every development document for every implementation task.
- Do not claim runtime delegation, validation, or reviewer independence that was not actually observed.
- VS Code-specific subagent access control does not imply equivalent enforcement in other runtimes.
