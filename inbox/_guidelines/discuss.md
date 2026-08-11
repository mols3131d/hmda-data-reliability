# Discuss

Use `discuss` when the primary purpose is to exchange and refine positions before a human or owning workflow makes a decision.

Discussion is not Research, Review, or a canonical decision. Route substantial evidence gathering to `research`, target evaluation and findings to `review`, and accepted normative outcomes to their owning artifact.

## Roles

Every structured discussion has three logical roles.

- **Moderator**: frames the question, chooses the discussion type and exchange pattern, controls scope and rounds, and synthesizes the result.
- **A** and **B**: independent participants. They argue from evidence and project constraints and may change position when warranted.

`A` and `B` identify participants, not fixed sides. Do not force artificial opposition.

The Moderator is a **coordination role, not necessarily a separate agent, chat, or scheduled task**. Its responsibilities may be carried by the human, one participant at an explicit boundary, or deterministic protocol. Use a separate Moderator execution only when independent synthesis or active coordination materially improves the discussion.

## Discussion Types

Choose the smallest type that matches the purpose. Types may transition when the change is explicit.

| Type | Use when | Expected result |
| --- | --- | --- |
| `explore` | useful options or framing are unclear | candidate directions and material unknowns |
| `compare` | known alternatives need trade-off comparison | criteria-based comparison and preferred options |
| `debate` | a contested proposition needs independent challenge | strongest arguments, counterarguments, changed positions |
| `challenge` | a leading proposal needs stress-testing | weak assumptions, failure modes, acceptance conditions |
| `converge` | prior discussion exists and disagreement needs narrowing | agreements, residual disagreements, human decision points |

Do not use `explore` to hide a question that actually needs Research.

## Exchange Patterns

Discussion type and exchange pattern are independent.

- **One-shot**: A and B respond independently once, then synthesize.
- **Cross-review**: A and B start independently, then each responds once to the other's strongest case. Default for consequential decisions.
- **Iterative**: A and B continue for multiple rounds while each round can materially change the result.

Default maximum: **3 rounds per decision**. Extend only for new evidence, a verified correction, a new human constraint, or material narrowing of disagreement.

## Cadence

Cadence controls when participant turns run.

- **Manual**: the human or Moderator advances turns.
- **Scheduled**: automations run turns asynchronously at predefined times or intervals.

Overnight discussion is one scheduled use case, not the default discussion model.

## Scheduled Discussion

Use scheduled discussion when a human does not need to intervene between turns and repository artifacts can carry the shared context.

A separate Moderator schedule is not required. Prefer two participant schedules when independent A/B execution matters; assign synthesis to one participant or a later human action.

### Model

Treat **one scheduled run as one complete participant turn**:

```text
read → check turn → reason/research → write → review → commit/push → exit
```

Do not keep a run alive to fill time, wait for the other participant, or attempt multiple delayed turns. Time values are soft work budgets, not guaranteed runtime.

Prefer staggered schedules:

```text
A schedule ── A1 ───── A2 ───── A3
                 │        │
B schedule ───── B1 ───── B2 ───── B3
```

If each schedule can run only hourly, offsetting A and B by 30 minutes yields a 30-minute exchange cadence. Do not emulate a denser cadence with internal waiting; use more scheduler capacity or another orchestrator when necessary.

### Configuration

Keep scheduler timing outside reusable discussion behavior. The active bundle only needs execution-relevant configuration, for example:

```yaml
discussion:
  id: <discussion-id>
  decision: <decision-id>
  type: debate
  exchange: iterative
  cadence: scheduled
  first_round: independent
  max_rounds: 3
  round_work: rpi-loop
  rpi_budget_minutes: 10
  turn_budget_minutes: 14
  synthesis_owner: B
  decision_authority: human
```

`rpi_budget_minutes` and `turn_budget_minutes` are optional **soft budgets**. Finish early when the turn is complete. Never implement them as sleep or deliberate delay.

`round_work: rpi-loop` means the participant uses the project's RPI loop to improve the current turn only. It does not expand discussion scope or authorize unrelated implementation.

### Run Contract

On every scheduled invocation:

1. Read this guideline, active configuration, shared context, and existing rounds.
2. Exit without a discussion write when synthesis already exists, this turn already exists, or the required preceding turn is missing.
3. Determine the next eligible round for this actor.
4. Refresh only evidence that can materially change the active decision.
5. If configured, run the RPI loop as a bounded improvement loop for this round.
6. Write one immutable participant round following the Participant Contract.
7. Self-review for unsupported claims, repetition, and whether the turn adds a material delta.
8. Commit and push the completed turn as one reviewable unit.
9. If this actor owns synthesis and a Stop Condition is met, synthesize when both sides can be represented fairly.
10. Exit. Never wait inside the run for the other participant.

