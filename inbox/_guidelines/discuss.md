# Discuss

Use `discuss` when the primary purpose is to exchange and refine positions before a human or owning workflow makes a decision.

Discussion is not Research, Review, or a canonical decision. Route substantial evidence gathering to `research`, target evaluation and findings to `review`, and accepted normative outcomes to their owning artifact.

## Roles

Every structured discussion has three roles.

- **Moderator**: frames the question, chooses the discussion type and exchange pattern, keeps shared context stable, opens and closes rounds, and synthesizes the result. The Moderator does not manufacture disagreement or silently turn its own preference into a decision.
- **A** and **B**: independent participants. They argue from evidence and project constraints, respond to the strongest opposing point, and may change position when the evidence warrants it.

`A` and `B` identify participants, not fixed sides. A participant may support, oppose, combine, or revise an option during the discussion.

## Discussion Types

Choose the smallest type that matches the purpose. Types may be composed when the transition is explicit.

| Type | Use when | Expected result |
| --- | --- | --- |
| `explore` | useful options or problem framing are still unclear | candidate directions and material unknowns |
| `compare` | known alternatives need trade-off comparison | criteria-based comparison and preferred options |
| `debate` | a contested proposition needs independent challenge | strongest arguments, counterarguments, and changed positions |
| `challenge` | a leading proposal needs stress-testing before adoption | failure modes, weak assumptions, and conditions for acceptance |
| `converge` | prior discussion already exists and the remaining task is to narrow disagreement | agreements, residual disagreements, and human decision points |

Do not force a debate when participants already converge. Do not use `explore` to hide a question that actually needs Research.

## Exchange Patterns

Discussion type and exchange pattern are independent.

- **One-shot**: A and B respond independently once, then the Moderator synthesizes. Use for cheap comparisons or early orientation.
- **Cross-review**: A and B start independently, then each reads the other's strongest case and responds once. Use as the default for consequential decisions.
- **Iterative**: participants alternate or cross-review for multiple rounds until a stop condition is met. Use only when each round can materially change the result.

The default maximum is **3 rounds per decision**. Additional rounds require new evidence, a verified correction, a new human constraint, or a material narrowing of disagreement.

## Cadence

Cadence controls when rounds run; it does not define the discussion type.

- **Manual**: the human or Moderator explicitly advances each round.
- **Scheduled**: automations run rounds asynchronously at predefined times or intervals.

Scheduled discussion is useful when latency is acceptable and human presence is unnecessary between rounds. Overnight discussion is one scheduled use case, not the default discussion model.

For scheduled discussion:

- the Moderator owns the active decision, next actor, round limit, and stop state;
- each run reads the latest shared state before writing;
- A and B write only to their own round output;
- a run produces no new round when there is no material delta or when the discussion is stopped;
- schedules must leave enough separation for the prior write to become visible before the next participant reads it.

## Shared Context

Before the first round, the Moderator establishes only the context needed for the decision:

- question or decision ID;
- scope and explicit non-goals;
- current evidence snapshot or canonical references;
- options or proposition when already known;
- discussion type, exchange pattern, cadence, and round limit;
- who has final decision authority.

A bundle may separate context, topics, rounds, synthesis, and decision log into files. Exact filenames are flexible, but their ownership must remain clear.

## Write Ownership

- The Moderator owns shared context, round control, synthesis, and discussion status.
- A owns only A's round outputs; B owns only B's round outputs.
- Participants do not rewrite the other's output or previously consumed rounds. Corrections go into a later round.
- GPT agreement never edits a human-owned decision into `Accepted` unless the human explicitly authorizes it.

This separation is required when multiple chats or scheduled runs can write concurrently.

## Participant Contract

A useful contribution should contain only what changes the discussion:

- current position;
- evidence or project constraint that supports it;
- response to the strongest opposing point when one exists;
- any concession or changed assumption that matters;
- current proposal to the decision maker;
- unresolved question only when it can change the choice.

Do not repeat an earlier position with different wording. Distinguish repository facts from inference and preference.

## Moderator Contract

The Moderator:

1. chooses the discussion type and exchange pattern from the decision's uncertainty and cost;
2. gives A and B the same shared context for independent first positions when independence matters;
3. keeps arguments scoped to the active decision;
4. checks after each round whether a material delta remains;
5. stops rather than extending a discussion for symmetry or volume;
6. synthesizes both participants fairly, including concessions and unresolved disagreement;
7. routes unanswered factual questions to Research when more evidence is required;
8. leaves the final decision to the declared decision authority.

## Stop Conditions

Stop a discussion when any of the following is true:

- A and B converge on the same material proposal;
- the remaining difference is a human priority, risk tolerance, or preference;
- new evidence is required before reasoning can advance;
- the latest round adds no material information;
- the configured round limit is reached;
- the decision authority decides or closes the topic.

The result may be agreement, disagreement, or a request for Research. Convergence is useful but not mandatory.

## Output

The Moderator's synthesis should make the decision cheaper for a human to review. Prefer:

- current recommendation or viable options;
- strongest evidence for each material position;
- points of agreement;
- remaining disagreement and the assumption causing it;
- new Research or validation needed, if any;
- the exact human decision still required.

## Boundaries

- Do not use role assignment to force theatrical opposition.
- Do not let `discuss` become an unbounded brainstorming log.
- Do not treat scheduled repetition as deeper reasoning by itself.
- Do not create a new canonical requirement or project decision inside the discussion artifact.
- Follow the common artifact and lifecycle rules in `inbox/AGENTS.md`.
