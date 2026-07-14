---
name: use-mock-patch
description: >
  What: Use mocks/spies in sandbox scripts to expose hidden internal states.
  When: Target function is opaque, direct modification is unsafe.
  Not: Simple pure functions.
  Keywords: mock, patch, spy, intercept, observability.
---

# Sandbox Mock/Patch

## Goal
Expose hidden internal states, intermediate variables, and adjacent module interactions via mocks/spies. Do not modify production code.

## Non-Goal
- Automated test suites.
- Mock dependencies just to bypass them without observing states.

## When to Use
- Target function is "black box". Direct modification unsafe/impossible.

## When NOT to Use
- Target is pure function. Direct input/output logging sufficient.

## Workflows
1. Identify target function and internal calls to expose.
2. Scaffold standalone sandbox script importing function.
3. Apply patches/spies to internal dependencies.
4. Execute and print captured states.

## Instructions
- **Match Framework**: Inspect dependencies/tests. Use existing mocking framework.
- **Prefer Spies**: Use spy/wrap techniques over hardcoded mock returns. Capture real sequence.
- **Visual Print**: Print intercepted states clearly (e.g., `[Intercepted Call 1] calc_tax() returned: ...`).

## Constraints
- NO production code alteration.
- NO hallucinated testing libraries absent from project ecosystem.
