# Discuss

Use `discuss` when the primary purpose is to exchange and refine positions before a human or owning workflow makes a decision.

Discussion is not Research, Review, or a canonical decision. Route substantial evidence gathering to `research`, target evaluation and findings to `review`, and accepted normative outcomes to their owning artifact.

## Roles

Every structured discussion has three logical roles.

- **Moderator**: frames the question, controls scope and rounds, and synthesizes the result.
- **A** and **B**: independent participants that argue from evidence and project constraints and may change position when warranted.

`A` and `B` identify participants, not fixed sides. Do not force artificial opposition.

The Moderator is a **coordination role, not necessarily a separate agent, chat, or scheduled task**. Its responsibilities may be carried by the human, one participant at an explicit boundary, or deterministic protocol.

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

- **One-shot**: A and B respond once, then synthesize.
- **Cross-review**: A and B produce positions and each reviews the other's strongest case once. Default for consequential decisions.
- **Iterative**: A and B continue while another turn can materially change the result.

Ordinary discussion defaults to **3 rounds per decision**. Extended scheduled discussion uses its configured session window and stop conditions instead of inheriting that limit blindly.

## Cadence

Cadence controls when participant turns run.

- **Manual**: the human or Moderator advances turns.
- **Scheduled**: two chat agents revisit the discussion asynchronously during a configured session window.

Overnight discussion is one scheduled use case, not the definition of `discuss`.

## Scheduled Discussion

Scheduled discussion is a **long-running asynchronous session between two chat agents**. The rules are designed around ChatGPT-style scheduled chats but must remain portable to other chat applications, agent runners, and schedulers.

Default session shape:

- participants: **A and B**;
- **A is the Lead** and carries the Moderator coordination role;
- topics: normally **1 primary topic**, optionally **1 secondary topic**;
- window: normally **6 to 12 hours**;
- exchange: A-led iterative review;
- final decision authority: human or the declared owning workflow.

More topics or a longer window are allowed when the discussion goal requires them. They are not defaults.

A scheduled discussion does **not** require a third scheduled Moderator.

### A — Lead

A owns session direction without owning the final human decision.

A:

- establishes the initial framing and topic order;
- opens each topic with the first substantive position;
- reads B's latest contribution before revising, defending, or narrowing its position;
- owns shared session state and topic transitions;
- decides from the protocol whether to continue, pause, request Research, change topic, or stop;
- writes the final synthesis;
- represents B's strongest evidence fairly and does not use Lead status to overrule it.

### B — Challenger

B is the independent counterweight to A's lead.

B:

- responds to A's latest published position for the active topic;
- verifies A's evidence, assumptions, trade-offs, and omitted alternatives;
- strengthens, challenges, or agrees with A based on evidence;
- records concessions and changed positions explicitly;
- may recommend another topic when it is necessary to answer the original discussion goal;
- does not rewrite shared session control or silently redefine the active topic.

B is not required to oppose A. Agreement is valid when A's position survives scrutiny.

### Topics

A session normally starts with **1 topic** and may contain **1 additional topic** when it materially serves the same discussion goal.

- Keep only one topic active at a time.
- Finish, block, or deliberately pause the active topic before switching.
- Keep subquestions inside the current topic unless separating them changes the decision.
- Add topics beyond two only when a newly discovered issue is necessary to resolve the original goal; A records why it was added.
- Do not add topics merely because session time remains.

Topic count is a default constraint, not a hard schema limit.

### Session Window

A session normally runs for **6 to 12 hours**.

- The window is a timebox, not a quota that must be consumed.
- Stop early when all active topics satisfy a Stop Condition.
- Extend beyond the configured window only when the human requested a longer session or new material evidence justifies an explicit extension.
- Do not create filler turns to occupy unused time.
- After expiry, do not start another argumentative turn. A may still synthesize the persisted discussion.

The common protocol does not prescribe a provider-specific trigger interval. Each platform maps the session window to schedules it actually supports.

### Turn Model

Treat **one scheduled invocation as one complete participant turn**:

```text
read → check eligibility → reason/research → write → self-review → commit/push → exit
```

A turn should:

1. read this guideline, the active discussion configuration, the current topic, and the latest relevant turn;
2. verify that this actor is eligible to act;
3. refresh only evidence that can materially change the active topic;
4. perform the configured reasoning, Research, or bounded RPI-style refinement needed for this turn;
5. write one reviewable contribution containing material changes only;
6. self-review unsupported claims, repetition, scope drift, and whether a material delta exists;
7. commit and push the completed turn as one reviewable unit;
8. exit without waiting for the other participant.

Do not keep a run alive to fill a target duration, sleep until the other participant acts, or attempt delayed turns inside one invocation. The scheduler provides the waiting interval; each invocation provides completed work.

A configured turn or RPI time value is a **soft work budget**, not guaranteed runtime and not a reason to delay completion.

