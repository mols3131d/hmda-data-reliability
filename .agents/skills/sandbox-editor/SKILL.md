---
name: sandbox-editor
description: >
  USE WHEN: Creating, editing, modifying, or updating interactive sandbox scripts to resolve understanding bottlenecks.
  EXCLUDES: General refactoring, test automation, or fixing production code.
---

# Sandbox Editor

## Goal

Generate interactive sandbox scripts ("Micro World"). Expose inputs, hidden state transitions, and adjacent module interactions. Enable users to safely explore production logic and restore "Peripheral Vision".

## Non-Goal

- Output static code without tweakable inputs.
- Modify or refactor production source code.

## When to Use

- Request to create, generate, edit, or modify a sandbox file.
- User faces "understanding bottleneck" and needs manual experimentation space.

## When NOT to Use

- Request to automatically test, explore, or fix code autonomously.
- General refactoring or feature development.

## Instructions

- **Observable Inputs**: Isolate input parameters at script top. Prompt user to tweak.
- **State Transitions**: Format logs as clear state transitions (`Input -> Process -> Output`).
- **Safe State**: Write experimental outputs to `tmp/`. Never mutate production data.
- **Clear Boundary**: Comment boundary between "sandbox observation" and "production intent".
- **Naming**: Prefix filename with `sandbox_`.

## Constraints

- **Zero Execution**: Never run the generated sandbox script yourself.
- **Direct Import**: Never copy production logic. Import directly from source.

## Workflow: Sandbox Editor

### Arguments from Context

- Target sandbox location (Default: `sandboxes/` or existing path)
- Target logic and understanding bottleneck

### Procedure

1. Parse intent to identify the target logic and understanding bottleneck. If the bottleneck or suitable sandbox experience is unclear, read [references/understanding-bottleneck.md](references/understanding-bottleneck.md).
2. Determine sandbox location (User path -> Existing `sandboxes/` -> Default `sandboxes/`).
3. Select and read required assets from the route selection:
   - [references/write-marimo-sandbox.md](references/write-marimo-sandbox.md) when building a Python sandbox.
   - [references/add-observability.md](references/add-observability.md) when state transitions need visibility.
   - [references/use-mock-patch.md](references/use-mock-patch.md) when internal calls need interception.
   - [references/understanding-bottleneck.md](references/understanding-bottleneck.md) when the goal or bottleneck is unclear.
4. Scaffold sandbox script, importing target logic directly.
5. Apply the selected observability approach without changing production code.
6. Output script path. Wait for user to tweak and execute.

### Validation

- The generated script path is displayed to the user.
- Production code remains completely unmodified.
