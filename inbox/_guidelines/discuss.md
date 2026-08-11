# Discuss

Use `discuss` to exchange and refine positions before a human or owning workflow makes a decision.

Discussion is non-canonical. Route substantial evidence gathering to `research`, target evaluation to `review`, and accepted outcomes to their owning artifact.

## Roles

Structured discussion has three logical roles.

- **Moderator**: frames the question, controls scope and rounds, and synthesizes the result.
- **A** and **B**: independent participants that argue from evidence and may change position when warranted.

`A` and `B` are participant identities, not fixed sides. Do not force artificial opposition.

The Moderator is a coordination role, not necessarily a separate agent or chat. In scheduled discussion, **A carries the Moderator role by default**.

## Types

Choose the smallest type that matches the purpose.

| Type | Use when | Result |
| --- | --- | --- |
| `explore` | options or framing are unclear | candidate directions and unknowns |
| `compare` | known alternatives need comparison | trade-offs and preferred options |
| `debate` | a contested proposition needs challenge | strongest arguments and changed positions |
| `challenge` | a leading proposal needs stress-testing | weak assumptions and acceptance conditions |
| `converge` | prior discussion needs narrowing | agreements, residual disagreements, decision points |

Types may transition when the change is explicit. Do not use `explore` when the real need is Research.

## Exchange And Cadence

Exchange patterns:

- **One-shot**: A and B respond once, then synthesize.
- **Cross-review**: A and B each review the other's strongest case once. Default for consequential decisions.
- **Iterative**: A and B continue while another turn can materially change the result.

Cadence:

- **Manual**: a human or Moderator advances turns.
- **Scheduled**: two chat agents revisit the discussion asynchronously during a configured session window.

Ordinary discussion defaults to **3 rounds per decision**. Scheduled discussion uses its session window and stop conditions instead.

## Scheduled Discussion

Scheduled discussion is a long-running asynchronous session between **A and B**. It is designed around ChatGPT-style scheduled chats but must remain portable to other chat applications and agent runners.

### Defaults

| Field | Default |
| --- | --- |
| Lead | A |
| Topics | 1 primary, optional 1 secondary |
| Active topics | 1 at a time |
| Session window | 6–12 hours |
| Exchange | iterative |
| Synthesis owner | A |
| Decision authority | human or owning workflow |

More topics or a longer session are allowed only when the discussion goal requires them.

### A — Lead

A owns discussion coordination, not the final human decision.

A:

- opens each topic and controls topic order;
- revises its position after reading B;
- owns shared session state and topic transitions;
- decides whether to continue, request Research, change topic, or stop from this protocol;
- writes the final synthesis;
- represents B's strongest evidence fairly.

### B — Challenger

B independently tests A's direction.

B:

- responds to A's latest published position;
- checks evidence, assumptions, trade-offs, and omitted alternatives;
- strengthens, challenges, or agrees with A based on evidence;
- recommends state or topic changes when needed;
- writes only B's own turns.

Agreement is valid when A's position survives scrutiny.

### Topics And Timebox

- Keep only **one topic active at a time**.
- Finish, block, or deliberately pause it before switching.
- Keep subquestions inside the active topic unless separation changes the decision.
- Add topics beyond two only when necessary to resolve the original goal.
- Do not add topics or turns merely because time remains.

The **6–12 hour session window is a timebox, not a quota**. Stop early when the discussion is resolved. After expiry, do not start another argumentative turn; A may still synthesize persisted results.

The common protocol does not prescribe a provider-specific trigger interval.

### One Invocation = One Turn

Each scheduled invocation performs one complete participant turn:

```text
read → check eligibility → reason/research → write → self-review → commit/push → exit
```

A turn:

1. reads this guideline, active configuration, active topic, and latest relevant turn;
2. exits when this actor is not eligible;
3. refreshes only evidence that can materially change the topic;
4. performs the configured reasoning or bounded RPI refinement;
5. writes one contribution with a material delta;
6. self-reviews unsupported claims, repetition, and scope drift;
7. commits and pushes the completed turn;
8. exits without waiting for the other participant.

Do not keep a run alive to fill time, sleep until the other participant acts, or attempt delayed turns inside one invocation. Time budgets are soft ceilings for useful work.

### Turn Order

Default order:

```text
A1 → B1 → A2 → B2 → ... → A synthesis
```

Derive eligibility from persisted turns instead of a shared mutable `next_actor` field:

- no turn exists → A;
- latest valid turn is A → B;
- latest valid turn is B → A;
- synthesis exists or the topic/session is closed → no further argumentative turn.

An actor must not publish two equivalent turns against the same input state.

A useful turn adds at least one of:

- new or corrected evidence;
- a stronger or narrower argument;
- a changed assumption or concession;
- a decision-relevant risk;
- a material narrowing of disagreement;
- a justified recommendation change.

No material delta → no new argumentative turn.

### Configuration

Keep provider-specific scheduling outside the reusable discussion contract.

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

`round_work: rpi-loop` improves the current turn only. It does not expand discussion scope or authorize unrelated implementation.

Do not store task IDs, recurrence syntax, model names, or notification settings in this common contract.

### Ownership And Recovery

- **A** owns shared session state, topic transitions, A turns, and synthesis.
- **B** owns only B turns and recommends shared-state changes in its contribution.
- Do not rewrite a turn already consumed by the other participant; correct it in the next eligible turn.
- Prefer **one participant turn = one commit** and keep unrelated repository changes out.

Recover from persisted state:

- missing prerequisite or duplicate invocation → no-op;
- stale repository state → refresh before writing;
- write conflict → preserve existing outputs and retry from current state;
- missed turn → resume from the latest valid turn;
- missing material evidence → request Research and block or close the topic;
- session expiry → stop new rounds and hand synthesis to A.

### Portability

The protocol requires only that a platform can eventually:

1. invoke A or B;
2. let the actor read durable shared state and prior turns;
3. persist the completed turn;
4. invoke the other actor later.

ChatGPT scheduled tasks, another chat scheduler, or an external orchestrator may implement these capabilities differently without changing the discussion rules.

## Stop And Synthesis

Stop a discussion or active topic when any of the following is true:

- A and B converge on the same material proposal;
- the remaining difference is human priority, risk tolerance, or preference;
- new evidence is required before reasoning can advance;
- the latest eligible turn adds no material information;
- an explicit safety bound is reached;
- the scheduled session window expires;
- the decision authority closes the topic.

A synthesis should record only what makes the human decision cheaper:

- result for each topic;
- strongest evidence and counterevidence;
- changed positions or concessions;
- agreements and remaining disagreements;
- unresolved Research or validation;
- recommended next action;
- the exact human decision still required, if any.

Synthesis is a discussion result, not a canonical project decision.

## Boundaries

- Do not require a separate Moderator execution when protocol is sufficient.
- Do not bind the common protocol to one provider, scheduler, trigger interval, task API, or model.
- Do not force theatrical opposition or equal turn counts.
- Do not let `discuss` become an unbounded brainstorming log.
- Do not treat scheduled repetition or elapsed time as deeper reasoning by itself.
- Do not create canonical requirements or decisions inside the discussion artifact.
- Follow the common artifact and lifecycle rules in `inbox/AGENTS.md`.
