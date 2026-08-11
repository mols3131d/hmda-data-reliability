# OpenAI ChatGPT Scheduled Discussion

This document extends [`discuss.md`](discuss.md) for scheduled discussions run by two OpenAI ChatGPT chats.

The common `discuss` protocol remains authoritative for bundle structure, participant ownership, turn workflow, eligibility, recovery, stop conditions, and synthesis. This extension owns only ChatGPT-specific scheduling and bootstrap behavior.

## Preconditions

Use this extension only when scheduled runs can access and update the shared GitHub discussion state required by `discuss.md`.

- Two active Scheduled Task slots are required: one for A and one for B.
- The scheduled run must be able to use the required GitHub connection or tool with sufficient repository permissions.
- Do not depend on files attached only to a ChatGPT Project; Scheduled Tasks may not have access to those project files. Keep durable discussion state in the repository.
- If a scheduled run cannot read or persist the required repository state, treat the discussion as blocked instead of reconstructing state from chat memory.

OpenAI currently limits a Scheduled Task to at most one run per hour. The default pattern below respects that limit by using two independent hourly tasks with a 30-minute phase offset. See [Scheduled Tasks in ChatGPT](https://help.openai.com/en/articles/10291617-tasks-in-chatgpt).

## Runtime Model

Use two independent ChatGPT chats: one for **A**, one for **B**.

Both prompts use the same absolute session anchors. Persist these anchors in the discussion `README.md` and treat the persisted values as the source of truth.

For the default hourly pattern:

- `ends_at` must be later than `started_at`;
- session duration must be a whole number of hours so `ends_at` is an A recurrence boundary.

```text
T+00m       A1
T+30m       B1
T+60m       A2
T+90m       B2
...
T+(N-30)m   Bn
T+Nh        A finalization
```

| Participant | First action | Recurrence | End boundary |
| --- | --- | --- | --- |
| A | immediately | every 60 minutes | `ends_at` is reserved for finalization if still open |
| B | after 30 minutes | every 60 minutes | last invocation is strictly before `ends_at` |

The discussion therefore advances every 30 minutes while each participant task runs at most once per hour.

The offset, recurrence, and absolute session timestamps are runtime configuration, not part of the common discussion artifact contract.

## Bootstrap

### A

When the A prompt is first submitted:

1. read the repository and discussion guidance;
2. validate the shared session anchors;
3. create or initialize the discussion bundle when needed;
4. persist `started_at` and `ends_at`;
5. publish the first eligible A turn immediately;
6. arrange later A invocations at 60-minute intervals through `ends_at`.

A is the Lead and carries Moderator coordination as defined by `discuss.md`.

### B

When the B prompt is first submitted:

1. read the repository and discussion guidance;
2. validate the same session anchors;
3. do not create the discussion bundle or A-owned shared state;
4. do **not** publish a B turn immediately;
5. arrange the first B invocation for `started_at + 30 minutes` and later B invocations every 60 minutes while the scheduled time is strictly before `ends_at`.

If the bundle does not yet exist during B bootstrap, schedule from the shared absolute session anchors and exit. The first scheduled B invocation must re-read the repository; if A still has not initialized the bundle or published A1, follow the common recovery rules.

Bootstrap configuration is not itself a participant turn.

## Invocation Contract

Every scheduled invocation follows the common rule:

```text
refresh → check eligibility → run Turn Workflow → publish → exit
```

Before writing, the participant must read the latest persisted discussion `README.md` and turns from the repository. Chat history is supporting context, not the source of truth for turn order or session timing.

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

Fill the same discussion ID, goal, `started_at`, and `ends_at` in both prompts. Keep common protocol details in `discuss.md` instead of duplicating them into each prompt unless ChatGPT needs the instruction to execute correctly.

## Boundaries

- Do not move task IDs, recurrence syntax, model names, notification settings, or UI instructions into the common `discuss` contract.
- Do not infer eligibility from wall-clock order alone; persisted turns decide who may act.
- Do not let both chats write the same shared state. A owns shared discussion state; B owns only B turns.
- Do not treat a missed scheduled invocation as a broken discussion. Resume from the latest valid persisted state.
- Do not create a faster-than-hourly task for either participant. Use the phase offset between two hourly tasks to obtain the effective 30-minute discussion cadence.
