# OpenAI ChatGPT Scheduled Discussion

This document extends [`discuss.md`](discuss.md) for scheduled discussions run by two OpenAI ChatGPT chats.

The common `discuss` protocol remains authoritative for bundle structure, participant ownership, topic handling, turn workflow, eligibility, recovery, stop conditions, and synthesis. This extension owns only ChatGPT-specific scheduling and bootstrap behavior.

## Preconditions

Use this extension only when scheduled runs can access and update the shared GitHub discussion state required by `discuss.md`.

- Two active Scheduled Task slots are required: one for A and one for B.
- The scheduled run must be able to use the required GitHub connection or tool with sufficient repository permissions.
- Do not depend on files attached only to a ChatGPT Project; Scheduled Tasks may not have access to those project files. Keep durable discussion state in the repository.
- If a scheduled run cannot read or persist the required repository state, treat the discussion as blocked instead of reconstructing state from chat memory.

OpenAI currently does not allow a Scheduled Task to run more than once per hour. The default schedule below respects that limit. See [Scheduled Tasks in ChatGPT](https://help.openai.com/en/articles/10291617-tasks-in-chatgpt).

## Schedule Configuration

Use the same values in both participant prompts.

| Field | Default | Rule |
| --- | --- | --- |
| `started_at` | required | absolute timestamp with timezone |
| `ends_at` | required | later than `started_at` |
| `participant_interval` | 60 minutes | scheduler-supported and not faster than the platform limit |
| `b_offset` | 30 minutes | greater than 0 and less than `participant_interval` |

`ends_at - started_at` must be an exact multiple of `participant_interval` so the session ends on an A recurrence boundary.

The defaults produce the original hourly A/B schedule, but the protocol does not require exactly 60/30-minute timing.

## Runtime Model

Use two independent ChatGPT chats: one for **A**, one for **B**.

Persist the shared schedule configuration in the discussion `README.md` and treat the persisted values as the source of truth.

Let:

- `I = participant_interval`
- `O = b_offset`

```text
T+0        A1
T+O        B1
T+I        A2
T+(I+O)    B2
...
T+ends_at  A finalization
```

A runs at `started_at + kI`. B runs at `started_at + O + kI` while that time is strictly before `ends_at`.

When `O = I / 2`, participant invocations are evenly interleaved. Otherwise the gaps alternate between `O` and `I - O`; ordering remains A → B → A → B.

The schedule determines when a participant is invoked. Persisted discussion state still determines whether that participant is eligible to publish a turn.

## Bootstrap

### A

When the A prompt is first submitted:

1. read the repository and discussion guidance;
2. validate the shared schedule configuration;
3. create or initialize the discussion bundle when needed;
4. persist the shared schedule configuration;
5. define only the topics needed by the goal, following the common topic defaults and one-active-topic rule;
6. publish the first eligible A turn immediately;
7. arrange later A invocations every `participant_interval` through `ends_at`.

A is the Lead and carries Moderator coordination as defined by `discuss.md`.

### B

When the B prompt is first submitted:

1. read the repository and discussion guidance;
2. validate the same schedule configuration;
3. do not create the discussion bundle or A-owned shared state;
4. do **not** publish a B turn immediately;
5. arrange the first B invocation for `started_at + b_offset` and later B invocations every `participant_interval` while the scheduled time is strictly before `ends_at`.

If the bundle does not yet exist during B bootstrap, schedule from the shared absolute session anchors and exit. The first scheduled B invocation must re-read the repository; if A still has not initialized the bundle or published A1, follow the common recovery rules.

Bootstrap configuration is not itself a participant turn.

## Invocation Contract

Every scheduled invocation follows the common rule:

```text
refresh → check eligibility → run Turn Workflow → publish → exit
```

Before writing, the participant must read the latest persisted discussion `README.md` and turns from the repository. Chat history is supporting context, not the source of truth for turn order, topics, or session timing.

A scheduled trigger does not guarantee an argumentative turn. Follow the common no-op, terminal-turn, research-block, and synthesis rules when applicable.

If a stop condition makes synthesis eligible before `ends_at`, the **next A invocation synthesizes immediately** instead of waiting for the session boundary. Later scheduled invocations no-op against the completed discussion.

Never wait inside one invocation for the other participant. The next scheduled invocation resumes from persisted repository state.

## Session End

The session window is a timebox, not a turn quota.

- No B argumentative invocation is scheduled at or after `ends_at`.
- If the discussion is still open at `ends_at`, A performs finalization instead of starting a new argumentative turn.
- The last participant turn may belong to A or B; a normally completed discussion ends with A synthesis.
- If required evidence or repository access prevents a valid synthesis, A records the blocked state and unresolved requirement instead of pretending completion.
- If the reserved final A invocation is missed or paused, recover by invoking A again; A synthesizes from the persisted repository state rather than replaying missed turns.

## Prompt Templates

Use these templates as the initial user messages for the two ChatGPT chats:

- [A — Lead Prompt](../_templates/discuss/openai-chatgpt-scheduled/a-prompt.md)
- [B — Challenger Prompt](../_templates/discuss/openai-chatgpt-scheduled/b-prompt.md)

Fill the same repository, discussion ID, goal, and schedule configuration in both prompts. Keep common discussion behavior in `discuss.md` instead of duplicating it here or in both prompts unless ChatGPT needs the instruction to execute correctly.

## Boundaries

- Do not move task IDs, recurrence syntax, model names, notification settings, or UI instructions into the common `discuss` contract.
- Do not hard-code topic count in this extension; topic scope belongs to the discussion goal and common `discuss` rules.
- Do not infer eligibility from wall-clock order alone; persisted turns decide who may act.
- Do not let both chats write the same shared state. A owns shared discussion state; B owns only B turns.
- Do not treat a missed scheduled invocation as a broken discussion. Resume from the latest valid persisted state.
- Do not configure `participant_interval` faster than the platform supports.
