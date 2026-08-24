---
trigger: glob
globs: "src/project_pivot/**/*"
---

# Project

- Use the package and domain ownership defined in `DEVELOPMENT.md` and `docs/domains/OVERVIEW.md`; do not add a new top-level package when an existing owner fits.
- Keep the data-layer boundary: HMDA source and Bronze ingestion are Python responsibilities; Silver and Gold transformations belong to dbt. Do not build a parallel Python transformation path for dbt-owned models.
- For data-facing APIs, document domain semantics that types cannot express, such as grain, units, missing-value meaning, or idempotency, when callers depend on them; keep broader rules in the canonical domain contract.
- For Pydantic contracts, use `BaseModel` with `ConfigDict(extra="forbid", frozen=True)`; use `field_validator` for field normalization and `model_validator` for cross-field invariants.
- Preserve the local-first architecture. Do not introduce cloud, distributed-processing, or production-control infrastructure unless the project contract explicitly expands to require it.
