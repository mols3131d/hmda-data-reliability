---
name: prj-load-context-review
description: >-
  Load repository context and orchestration for top-level independent review of a bounded
  technical change or artifact, including pull requests, diffs, files, commits, working
  tree changes, implementation, tests, runtime, or code-facing configuration. In VS Code,
  route dual-perspective review through mols-review-dualvantage when available. The caller
  retains project review policy and assessment. Do not use for implementation self-review.
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

At a top-level independent review boundary, the caller owns the project's review gate. `mols-review-dualvantage` provides independent technical analysis and evidence adjudication; it does **not** return a project-level review decision.

1. Delegate one bounded review to `mols-review-dualvantage` in a separate subagent context. Provide the target/revision or observable state, intended behavior, in/out scope, applicable contract and instructions, and known validation and limitations.
1. Provide the project's review-local admission and assessment criteria below as **caller policy**, not as instructions to redefine DualVantage's internal evidence states.
1. Do not invoke `mols-review-dualvantage-verifier` or `mols-review-dualvantage-challenger` directly. DualVantage owns dispatch and independent candidate adjudication.
1. Consume confirmed material candidates, decision-relevant unresolved items, state basis, validation, coverage gaps and unknowns; do not treat the Root's `confirmed | rejected | merged | unresolved` as project finding dispositions or final status.
1. Apply the following caller-owned admission and assessment. If the reviewed state changes materially, the previous result becomes stale.

If delegation, worker coverage or independence is unavailable, report the specific gap. Same-context review does not satisfy an independent dual-perspective gate.

## Finding Admission

The caller checks each surviving candidate against the authorized Goal, In Scope, Out of Scope, Acceptance and contract-change boundary before deciding whether remediation is required. Candidate confirmation establishes evidence, **not** permission to change the target.

최종 assessment 전에 살아남은 candidate마다 `Scope relation`과 `Disposition`을 판정한다.

| Disposition | Use when |
| --- | --- |
| `current_required` | 현재 승인된 Goal, In Scope, Out of Scope, Acceptance와 authorized contract-change boundary 안에서 해결할 수 있는 explicit target defect, current change가 만든 reachable regression 또는 contract/acceptance gap이며, current Goal을 accept하려면 반드시 닫아야 한다. |
| `scope_decision` | 해결하려면 Goal, In Scope, Out of Scope, Acceptance 또는 authorized contract-change boundary를 넓혀야 하며 그 변경 권한이 review에 없다. |
| `follow_up` | 유용하거나 material할 수 있지만 current Goal을 완료하는 데 필수적이지 않은 독립 요구사항 또는 개선이다. |
| `unrelated` | pre-existing issue이거나 current target과 causal/material relation이 없다. |
| `unknown` | 필요한 evidence가 없어 current Goal과의 relation 또는 impact를 확정할 수 없다. |

`Scope relation`은 가능한 경우 `explicit_target`, `direct_regression`, `contract_dependency`, `acceptance_gap`, `scope_change`, `independent_requirement`, `unrelated`, `unknown` 중 가장 가까운 하나로 기록한다.

Disposition은 materiality보다 authority boundary를 먼저 판정한다. Task가 contract 변경 자체를 명시적으로 승인한 경우에는 그 authorized delta 안의 correction을 scope expansion으로 취급하지 않는다.

1. 해결에 authorized Goal, In Scope, Out of Scope, Acceptance 또는 contract-change boundary의 확대가 필요하면, current Goal에 중요하거나 필수적이어도 먼저 `scope_decision`으로 분류한다.
1. 그런 확대 없이 현재 authority 안에서 해결할 수 있고 current Goal을 accept하려면 반드시 닫아야 하면 `current_required`로 분류한다.
1. Current Goal에 필수적이지 않은 독립 요구사항이나 개선이면 `follow_up`, causal/material relation이 없으면 `unrelated`, 필요한 evidence가 부족하면 `unknown`으로 분류한다.

Admission 규칙은 다음과 같다.

- `current_required`만 `changes_required`의 근거가 된다.
- `scope_decision`은 review가 scope expansion을 승인하지 않는다. Current Goal이 그 결정 없이는 accept될 수 없을 때만 `blocked`의 근거가 되며, 그렇지 않으면 `follow_up`으로 낮춘다.
- `follow_up`과 `unrelated`는 severity가 높아도 current remediation 권한을 만들거나 `clear`를 `changes_required`로 바꾸지 않는다.
- `unknown`은 current Goal 판단에 필요한 evidence gap일 때만 `blocked`의 근거가 되며, 그렇지 않으면 limitation으로 남긴다.
- Severity는 impact를 표현할 뿐 scope authority를 부여하지 않는다.

세 번째 full review를 새로 수행하지 않는다. Caller의 직접 분석은 candidate claim 검증, conflict resolution, admission과 coverage 확인에 한정한다.



## Assessment

The caller returns **Reviewed** (target and exact revision/version/observable state) and one **Assessment**: `clear | changes_required | blocked`.

Priority order:

1. `blocked` if missing scope authority, decision-relevant evidence or required independent specialist coverage prevents closing the current Goal's review gate, even when a confirmed `current_required` exists;
1. otherwise `changes_required` if any confirmed `current_required` remains;
1. otherwise `clear`.

Report admitted material items with disposition, scope relation, affected surface, decisive evidence, reachability and impact. State validation performed/not run, coverage gaps and unresolved unknowns. `scope_decision`, `follow_up`, `unrelated` and non-blocking `unknown` do not silently authorize current remediation. Review does not mutate or approve the target.

## Boundary

- This Skill selects review context, the top-level review entrypoint and caller-owned assessment policy; it does not own code-review methodology, severity policy, VCS lifecycle, OpenSpec planning, or review artifact format.
- Do not re-delegate when already executing as `mols-review-dualvantage` or one of its internal specialists.
- Do not turn a review request into implementation or modify the reviewed target.
- Do not require OpenSpec, GitHub, or an inbox artifact when the actual review target does not need them.
- VS Code-specific subagent access control does not imply equivalent enforcement in other runtimes.