When using RPI inside a turn, preserve only conclusions, evidence, changed assumptions, and reviewable rationale. Do not expose private chain-of-thought.

### Turn Order

For normal iterative exchange:

```text
A1 → B1 → A2 → B2 → ... → synthesis
```

- A1 starts only when A1 does not exist.
- B1 starts after A1 exists. With `first_round: independent`, B records its own initial position without using A1's argument content.
- A<n> starts only after B<n-1> exists and A<n> does not.
- B<n> starts only after A<n> exists and B<n> does not.

These checks make scheduled turns idempotent and allow a missed run to recover later without inventing missing rounds.

### Commit And Recovery

Prefer **one participant turn = one commit**. Include only that round and, when owned by the same turn, its synthesis or control update.

- Missing prerequisite → no-op; retry on the next scheduled run.
- Duplicate invocation → no-op if the intended output exists.
- Stale repository state → refresh before writing.
- Write conflict → preserve existing outputs; never overwrite the other participant's round.
- Missing material evidence → record the Research need and recommend stopping.
- Round limit reached → synthesize remaining agreement and disagreement rather than extending automatically.

### Scheduled Task Prompt

Participant schedules should differ only by actor identity, timing, and active bundle path. Keep reusable behavior here.

```text
Act as participant <A|B> for the active scheduled discussion.
Read inbox/_guidelines/discuss.md and the discussion bundle first.
Run only when your next turn is eligible; otherwise make no discussion write.
Use the configured round_work and soft budgets for one complete turn.
Write only your participant output, self-review it, commit and push the turn,
and exit without waiting for the other participant.
If you own synthesis and a stop condition is reached, write the synthesis.
Never accept the human decision on the user's behalf.
```

## Shared Context

Before the first round, establish only what the decision needs:

- question or decision ID;
- scope and explicit non-goals;
- current evidence snapshot or canonical references;
- options or proposition when already known;
- discussion type, exchange pattern, cadence, and round limit;
- final decision authority.

A bundle may separate context, topics, configuration, rounds, synthesis, and decision log. Exact filenames are flexible, but ownership must remain clear.

## Write Ownership

- The Moderator role owns shared context, round control, synthesis, and discussion status.
- A owns only A's round outputs; B owns only B's round outputs.
- Without a separate Moderator execution, assign Moderator writes only at explicit protocol boundaries.
- Do not rewrite another participant's output or a previously consumed round. Correct errors in the next round.
- GPT agreement never changes a human-owned decision to `Accepted` without explicit human authorization.

## Participant Contract

A useful contribution contains only what changes the decision:

- current position;
- material evidence or project constraint;
- response to the strongest opposing point when one exists;
- concessions or changed assumptions;
- current proposal;
- unresolved question only when it can change the choice;
- continue or synthesize recommendation when rounds are iterative.

Distinguish repository facts from inference and preference. Do not repeat an earlier position with different wording.

## Moderator Contract

The Moderator role:

1. chooses type and exchange pattern from uncertainty and decision cost;
2. gives A and B equivalent context when independent positions matter;
3. keeps discussion scoped to the active decision;
4. stops when another round has no material value;
5. synthesizes both sides fairly, including concessions and unresolved disagreement;
6. routes unanswered factual questions to Research when needed;
7. leaves the final decision to the declared decision authority.

These are coordination responsibilities, not a requirement for a dedicated Moderator invocation.

## Stop Conditions

Stop when any of the following is true:

- A and B converge on the same material proposal;
- the remaining difference is human priority, risk tolerance, or preference;
- new evidence is required before reasoning can advance;
- the latest round adds no material information;
- the configured round limit is reached;
- the decision authority closes the topic.

The result may be agreement, disagreement, or a Research request. Convergence is useful but not mandatory.

## Synthesis

Make the human decision cheaper to review. Prefer:

- current recommendation or viable options;
- strongest evidence for each material position;
- points of agreement;
- remaining disagreement and its underlying assumption;
- Research or validation still needed;
- the exact human decision still required.

Synthesis is not a canonical decision.

## Boundaries

- Do not require a separate Moderator execution when protocol is sufficient.
- Do not force theatrical opposition.
- Do not let `discuss` become an unbounded brainstorming log.
- Do not treat scheduled repetition or elapsed time as deeper reasoning by itself.
- Do not create canonical requirements or decisions inside the discussion artifact.
- Follow the common artifact and lifecycle rules in `inbox/AGENTS.md`.
