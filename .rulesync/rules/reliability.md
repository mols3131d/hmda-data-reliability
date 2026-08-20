---
root: false
targets:
  - copilot
description: "Use when editing reliability detection, impact, remediation, recovery, evaluation, contracts, or related tests. Covers read-only lifecycle boundaries and separate recovery/evaluation APIs."
globs:
  - "src/project_pivot/reliability/**"
  - "tests/reliability/**"
copilot:
  name: "Reliability"
---

# Reliability

- Lifecycle (read-only): detect → impact → remediation **draft**. No approval, backfill, or validation side effects inside lifecycle.
- Public hub: `project_pivot.reliability` re-exports. External callers use package exports, not deep private imports.
- Recovery only after external approval (e.g. `execute_approved_backfill`). Evaluation: `build_evaluation_report` / `write_evaluation_report` — separate from lifecycle.
- Contracts: `reliability/contracts` — same Pydantic defaults as Project Pivot instructions, plus `allow_inf_nan=False` where used. Errors: `reliability/errors.py`.
