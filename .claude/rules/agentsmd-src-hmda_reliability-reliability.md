---
paths:
  - src/hmda_reliability/reliability/**/*
---

# Reliability

- Lifecycle is read-only: detect → impact → remediation **draft**. Do not add approval, backfill, or validation side effects inside lifecycle.
- Public hub: `hmda_reliability.reliability` re-exports the public surface. External callers use package exports, not deep private imports.
- Recovery runs only after external approval, for example `execute_approved_backfill`. Evaluation uses `build_evaluation_report` / `write_evaluation_report` and stays separate from lifecycle.
- Contracts live in `reliability/contracts` and follow the package Pydantic defaults from the parent `AGENTS.md`, plus `allow_inf_nan=False` where used. Errors live in `reliability/errors.py`.
