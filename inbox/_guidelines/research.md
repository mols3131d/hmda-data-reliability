# Research

Use `research` when the artifact's primary purpose is to answer a question by gathering and validating evidence before a decision, specification, or implementation.

## Contract

- State the question and relevant scope.
- Check current behavior and existing evidence before adding new investigation.
- Distinguish verified facts, inference, assumptions, and unresolved uncertainty when material.
- Connect important conclusions to evidence that can be checked again.
- Compare alternatives only when they can change the answer or decision.
- Stop when additional investigation is unlikely to change the answer or a material uncertainty.

## Resources

- Template: [`inbox/_templates/research.md`](../_templates/research.md)
- Skill: `pivot-research-workspace` when evidence-backed investigation of current behavior, scope, dependencies, alternatives, or failures is useful.

Use only the resources that help answer the research question. Adapt or omit template sections that do not serve it.

## Output

Lead with the evidence-backed answer. Include only the context, evidence, alternatives, and uncertainty needed for the artifact's purpose.

Research supports decisions but does not make requirements, design, implementation, or project documentation canonical by itself.

## Boundaries

- Do not use `research` for a simple reference dump or summary with no investigation question.
- Do not expand into unrelated repository-wide investigation.
- Do not present unverified assumptions as repository facts.
- Follow the common artifact and lifecycle rules in `inbox/AGENTS.md`.
