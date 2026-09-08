# Research

Use `research` when the artifact's primary purpose is to answer a material question with evidence before a decision, specification, or implementation.

Research is a working, non-canonical artifact. It supports later judgment but does not make requirements, design, implementation, or project documentation canonical by itself.

## Contract

- State one core question and the scope needed to answer it.
- Lead with the current evidence-backed answer instead of the investigation sequence.
- Keep verified facts, inference, assumptions, conflicts, and unresolved uncertainty distinguishable when material.
- Connect important conclusions to evidence that can be checked again.
- Include only alternatives, implications, and open questions that can materially change the answer or downstream judgment.
- Preserve important limits on the answer instead of converting missing evidence into confidence.

## Frontmatter

Follow the common Inbox artifact contract in [`inbox/AGENTS.md`](../AGENTS.md). Research-specific frontmatter adds no required fields beyond `type: research`.

Use `description` to identify the research question and the judgment or use it supports. Do not use it as a second conclusion summary.

Do not add `status` by default. Inbox is not a canonical status projection, and research completion or blocking state belongs in the current answer and applicable workflow unless another governing contract explicitly requires metadata.

`tags` remains optional and follows the common Inbox contract. This guideline does not define a separate research taxonomy.

## Structure

Optimize the artifact for a reader who needs to recover the answer, inspect the strongest evidence, understand what it changes, and identify material uncertainty without reading the document from start to finish.

Use the template's structure in this order:

1. leading answer callout
1. `Question`
1. `Scope`
1. `Findings`
1. optional `Options`
1. optional `Implications`
1. optional `Open Questions`

The leading callout owns the current answer. Do not add a second `Conclusion` section that repeats it.

Add a task-specific section only when it owns material information that does not fit the standard sections. Do not duplicate or casually rename an existing section responsibility.

### Question and Scope

Keep the core question explicit and narrow enough to answer with evidence. Use `Scope` for the included boundary and retain `Out of Scope` only when omission could otherwise be misread as incomplete research.

Do not print the investigation stop condition as a document section. Investigation mechanics and stopping rules belong to the research workflow, not the reader-facing result.

### Findings

Use H3 headings that state the finding itself rather than generic labels such as `Finding 1` or `Analysis`.

Stable IDs such as `F1` are optional. Use them only when findings need repeated cross-reference across a long artifact, discussion, or follow-up work.

Use prose to explain what was observed, what is inferred, and why it matters to the research question. Do not force every finding into repeated `Evidence` and `Implication` subsections when the meaning is already clear.

### Evidence

Keep evidence close to the claim it supports and preserve enough locator information to verify the conclusion again.

For a simple finding with one or two sources, an inline link or footnote may be sufficient. Use an `Evidence` H4 when grouping several sources, files, tests, requirements, observations, or locators materially improves readability.

When using an `Evidence` section:

- use the source, file, artifact, Pull Request, Issue, or external document as the top-level bullet;
- put symbols, tests, requirements, sections, line references, or concise observations under the source as nested bullets;
- link directly navigable targets when a stable link is available;
- keep exact path and identifier spelling;
- avoid repeating multiple sources that establish the same fact without adding verification value.

Footnotes are for supporting provenance, secondary evidence, exceptions, or detail that would interrupt the main flow. Do not hide the core evidence, material uncertainty, or a result-changing conflict in a footnote.

### Options

Keep `Options` only when multiple plausible alternatives can materially change the answer or downstream judgment.

Use a table when the alternatives share comparable criteria. Use prose or bullets when the alternatives have different structures or a table would make the comparison harder to read.

Do not collect options for completeness after the question is already answered by stronger evidence.

### Implications

Use this optional section when the research result materially changes a downstream decision, plan, specification, validation target, or work boundary.

State what the evidence means for the next judgment without turning the research artifact into the canonical decision or requirement. Do not add a fixed `Next Step` section when there is no meaningful next action.

Use prose for one implication and bullets for several peer implications or follow-up actions.

### Open Questions

Keep only unresolved questions or conflicts that can still change the answer, confidence, scope, or downstream judgment.

When useful, nest under each question the evidence, decision, access, or observation needed to resolve it. Do not use this section as a backlog of unrelated improvements.

## Investigation and Completion

Use `prj-research-workspace` when evidence-backed investigation of current behavior, scope, dependencies, alternatives, or failures is useful. That workflow owns evidence search, rigor, conflict handling, stop conditions, and completion semantics; this guideline owns the Inbox research artifact's content and presentation contract.

The artifact should preserve the synthesized result, not reproduce the investigation log. Raw logs, large generated output, exhaustive link collections, and detailed activity history should not be embedded unless they are themselves necessary evidence. Prefer a reproducible locator, command, or supporting artifact.

## Resources

- Template: [`inbox/_templates/research.md`](../_templates/research.md)
- Skill: `prj-research-workspace`

Use only the resources that serve the research question. Optional template sections may be omitted when they do not improve the result.

## Boundaries

- Do not use `research` for a simple reference dump or summary with no investigation question.
- Do not broaden into unrelated repository-wide investigation.
- Do not present unverified assumptions as repository facts.
- Do not turn the artifact into a chronological work log when the reader needs a synthesized answer.
- Do not treat the research artifact as the canonical requirement, design, implementation plan, or project decision.
- Follow the common artifact and lifecycle rules in `inbox/AGENTS.md`.
