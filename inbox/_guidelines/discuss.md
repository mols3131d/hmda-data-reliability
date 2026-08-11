# Discuss

Use `discuss` to exchange and refine positions before a human or owning workflow makes a decision.

Discussion is non-canonical. Route substantial evidence gathering to `research`, target evaluation to `review`, and accepted outcomes to their owning artifact.

## Core

Structured discussion has three logical roles:

- **Moderator**: frames the question, controls scope and rounds, and synthesizes the result.
- **A**, **B**: independent participants that argue from evidence and may change position when warranted.

`A` and `B` are identities, not fixed sides. The Moderator is a coordination role, not necessarily a separate agent or chat. In scheduled discussion, **A carries it by default**.

Choose the smallest discussion type that matches the purpose.

| Type | Use when | Result |
| --- | --- | --- |
| `explore` | options or framing are unclear | directions and unknowns |
| `compare` | known alternatives need comparison | trade-offs and preferred options |
| `debate` | a proposition needs challenge | strongest arguments and changed positions |
| `challenge` | a leading proposal needs stress-testing | weak assumptions and acceptance conditions |
| `converge` | prior discussion needs narrowing | agreements, disagreements, decision points |

Types may transition when explicit. Do not use `explore` when the real need is Research.

Exchange patterns:

- **One-shot**: A and B respond once, then synthesize.
- **Cross-review**: each reviews the other's strongest case once. Default for consequential decisions.
- **Iterative**: continue while another turn can materially change the result.

Cadence:

- **Manual**: a human or Moderator advances turns.
- **Scheduled**: two chat agents revisit the discussion asynchronously during a session window.

Ordinary discussion defaults to **3 rounds per decision**. Scheduled discussion uses its session window and stop conditions instead.

## Scheduled Discussion

Scheduled discussion is a long-running asynchronous session between **A and B**. It is designed around ChatGPT-style scheduled chats but must remain portable to other chat applications and agent runners.

### Defaults

| Field | Default |
| --- | --- |
| Lead | A |
| Topics | 1 primary, optional 1 secondary |
| Active topics | 1 |
| Session | 6–12 hours |
| Exchange | iterative |
| Synthesis | A |
| Decision authority | human or owning workflow |

More topics or a longer session require a reason tied to the discussion goal.

### Roles

**A — Lead**

- opens topics and controls topic order;
- revises after reading B;
- owns shared state and topic transitions;
- chooses continue, Research, topic change, or stop from this protocol;
- writes the final synthesis and represents B's strongest evidence fairly.

**B — Challenger**

- responds to A's latest published position;
- checks evidence, assumptions, trade-offs, and omitted alternatives;
- strengthens, challenges, or agrees based on evidence;
- recommends state or topic changes without rewriting shared control;
- writes only B's turns.

Agreement is valid when A's position survives scrutiny.

### Topics And Session

- Keep **one topic active at a time**.
- Finish, block, or deliberately pause it before switching.
- Keep subquestions inside the topic unless separation changes the decision.
- Add topics beyond two only when necessary to resolve the original goal.
- Do not add topics or turns merely because time remains.

The **6–12 hour window is a timebox, not a quota**. Stop early when resolved. After expiry, start no new argumentative turn; A may still synthesize persisted results.

Provider-specific trigger intervals stay outside this guideline.

### One Invocation = One Turn

```text
read → check eligibility → reason/research → write → self-review → commit/push → exit
```

Each invocation:

1. reads this guideline, configuration, active topic, and latest relevant turn;
2. exits when this actor is not eligible;
3. refreshes only decision-relevant evidence;
4. performs the configured reasoning or bounded RPI refinement;
5. writes one contribution with a material delta;
6. self-reviews unsupported claims, repetition, and scope drift;
7. commits and pushes the completed turn;
8. exits without waiting for the other participant.

Do not sleep, wait for another participant, or attempt delayed turns inside one invocation. Time budgets are soft ceilings for useful work.

Default order:

```text
A1 → B1 → A2 → B2 → ... → A synthesis
```

Derive eligibility from persisted turns, not a shared mutable `next_actor`:

- no turn → A;
- latest valid turn A → B;
- latest valid turn B → A;
- synthesis exists or topic/session closed → no argumentative turn.

Do not publish two equivalent turns against the same input state.

A material delta is at least one of: new or corrected evidence, stronger or narrower argument, changed assumption or concession, decision-relevant risk, narrowed disagreement, or justified recommendation change.

No material delta → no new argumentative turn.

### Configuration

```yaml
discussion:
  id: <discussion-id>
  status: active
  type: debate
  exchange: iterative
  cadence: scheduled
  lead: A
  decision_authority: human
  started_at: <timestamp>
  ends_at: <timestamp>
  active_topic: <topic-id>
  topics:
    - id: <topic-id>
      status: active
  round_work: rpi-loop
```

Optional safety fields such as `max_rounds`, `rpi_budget_minutes`, or `turn_budget_minutes` may be added when useful.

`round_work: rpi-loop` improves the current turn only. It does not expand scope or authorize unrelated implementation.

Keep task IDs, recurrence syntax, model names, trigger intervals, and notifications outside this contract.

### Ownership And Recovery

- **A** owns shared state, topic transitions, A turns, and synthesis.
- **B** owns only B turns and recommends shared-state changes in its turn.
- Never rewrite a turn already consumed by the other participant; correct it in the next eligible turn.
- Prefer **one turn = one commit** and keep unrelated repository work out.
- Missing prerequisite or duplicate invocation → no-op.
- Stale state or write conflict → refresh, preserve existing outputs, retry from current state.
- Missed turn → resume from the latest valid turn.
- Missing material evidence → request Research and block or close the topic.
- Session expiry → stop new rounds and hand synthesis to A.

The protocol requires only that a platform can invoke A/B, expose durable shared state and prior turns, persist a turn, and invoke the other actor later. Scheduler-specific implementation may vary.

## Stop And Synthesis

Stop a discussion or active topic when:

- A and B converge on the same material proposal;
- the remaining difference is human priority, risk tolerance, or preference;
- new evidence is required before reasoning can advance;
- the latest eligible turn adds no material information;
- an explicit safety bound or session window is reached;
- the decision authority closes the topic.

Synthesis records only what makes the human decision cheaper:

- result for each topic;
- strongest evidence and counterevidence;
- changed positions or concessions;
- agreements and remaining disagreements;
- unresolved Research or validation;
- recommended next action;
- exact human decision still required, if any.

Synthesis is a discussion result, not a canonical project decision.

## Boundaries

- Do not require a separate Moderator execution when protocol is sufficient.
- Do not bind the protocol to one provider, scheduler, task API, trigger interval, or model.
- Do not force opposition or equal turn counts.
- Do not let `discuss` become an unbounded brainstorming log.
- Do not treat repetition or elapsed time as deeper reasoning by itself.
- Do not create canonical requirements or decisions inside the discussion artifact.
- Follow `inbox/AGENTS.md`.
