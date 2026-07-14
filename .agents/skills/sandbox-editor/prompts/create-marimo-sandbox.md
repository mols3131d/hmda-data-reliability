---
name: create-marimo-sandbox
description: >
  What: Create Python Marimo sandbox with reactive cells to fix user bottlenecks.
  When: User requests Python sandbox or interactive code exploration.
  Not: Non-notebook languages, standard .py script requests.
  Keywords: marimo, python, sandbox, interactive, reactive.
---

# Create Marimo Sandbox

## Goal
Build reactive Marimo sandbox. Solve user bottleneck via interactive variables & instant feedback.

## Non-Goal
- Static output without interactivity.

## When to Use
- Request Python sandbox.
- User needs interactive code exploration.

## When NOT to Use
- Non-notebook languages.
- Request standard `.py` script.

## Instructions
- **Syntax**: Follow <https://github.com/marimo-team/skills>.
- **Isolate Setup**: Put `notebook_init()` in first cell.
- **Expose Variables**: Extract key params to standalone cell. Add comment: "Edit this".
- **Enable Explore**: Provide code to call methods/queries on objects. Don't just print final state.
- **Reactive Modules**: Pass state via `return` -> `arg`. Ensure edits auto-trigger dependents.

## Constraints
- NO hidden hardcoded variables.
- NO multi-step monolithic cells.
- MUST use Marimo syntax (`@app.cell`).
