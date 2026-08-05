# Artifact Consistency Report

## Summary

- Scope: `openspec/specs/`, `src/`, `tests/`
- Target / Baseline: `main` branch (commit `HEAD`)
- Verification loops: `1/1`
- Result: findings

## Findings

### CON-SPECS-001 — Stale reference to deleted scratch documentation

- **Status:** verified
- **Severity:** info
- **Type:** stale-reference
- **Owner:** OpenSpec
- **Relation:** `openspec/specs/foundation-baseline/spec.md` ↔ Repository file system (`scratch/docs/`)
- **Expected:** `foundation-baseline/spec.md` scenario expects `scratch/docs/foundation.md`, `scratch/docs/mvp_scope.md`, and `scratch/docs/memo.md` to exist as input evidence references.
- **Actual:** `scratch/docs/` directory and files were deleted after migration to canonical `docs/development/foundation/` and `openspec/specs/`.
- **Evidence:**
  - `openspec/specs/foundation-baseline/spec.md#L15` — scenario references `scratch/docs/foundation.md`, `scratch/docs/mvp_scope.md`, `scratch/docs/memo.md`
  - `file_search(query="scratch/**")` — returned 0 matching files in workspace
- **Impact:** Specification contains a broken file path reference to private scratch notes that were already cleaned up.
- **Reproduction:** Inspect `openspec/specs/foundation-baseline/spec.md#L15` and query `scratch/docs/` in workspace.
- **Fingerprint:** `stale-reference+openspec/specs/foundation-baseline/spec.md+scratch/docs/foundation.md+deleted-scratch-files+2026-08-04`

### CON-SPECS-002 — Active change delta specs not yet synced to main durable spec

- **Status:** verified
- **Severity:** info
- **Type:** handoff-gap
- **Owner:** OpenSpec
- **Relation:** `openspec/changes/hmda-eda-foundation-extension/specs/` ↔ `openspec/specs/hmda-eda-baseline/spec.md`
- **Expected:** OpenSpec active change `hmda-eda-foundation-extension` adds new requirements (`action_taken`, `loan_purpose`, `state_code` distributions, five-number summary, grain alignment) which are fully implemented in `src/project_pivot/hmda_data/eda/` and tested in `tests/hmda_data/eda/`.
- **Actual:** Main spec `openspec/specs/hmda-eda-baseline/spec.md` does not yet contain these delta requirements because the active change has not been archived or synced via `openspec sync-specs`.
- **Evidence:**
  - `openspec/changes/hmda-eda-foundation-extension/specs/hmda-eda-foundation/spec.md#L20-L80` — contains `Core code distributions`, `Numeric summary and anomaly observation`, `MVP grain alignment`
  - `openspec/specs/hmda-eda-baseline/spec.md` — contains baseline requirements without new field distributions
  - `src/project_pivot/hmda_data/eda/analysis.py#L80-L240` — implements distributions, numeric summaries, and grain alignment
- **Impact:** Main durable spec does not reflect in-progress active change delta requirements until `openspec-sync-specs` or change archive is executed.
- **Reproduction:** Compare `openspec/changes/hmda-eda-foundation-extension/specs/hmda-eda-foundation/spec.md` with `openspec/specs/hmda-eda-baseline/spec.md`.
- **Fingerprint:** `handoff-gap+openspec/changes/hmda-eda-foundation-extension/specs/hmda-eda-foundation/spec.md+openspec/specs/hmda-eda-baseline/spec.md+active-delta-unarchived+2026-08-04`

### CON-SPECS-003 — Archive directory locator date prefix discrepancy

- **Status:** verified
- **Severity:** info
- **Type:** drift
- **Owner:** OpenSpec
- **Relation:** `openspec/specs/foundation-baseline/spec.md` ↔ `openspec/changes/archive/`
- **Expected:** `foundation-baseline/spec.md` scenario states archived change location as `openspec/changes/archive/complete-foundation-baseline`.
- **Actual:** Physical archive directory includes date prefix `openspec/changes/archive/2026-06-10-complete-foundation-baseline/`.
- **Evidence:**
  - `openspec/specs/foundation-baseline/spec.md#L79` — references `openspec/changes/archive/complete-foundation-baseline`
  - `file_search` locator — physical path is `openspec/changes/archive/2026-06-10-complete-foundation-baseline/`
- **Impact:** Exact string match for archive folder path in spec omits date prefix `2026-06-10-`.
- **Reproduction:** Compare string in `openspec/specs/foundation-baseline/spec.md#L79` with `openspec/changes/archive/` directory names.
- **Fingerprint:** `drift+openspec/specs/foundation-baseline/spec.md+openspec/changes/archive/2026-06-10-complete-foundation-baseline+date-prefix-omission+2026-08-04`

## Coverage

- Relations checked:
  - 18 main durable specifications under `openspec/specs/`
  - 76 Python source modules under `src/project_pivot/`
  - 39 Python test modules under `tests/`
  - Active change delta specs under `openspec/changes/hmda-eda-foundation-extension/specs/`
- Evidence and commands:
  - `uv run pytest tests/hmda_data/ tests/reliability/ tests/data_operations/ tests/data_platform/ tests/orchestration/ tests/dbt/` (115 passed)
  - `file_search` for `scratch/**` and `openspec/changes/archive/*`
- Exclusions and limitations:
  - Markdown formatting checks and code style/linting were excluded per mode boundaries.
  - Source artifacts were not modified.
