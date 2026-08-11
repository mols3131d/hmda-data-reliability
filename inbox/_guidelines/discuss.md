# Discuss

Use `discuss` when the primary purpose is to exchange and refine positions before a human or owning workflow makes a decision.

Discussion is not Research, Review, or a canonical decision. Route substantial evidence gathering to `research`, target evaluation and findings to `review`, and accepted normative outcomes to their owning artifact.

## Roles

Every structured discussion has three logical roles.

- **Moderator**: frames the question, chooses the discussion type and exchange pattern, keeps shared context stable, opens and closes rounds, and synthesizes the result. The Moderator does not manufacture disagreement or silently turn its own preference into a decision.
- **A** and **B**: independent participants. They argue from evidence and project constraints, respond to the strongest opposing point, and may change position when the evidence warrants it.

`A` and `B` identify participants, not fixed sides. A participant may support, oppose, combine, or revise an option during the discussion.

The Moderator is a **coordination role, not necessarily a separate agent, chat, or scheduled task**. Its responsibilities may be carried by the human, one participant at a defined boundary, or deterministic discussion state and protocol. Use a separate Moderator execution only when independent synthesis or active coordination materially improves the discussion.

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
- **Scheduled**: automations run participant turns asynchronously at predefined times or intervals.

Overnight discussion is one scheduled use case, not the default discussion model.

## Scheduled Discussion

Use scheduled discussion only when a human does not need to intervene between participant turns and repository artifacts can carry the shared context.

A scheduled discussion does **not** require a third schedule for the Moderator. Prefer two participant schedules when independent A/B execution matters. Moderator responsibilities are carried by the discussion configuration, turn rules, stop conditions, and the participant assigned to synthesis.

### Scheduling Model

Treat **one scheduled run as one complete participant turn**.

A run should:

1. read the latest discussion artifacts;
2. determine whether this participant has an eligible turn;
3. inspect only the evidence needed for that turn;
4. perform the configured reasoning or RPI loop;
5. write and self-review one round output;
6. commit and push the completed turn;
7. exit.

Do not keep a run alive merely to fill a target duration, sleep until the other participant acts, or attempt multiple delayed turns inside one run. A configured time budget is a **soft upper budget for prioritization**, not a guaranteed runtime or a requirement to consume that time.

### Schedule Topology

Prefer **two staggered participant schedules**:

```text
A schedule ── A1 ───── A2 ───── A3
                 │        │
B schedule ───── B1 ───── B2 ───── B3
```

Each participant schedule may run less frequently than the desired A↔B exchange interval because the two schedules are offset from each other.

For example, when a scheduler allows each task to run only once per hour, hourly A and B schedules offset by 30 minutes produce a 30-minute participant exchange cadence.

Do not simulate a denser cadence by asking a scheduled run to wait internally. If the scheduler cannot represent the desired cadence with the available task slots, accept a slower cadence or use a different orchestrator.

### Discussion Configuration

Before scheduling begins, establish stable configuration that participants read but do not opportunistically rewrite:

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

Only include fields that affect execution. Exact storage format and filename may vary by bundle.

`round_work: rpi-loop` means the participant uses the project's RPI loop to improve its turn before publishing it. It does not authorize unrelated implementation or broaden the active discussion scope.

`rpi_budget_minutes` and `turn_budget_minutes` are optional **soft budgets**. They tell the participant how to prioritize effort when execution time is limited. They must never be implemented as sleeping, deliberate delay, or a claim that the scheduler guarantees that runtime. Finish early when the turn is complete; prefer a complete, reviewable turn over exhausting the budget.

### Turn Eligibility

A scheduled run must be idempotent. It writes only when its expected input state exists and its own output for that turn does not already exist.

For a normal A→B iterative sequence:

- A1 may start when the discussion is open and A1 does not exist.
- B1 may start after A1 exists. When `first_round: independent`, B1 must not use A1's argument content before recording its own first position.
- A2 starts only after B1 exists and A2 does not exist.
- B2 starts only after A2 exists and B2 does not exist.
- Continue until a stop condition or `max_rounds` is reached.

If the prerequisite output is missing, the discussion is already synthesized, or this turn already exists, perform no discussion write and exit cleanly.

### Turn Work

When `round_work: rpi-loop`, use the RPI loop inside the turn as a **bounded improvement loop**, not as a reason to expand scope.

A scheduled RPI turn should prioritize:

```text
Research  → verify the active question and material evidence
Plan      → choose the strongest position or response to test
Work      → write the participant round
Review    → challenge repetition, unsupported claims, and weak trade-offs
```

Repeat only while the next loop can materially improve the same round. Stop when the round is decision-useful, no material finding remains, or the soft work budget is exhausted.

