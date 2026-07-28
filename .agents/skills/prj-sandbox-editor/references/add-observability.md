---
name: add-observability
description: >
  What: Inject observability logs into sandbox code to expose internal state changes.
  When: Resolving understanding bottleneck via Timeline Debugger experience.
  Not: Functional changes, bug fixes, unit tests.
  Keywords: observability, logs, timeline debugger, state transitions.
---

# Add Observability

## Goal

Transform code into "Timeline Debugger". Expose internal behavior, data transformations, and state changes step-by-step.

## Non-Goal

- Raw execution logs without timeline context.

## When to Use

- Make internal state transitions visible for human understanding.

## When NOT to Use

- Request functional changes, bug fixes, or unit tests.

## Workflows

1. Identify opaque state changes.
2. Inject observability logs (e.g., `print`, structured logs).
3. Format traces as state transitions.
4. Output runnable code.

## Instructions

- **Log Explicitly**: Capture intermediate variables, loop iterations, branches, exceptions.
- **Visual Transitions**: Format output as timeline. Use separators, step numbers, labels (`[State A] -> (Transformation) -> [State B]`).
- **Distinct Traces**: Make added logs visually distinct from original output.

## Constraints

- NO logic alteration. Only add logs. Do not alter existing logic, return types, or algorithms.