### Exchange

Default scheduled exchange:

```text
A1 → B1 → A2 → B2 → ... → A synthesis
```

A and B do not need equal numbers of contributions. If the latest evidence resolves the topic, advance or close it without a ceremonial rebuttal.

A turn should add at least one material delta:

- new or corrected evidence;
- a stronger or narrower argument;
- a changed assumption or concession;
- a newly identified decision-relevant risk;
- a material narrowing of disagreement;
- a justified recommendation change.

If no material delta exists, do not create another argumentative turn merely because a schedule fired.

### Configuration

Keep reusable discussion behavior independent from provider-specific scheduling syntax.

A portable configuration may look like:

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

Optional safety fields such as `max_rounds`, `rpi_budget_minutes`, or `turn_budget_minutes` may be added when useful. The session window plus material-delta rules are the primary bounds for an extended scheduled session.

`round_work: rpi-loop` means the participant uses the project's RPI loop to improve **its current turn only**. It does not expand scope or authorize unrelated implementation.

Keep provider-specific task IDs, recurrence syntax, model names, notification settings, and delivery metadata outside the common discussion contract.

### Turn Eligibility

Derive the next actor from **persisted immutable turns**, not from both agents racing to update a shared `next_actor` field.

For one active topic:

- no participant turn exists → A is eligible;
- latest valid turn is A → B is eligible;
- latest valid turn is B → A is eligible;
- synthesis exists or topic/session is closed → neither is eligible for a new argumentative turn.

An actor must not publish two equivalent turns against the same input state.

If the expected input is missing, this actor is not eligible, the intended turn already exists, or the session window expired, perform no new argumentative write and exit cleanly.

### Write Ownership

Scheduled discussion intentionally uses asymmetric ownership.

- **A** owns shared session state, topic transitions, A turns, and final synthesis.
- **B** owns only B turns.
- Neither participant rewrites a contribution already consumed by the other; corrections go into the next eligible turn.
- B recommends state changes in its contribution; A applies shared-state changes at its next eligible boundary.

This keeps both chat agents from racing to modify the same control file.

### Commit Boundary

Prefer **one participant turn = one reviewable commit**.

The commit contains the completed turn and, for A only when needed, its small session-state transition or final synthesis. Do not mix unrelated repository work into a discussion turn.

If a stale revision or write conflict is detected, re-read the current artifacts before retrying. Never overwrite the other participant's contribution to resolve a conflict.

### Failure And Recovery

Scheduled execution may be late, skipped, duplicated, or unavailable. Recover from persisted state rather than assumed wall-clock order.

- Missing prerequisite turn → no-op; retry on a later invocation.
- Duplicate invocation → no-op if the intended turn already exists.
- Stale repository state → refresh before writing.
- Write conflict → preserve existing outputs and retry from current state.
- Missed turns → resume from the latest valid persisted turn.
- Missing evidence required to proceed → request Research and block or close the topic.
- Session expiry → stop new rounds and hand final synthesis to A.

### Portability

The common protocol assumes only that a platform can eventually:

1. invoke A or B;
2. let that actor read durable shared state and prior published turns;
3. persist the actor's completed output;
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

The synthesis is a discussion result, not a canonical project decision.

## Shared Context

Before the first turn, establish only what the discussion needs:

- question or decision ID;
- scope and explicit non-goals;
- current evidence snapshot or canonical references;
- initial topic list or proposition when known;
- discussion type, exchange pattern, cadence, and applicable bounds;
- final decision authority.

A bundle may separate context, topics, configuration, turns, synthesis, and decision log. Exact filenames are flexible, but ownership must remain clear.

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

## Moderator Contract

The Moderator role:

1. chooses type and exchange pattern from uncertainty and decision cost;
2. keeps discussion scoped to the active decision;
3. stops when another turn has no material value;
4. synthesizes both sides fairly, including concessions and unresolved disagreement;
5. routes unanswered factual questions to Research when needed;
6. leaves the final decision to the declared decision authority.

These are coordination responsibilities, not a requirement for a dedicated Moderator invocation. In scheduled discussion, A carries them by default.

## Stop Conditions

Stop a discussion or active topic when any of the following is true:

- A and B converge on the same material proposal;
- the remaining difference is human priority, risk tolerance, or preference;
- new evidence is required before reasoning can advance;
- the latest eligible turn adds no material information;
- an explicitly configured safety bound is reached;
- the scheduled session window expires;
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
- Do not bind the common protocol to one chat provider, scheduler, trigger interval, task API, or model.
- Do not force theatrical opposition.
- Do not let `discuss` become an unbounded brainstorming log.
- Do not treat scheduled repetition, elapsed time, or equal turn counts as deeper reasoning by itself.
- Do not create canonical requirements or decisions inside the discussion artifact.
- Follow the common artifact and lifecycle rules in `inbox/AGENTS.md`.
