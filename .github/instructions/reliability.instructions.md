---
name: Reliability
description: "Use when editing reliability detection, impact, remediation, recovery, evaluation, contracts, or related tests. Covers read-only lifecycle boundaries and separate recovery/evaluation APIs."
applyTo: "src/hmda_reliability/reliability/**,tests/reliability/**"
---

- Lifecycle (read-only): detect → impact → remediation **draft**. No approval, backfill, or validation side effects inside lifecycle.
- Public hub: `hmda_reliability.reliability` re-exports. External callers use package exports, not deep private imports.
- Recovery only after external approval (e.g. `execute_approved_backfill`). Evaluation: `build_evaluation_report` / `write_evaluation_report` — separate from lifecycle.
- Contracts: `reliability/contracts` — same Pydantic defaults as Project instructions, plus `allow_inf_nan=False` where used. Errors: `reliability/errors.py`.