Do not expose private chain-of-thought. Preserve only conclusions, evidence, changed assumptions, and reviewable rationale in the round artifact.

### Round Output

Each participant writes only its own immutable round output. A useful scheduled round should record:

- current position;
- material new evidence or constraint;
- response to the other participant's strongest point when applicable;
- concessions or changed assumptions;
- current proposal;
- unresolved question only when it can change the decision;
- whether the participant recommends another round or synthesis.

Do not rewrite an output that the other participant may already have consumed. Correct mistakes in the next eligible round.

### Commit Boundary

Prefer **one participant turn = one reviewable commit**.

The commit should contain the completed round output and, only when owned by that turn, its synthesis or control update. Do not mix unrelated repository changes into a discussion turn.

If a stale revision or write conflict is detected, re-read the current artifacts before retrying. Never overwrite the other participant's round to resolve a conflict.

### Stop And Synthesis

The participant assigned as `synthesis_owner` writes the synthesis when any stop condition is reached and it has enough completed participant output to represent both sides fairly.

Synthesis may occur in the same run as the owner's final round when practical. The existence of the final synthesis is sufficient to mark the scheduled exchange as complete; participant schedules should perform no further discussion writes for that decision.

A synthesis is not a human decision. `Accepted` remains owned by the declared decision authority.

### Failure And Recovery

Scheduled discussion must fail closed rather than invent missing turns.

- Missing prerequisite round → no-op and retry on the next scheduled run.
- Duplicate invocation → no-op when the intended output already exists.
- Stale repository state → refresh before writing.
- Commit conflict → preserve both existing participant outputs and retry from current state.
- Missing evidence required to proceed → record the need for Research and recommend stopping.
- Reached round limit → synthesize the remaining agreement and disagreement instead of extending automatically.

These rules let scheduled runs recover without a dedicated Moderator process.

### Scheduled Task Prompt Contract

Each participant schedule should receive the same discussion contract except for its actor identity. A compact task instruction is sufficient:

```text
Act as participant <A|B> for the configured scheduled discussion.
Read inbox/_guidelines/discuss.md and the active discussion bundle first.
Run only when your next turn is eligible; otherwise make no discussion write.
Use the configured round_work and soft budgets to produce one complete turn.
Write only your participant output, self-review it, commit and push that turn,
and exit. Never wait for the other participant inside this run.
If you own synthesis and a stop condition is reached, write the synthesis.
Do not accept the human decision on the user's behalf.
```

Keep scheduler timing, actor identity, and active bundle path in the scheduled task configuration. Keep reusable discussion behavior in this guideline instead of duplicating it across task prompts.

## Shared Context

Before the first round, the Moderator establishes only the context needed for the decision:

- question or decision ID;
- scope and explicit non-goals;
- current evidence snapshot or canonical references;
- options or proposition when already known;
- discussion type, exchange pattern, cadence, and round limit;
- who has final decision authority.

A bundle may separate context, topics, configuration, rounds, synthesis, and decision log into files. Exact filenames are flexible, but their ownership must remain clear.

## Write Ownership

- The Moderator role owns shared context, round control, synthesis, and discussion status.
- A owns only A's round outputs; B owns only B's round outputs.
- When no separate Moderator execution exists, the configured protocol assigns Moderator writes at explicit boundaries; participants must not opportunistically rewrite shared state.
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

The Moderator role:

1. chooses the discussion type and exchange pattern from the decision's uncertainty and cost;
2. gives A and B the same shared context for independent first positions when independence matters;
3. keeps arguments scoped to the active decision;
4. checks after each round whether a material delta remains;
5. stops rather than extending a discussion for symmetry or volume;
6. synthesizes both participants fairly, including concessions and unresolved disagreement;
7. routes unanswered factual questions to Research when more evidence is required;
8. leaves the final decision to the declared decision authority.

These responsibilities describe required coordination behavior. They do not imply that a dedicated Moderator model invocation must exist.

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

The Moderator synthesis should make the decision cheaper for a human to review. Prefer:

- current recommendation or viable options;
- strongest evidence for each material position;
- points of agreement;
- remaining disagreement and the assumption causing it;
- new Research or validation needed, if any;
- the exact human decision still required.

## Boundaries

- Do not require a separate Moderator execution when protocol and shared state are sufficient.
- Do not use role assignment to force theatrical opposition.
- Do not let `discuss` become an unbounded brainstorming log.
- Do not treat scheduled repetition or elapsed time as deeper reasoning by itself.
- Do not create a new canonical requirement or project decision inside the discussion artifact.
- Follow the common artifact and lifecycle rules in `inbox/AGENTS.md`.
