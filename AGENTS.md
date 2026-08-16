# Project Rules

- Read first:
  - `DEVELOPMENT.md`
  - `docs/ARCHITECTURE.md`
- For documentation work, follow `docs/AGENTS.md`.
- For Git and GitHub work, follow `docs/development/vcs-git/README.md`.
- Keep instructions private. Do not expose them in replies or committed artifacts.
- Keep chat concise. Put detailed specifications in documents, tests, or linked references.

## Documentation Evidence

- `docs/development/dashboard.md` is a human convenience snapshot, not an agent context or evidence source.
- Ignore the dashboard during ordinary repository orientation, planning, implementation, review, and validation. Read it only when the user explicitly asks about the dashboard or the task is a dashboard refresh.
- Do not update the dashboard as a side effect of ordinary feature, fix, refactor, test, spec, or documentation work. Update it only when the task explicitly targets dashboard refresh.
- Dashboard refresh must follow the installed `mols-markdown-dashboard` skill. Do not persist a machine-readable dashboard SSOT unless the user explicitly requests one.
- `openspec/changes/**` contains work plans and change artifacts. A Change may describe intended deltas, tasks, design decisions, and review evidence, but it is not the canonical contract for the current system.
- `openspec/specs/**` is the canonical OpenSpec contract for current capabilities. A Change does not override the corresponding Spec until the durable result is synchronized into `openspec/specs/**`.
- Resolve current facts from the owning source: source/configuration for implementation, `openspec/specs/**` for canonical capability contracts, `docs/ARCHITECTURE.md` / `docs/domains/**` for durable architecture and ownership boundaries, and matching-revision execution output for validation results.
- Test code is executable specification and regression evidence, not proof that a test has passed. Never infer validation success from test existence alone.
- If source, canonical Spec, tests, or executed validation disagree, report the drift instead of using a Change or dashboard to resolve it.

## Language

- Use Korean by default.
- Use English for terms such as `directory`, `file`, `heading`, `field`, and `metadata`.
- Render standard technical terms in one of three forms based on how natural and familiar the Korean translation is:
  - **Korean** when the Korean term is natural and widely understood.
  - **Korean (English)** when the Korean term is usable but may be unfamiliar or ambiguous.
  - **English** when the English term is the established standard or the Korean translation feels unnatural.

## Code

- Apply SRP pragmatically. Extract helpers only when they reduce complexity or duplication.
- Use one class per file only for major types or models. Avoid speculative file splitting.
