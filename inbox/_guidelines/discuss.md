# Discuss

Use `discuss` when the primary purpose is to exchange and refine positions before a human or owning workflow makes a decision.

Discussion is non-canonical. Route substantial evidence gathering to `research`, target evaluation to `review`, and accepted outcomes to their owning artifact.

## Roles

Every structured discussion has three logical roles.

- **Moderator**: frames the question, controls scope and rounds, and synthesizes the result.
- **A** and **B**: independent participants that argue from evidence and project constraints and may change position when warranted.

`A` and `B` are participant identities, not fixed sides. Do not force artificial opposition.

The Moderator is a coordination role, not necessarily a separate agent, chat, or scheduled task. In scheduled discussion, **A carries this role by default**.

## Discussion Types

Choose the smallest type that matches the purpose.

| Type | Use when | Expected result |
| --- | --- | --- |
| `explore` | options or framing are unclear | candidate directions and material unknowns |
| `compare` | known alternatives need comparison | trade-offs and preferred options |
| `debate` | a contested proposition needs challenge | strongest arguments and changed positions |
| `challenge` | a leading proposal needs stress-testing | weak assumptions and acceptance conditions |
| `converge` | prior discussion needs narrowing | agreements, residual disagreements, decision points |

Types may transition when the change is explicit. Do not use `explore` to hide a question that actually needs Research.

## Exchange Patterns

- **One-shot**: A and B respond once, then synthesize.
- **Cross-review**: A and B produce positions and each reviews the other's strongest case once. Default for consequential decisions.
- **Iterative**: A and B continue while another turn can materially change the result.

Ordinary discussion defaults to **3 rounds per decision**. Extended scheduled discussion uses its configured session window and stop conditions instead.

## Cadence

- **Manual**: the human or Moderator advances turns.
- **Scheduled**: two chat agents revisit the discussion asynchronously during a configured session window.

Overnight discussion is one scheduled use case, not the definition of `discuss`.

## Scheduled Discussion

Scheduled discussion is a **long-running asynchronous session between two chat agents**. The rules are designed around ChatGPT-style scheduled chats but must remain usable by other chat applications, schedulers, and agent runners.

### Defaults

| Field | Default |
| --- | --- |
| Participants | A, B |
| Lead | A |
| Topics | 1 primary, optionally 1 secondary |
| Active topics | 1 at a time |
| Session window | 6–12 hours |
| Exchange | A-led iterative |
| Synthesis owner | A |
| Decision authority | Human or declared owning workflow |

More topics or a longer window are allowed when the discussion goal requires them. They are not defaults.

A separate Moderator schedule is not required.

### A — Lead

A owns session direction without owning the final human decision.

A:

- establishes the initial framing and topic order;
- opens each topic with the first substantive position;
- reads B's latest contribution before revising its position;
- owns shared session state and topic transitions;
- decides from the protocol whether to continue, pause, request Research, change topic, or stop;
- writes the final synthesis;
- represents B's strongest evidence fairly and does not overrule it by role authority.

### B — Challenger

B independently tests A's direction.

B:

- responds to A's latest published position;
- verifies evidence, assumptions, trade-offs, and omitted alternatives;
- strengthens, challenges, or agrees with A based on evidence;
- records concessions and changed positions;
- may recommend another topic when needed for the original discussion goal;
- does not rewrite shared session control or silently redefine the active topic.

Agreement is valid when A's position survives scrutiny.

### Topics

A session normally starts with **1 topic** and may contain **1 additional topic** when it materially serves the same goal.

- Keep only one topic active at a time.
- Finish, block, or deliberately pause the active topic before switching.
- Keep subquestions inside the current topic unless separation changes the decision.
- Add topics beyond two only when a newly discovered issue is necessary to resolve the original goal; A records why it was added.
- Do not add topics merely because time remains.

### Session Window

A session normally runs for **6 to 12 hours**.

- The window is a timebox, not a quota.
- Stop early when all active topics satisfy a Stop Condition.
- Extend only when the human requested a longer session or new material evidence justifies an explicit extension.
- Do not create filler turns to consume unused time.
- After expiry, do not start another argumentative turn. A may still synthesize persisted results.

The common protocol does not prescribe a provider-specific trigger interval. Each platform maps the session window to schedules it supports.

### Turn Model

Treat **one scheduled invocation as one complete participant turn**:

```text
read → check eligibility → reason/research → write → self-review → commit/push → exit
```

Each turn:

