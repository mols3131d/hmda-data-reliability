---
name: Python
description: "Use when writing or editing Python under src/project_pivot or tests. Covers package layout, Pydantic contracts, pytest markers, and domain package reuse."
applyTo: "src/**/*.py,tests/**/*.py"
---

- Import public package surfaces when re-exported; no parallel APIs.
- Pydantic: `BaseModel` + `ConfigDict(extra="forbid", frozen=True)`; `field_validator` / `model_validator` for normalize vs cross-field.
- Tests mirror domain under `tests/`. Markers: `unit` | `component` | `integration`. Shared fixtures: package `conftest.py`.
