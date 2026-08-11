# Discuss

Use `discuss` to exchange and refine positions before a human or owning workflow makes a decision.

Discussion is non-canonical. Route substantial evidence gathering to `research`, target evaluation to `review`, and accepted outcomes to their owning artifact.

## Bundle Contract

Every `discuss` artifact **must be a bundle**. Do not create a single-file discussion artifact.

Default runtime shape:

```text
<discuss-bundle>/
├── README.md
└── turns/
    └── <sequence>-<participant>.md
```

`README.md` is the entrypoint and owns goal, scope, configuration, topics, current state, references, and synthesis by default. `turns/` contains immutable participant turns.

Turn filenames contain only the discussion-global sequence and participant identity. Example: `001-a.md`, `002-b.md`, `003-a.md`. Zero-pad the sequence so lexical order matches discussion order. Topic and other metadata belong in the turn content, not the filename.

Split content into an additional file only when it materially improves readability. A large final synthesis may move to `synthesis.md`; link it from `README.md`. Do not create extension files preemptively.

Template: [`inbox/_templates/discuss/`](../_templates/discuss/). `turns/_turn.md` and `_synthesis.md` are authoring templates, not required runtime files.

## Core

Structured discussion has three logical roles:

- **Moderator**: frames the question, controls scope and turns, and synthesizes the result.
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

Manual `iterative` discussion defaults to at most **3 exchanges**. `one-shot` and `cross-review` use their own bounds. Scheduled discussion uses its session window and stop conditions instead.

## Turn Workflow

Every eligible A/B turn uses the same minimal RPI workflow:

```text
Research → Plan → Implement → Review → publish
```

1. **Research** — read `README.md`, the latest relevant turn, repository guidance, and decision-relevant evidence before forming a position. Refresh only what may change the current decision. If evidence gathering becomes substantial, record `Next: research` and stop argumentative work instead of expanding the discussion turn.
1. **Plan** — choose the smallest claim, challenge, correction, or transition this turn must resolve.
1. **Implement** — author only the participant-owned contribution. In this workflow, Implement means writing the discussion artifact, not modifying source code. A may also update A-owned shared state or synthesis when allowed.
1. **Review** — self-review correctness, evidence, strongest counterargument, repetition, and scope. If a material finding remains, repeat the full workflow from Research.
1. **Publish** — persist the completed turn, prefer one turn per commit, push, then exit.

Default refinement bounds:

```yaml
max_loops: 10
stop_condition: review_has_no_findings
```

- A loop counts only when Research, Plan, Implement, and Review all run.
- Later loops start from unresolved findings or new evidence; repeated wording does not count.
- Stop early when Review has no material findings.
- At loop 10, publish only if the result is still useful and record unresolved findings in `Next`; otherwise block instead of pretending completion.
- When an `rpi-loop` capability is available, use it for this refinement contract. Otherwise follow the same contract locally.

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

### A — Lead Workflow

A carries Moderator coordination in addition to the common Turn Workflow.

1. On the first turn, define the active topic and evidence baseline in `README.md`.
1. On later turns, read B's latest turn and test its strongest evidence or objection before revising A's position.
1. Keep topic state and transitions in `README.md`; do not open another topic while the current one can still be resolved.
1. If a stop condition is met, synthesize instead of creating another argumentative turn.

A owns `README.md`, A turns, topic transitions, and synthesis. A synthesis uses the same RPI refinement bounds but does not create another participant turn.

### B — Challenger Workflow

B applies the common Turn Workflow independently against A's latest published position.

1. Verify A's important evidence and assumptions rather than accepting its framing by default.
1. Search for the strongest counterexample, omitted alternative, trade-off, or reason to agree.
1. Write only B's turn; recommend shared-state or topic changes through `Next` instead of editing A-owned state.
1. If Review finds no material objection or alternative, write a **terminal turn** that records convergence or no remaining finding and sets `Next: synthesize` rather than silently no-oping.

B owns only B turns.

### Topics And Session

- Keep **one topic active at a time**.
- Keep topic definitions and status in `README.md`.
- Finish, block, or deliberately pause the active topic before switching.
- Keep subquestions inside the topic unless separation changes the decision.
- Add topics beyond two only when necessary to resolve the original goal.
- Do not add topics or turns merely because time remains.

The **6–12 hour window is a timebox, not a quota**. Stop early when resolved. After expiry, start no new argumentative turn; A may still synthesize persisted results. Provider-specific trigger intervals stay outside this guideline.

### One Invocation = One Turn

```text
read → check eligibility → run Turn Workflow → commit/push → exit
```

Each invocation handles at most one participant turn or A synthesis. Do not sleep, wait for another participant, or attempt delayed turns inside one invocation. Time budgets are soft ceilings for useful work.

Default order:

```text
A1 → B1 → A2 → B2 → ... → A synthesis
```

Derive eligibility from persisted turns, not a shared mutable `next_actor`:

- no turn → A;
- latest valid turn A → B;
- latest valid turn B → A;
- discussion/topic closed → no argumentative turn.

The filename sequence records the persisted discussion order. Participant-local numbering is not stored unless a future workflow demonstrates a concrete need for it.

Do not publish two equivalent argumentative turns against the same input state. A material delta is new or corrected evidence, a stronger or narrower argument, a changed assumption or concession, a decision-relevant risk, narrowed disagreement, or a justified recommendation change. A terminal turn that records convergence, a research block, or a justified request to synthesize is also a valid workflow delta.

Reusable discussion configuration and topic state live in `README.md`. Keep task IDs, recurrence syntax, model names, trigger intervals, and notifications outside the common bundle contract.

### Recovery

- Never rewrite a turn already consumed by the other participant; correct it in the next eligible turn.
- Missing prerequisite or duplicate invocation → no-op.
- Stale state or write conflict → refresh, preserve existing outputs, retry from current state.
- Missed turn → resume from the latest valid turn.
- Missing material evidence → participant sets `Next: research`; A marks shared topic state blocked when needed.
- Session expiry → stop new turns and hand synthesis to A.

The protocol requires only that a platform can invoke A/B, expose durable shared state and prior turns, persist a turn, and invoke the other actor later. Scheduler-specific implementation may vary.

## Stop And Synthesis

Stop a discussion or active topic when:

- A and B converge on the same material proposal;
- the remaining difference is human priority, risk tolerance, or preference;
- new evidence is required before reasoning can advance;
- the latest eligible turn adds no material information beyond a terminal signal;
- an explicit safety bound or session window is reached;
- the decision authority closes the topic.

By default, A writes the synthesis in `README.md`. Split it to `synthesis.md` only when the result is large enough that separation improves readability.

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

- Do not create single-file `discuss` artifacts.
- Do not create `topics.md`, `synthesis.md`, or other extension files unless separation materially improves readability.
- Do not require a separate Moderator execution when protocol is sufficient.
- Do not bind the protocol to one provider, scheduler, task API, trigger interval, or model.
- Do not force opposition or equal turn counts.
- Do not let `discuss` become an unbounded brainstorming log.
- Do not treat repetition or elapsed time as deeper reasoning by itself.
- Do not create canonical requirements or decisions inside the discussion artifact.
- Follow `inbox/AGENTS.md`.