1. reads this guideline, active configuration, current topic, and latest relevant turn;
2. verifies that this actor is eligible;
3. refreshes only evidence that can materially change the topic;
4. performs the configured reasoning, Research, or bounded RPI-style refinement;
5. writes one reviewable contribution containing material changes only;
6. self-reviews unsupported claims, repetition, and scope drift;
7. commits and pushes the completed turn as one reviewable unit;
8. exits without waiting for the other participant.

Do not keep a run alive to fill a duration, sleep until the other participant acts, or attempt delayed turns inside one invocation. Scheduling provides the wait; each invocation provides completed work.

A turn or RPI time value is a **soft work budget**, not guaranteed runtime and not a reason to delay completion.

### Exchange And Eligibility

Default exchange:

```text
A1 → B1 → A2 → B2 → ... → A synthesis
```

Derive the next actor from persisted immutable turns rather than both agents updating a shared `next_actor` field.

- no turn exists → A is eligible;
- latest valid turn is A → B is eligible;
- latest valid turn is B → A is eligible;
- synthesis exists or topic/session is closed → neither is eligible for another argumentative turn.

An actor must not publish two equivalent turns against the same input state.

If this actor is not eligible, the intended turn already exists, or the session expired, make no new argumentative write and exit cleanly.

### Material Delta

A scheduled turn should add at least one material delta:

- new or corrected evidence;
- a stronger or narrower argument;
- a changed assumption or concession;
- a decision-relevant risk;
- a material narrowing of disagreement;
- a justified recommendation change.

If no material delta exists, do not create another argumentative turn merely because a schedule fired.

### Configuration

Keep provider-specific scheduling outside reusable discussion behavior.

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

`round_work: rpi-loop` applies only to improving the current turn. It does not expand scope or authorize unrelated implementation.

Keep task IDs, recurrence syntax, model names, notification settings, and delivery metadata outside this common contract.

### Write Ownership

Scheduled discussion intentionally uses asymmetric ownership.

- **A** owns shared session state, topic transitions, A turns, and final synthesis.
- **B** owns only B turns.
- B recommends state changes in its contribution; A applies them at its next eligible boundary.
- Neither participant rewrites a contribution already consumed by the other; corrections go into the next eligible turn.

Prefer **one participant turn = one commit**. Do not mix unrelated repository work into a discussion turn.

### Failure And Recovery

Recover from persisted state rather than assumed wall-clock order.

- Missing prerequisite turn → no-op and retry later.
- Duplicate invocation → no-op if the intended turn already exists.
- Stale repository state → refresh before writing.
- Write conflict → preserve existing outputs and retry from current state.
- Missed turns → resume from the latest valid persisted turn.
- Missing evidence → request Research and block or close the topic.
- Session expiry → stop new rounds and hand synthesis to A.

### Portability

The protocol assumes only that a platform can eventually:

1. invoke A or B;
2. let the actor read durable shared state and prior published turns;
3. persist the completed output;
4. invoke the other actor later.

ChatGPT scheduled tasks, another chat application's scheduler, or an external orchestrator may implement those capabilities differently without changing the discussion rules.

### End Of Session

A writes the final synthesis when all topics close, a Stop Condition is reached, or the session window expires.

The synthesis records:

- result for each topic;
- strongest evidence and counterevidence;
- where A or B changed position;
- agreements and remaining disagreements;
- unresolved uncertainty or required Research;
- recommended next action;
- the exact human decision still required, if any.

Synthesis is a discussion result, not a canonical project decision.

## Participant Contract

A useful contribution contains only what changes the decision:

- current position;
- material evidence or project constraint;
- response to the strongest opposing point when one exists;
- concessions or changed assumptions;
- current proposal;
- unresolved question only when it can change the choice;
- continue, change topic, Research, or stop recommendation when iterative.

Distinguish repository facts from inference and preference. Do not repeat an earlier position with different wording.

## Stop Conditions

Stop a discussion or active topic when any of the following is true:

- A and B converge on the same material proposal;
- the remaining difference is human priority, risk tolerance, or preference;
- new evidence is required before reasoning can advance;
- the latest eligible turn adds no material information;
- an explicit safety bound is reached;
- the scheduled session window expires;
- the decision authority closes the topic.

The result may be agreement, disagreement, or a Research request.

## Boundaries

- Do not require a separate Moderator execution when protocol is sufficient.
- Do not bind the common protocol to one chat provider, scheduler, trigger interval, task API, or model.
- Do not force theatrical opposition.
- Do not let `discuss` become an unbounded brainstorming log.
- Do not treat scheduled repetition, elapsed time, or equal turn counts as deeper reasoning by itself.
- Do not create canonical requirements or decisions inside the discussion artifact.
- Follow the common artifact and lifecycle rules in `inbox/AGENTS.md`.
