# OpenAI ChatGPT Scheduled Discussion

This document extends [`discuss.md`](discuss.md) for scheduled discussions run by two OpenAI ChatGPT chats.

The common `discuss` protocol remains authoritative for bundle structure, participant ownership, turn workflow, eligibility, recovery, stop conditions, and synthesis. This extension owns only ChatGPT-specific scheduling and bootstrap behavior.

## Runtime Model

Use two independent ChatGPT chats: one for **A**, one for **B**.

Both chats receive their role prompt at approximately the same session start, but their first discussion actions are offset.

```text
T+00m  A1
T+30m  B1
T+60m  A2
T+90m  B2
T+120m A3
T+150m B3
...
```

Default schedule:

| Participant | First action | Recurrence |
| --- | --- | --- |
| A | immediately | every 60 minutes |
| B | after 30 minutes | every 60 minutes |

The effective discussion cadence is therefore 30 minutes while each participant runs at most once per hour.

The offset and recurrence are runtime configuration, not part of the common discussion artifact contract.

## Bootstrap

### A

When the A prompt is first submitted:

1. read the repository and discussion guidance;
2. create or initialize the discussion bundle when needed;
3. publish the first eligible A turn immediately;
4. arrange later A invocations at the configured recurrence until the session ends.

A is the Lead and carries Moderator coordination as defined by `discuss.md`.

### B

When the B prompt is first submitted:

1. read the repository and discussion guidance;
2. identify the discussion bundle and session window;
3. do **not** publish a B turn immediately when A has not yet published A1;
4. arrange the first B invocation for the configured offset, normally 30 minutes after session start;
5. on that invocation, refresh persisted state, read A's latest eligible turn, then publish B1;
6. continue at the configured recurrence until the session ends.

Bootstrap configuration is not itself a participant turn.

## Invocation Contract

Every scheduled invocation follows the common rule:

```text
refresh → check eligibility → run Turn Workflow → publish → exit
```

Before writing, the participant must read the latest persisted `README.md` and turns from the repository. Chat history is supporting context, not the source of truth for turn order.

A scheduled trigger does not guarantee that an argumentative turn should be written. If the participant is not eligible, the topic is closed, synthesis is due, material evidence is missing, or no material delta exists, follow the common no-op, terminal-turn, research-block, or synthesis rules instead.

Never wait inside one invocation for the other participant. The next scheduled invocation resumes from persisted repository state.

## Session End

The session window is a timebox, not a turn quota.

- Stop early when common discussion stop conditions are met.
- After session expiry, start no new argumentative turn.
- A may synthesize persisted results when synthesis is eligible.
- A completed or blocked discussion should not keep producing equivalent turns merely because scheduled triggers remain.

## Prompt Templates

Use these templates as the initial user messages for the two ChatGPT chats:

- [A — Lead Prompt](../_templates/discuss/openai-chatgpt-scheduled/a-prompt.md)
- [B — Challenger Prompt](../_templates/discuss/openai-chatgpt-scheduled/b-prompt.md)

Fill only the discussion-specific placeholders. Keep common protocol details in `discuss.md` instead of duplicating them into each prompt unless ChatGPT needs the instruction to execute correctly.

## Boundaries

- Do not move ChatGPT task IDs, recurrence syntax, model names, notification settings, or UI instructions into the common `discuss` contract.
- Do not infer eligibility from wall-clock order alone; persisted turns decide who may act.
- Do not let both chats write the same shared state. A owns shared discussion state; B owns only B turns.
- Do not treat a missed scheduled invocation as a broken discussion. Resume from the latest valid persisted state.
- Do not require exactly 30/60-minute timing. Preserve the phase-offset pattern when runtime constraints require another interval.
