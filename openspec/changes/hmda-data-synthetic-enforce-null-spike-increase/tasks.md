---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Enforce HMDA null-spike increase tasks
description: Implement and verify deterministic null-spike generation that always creates a real, original-relative null increase.
tasks_completed: 5
tasks_total: 5
tags:
  - "domain:hmda-data"
  - "capability:synthetic-defects"
  - "null-spike"
---

## Tasks

- [x] Add component regressions for original-relative null-spike behavior.
  - **Covers:** `Income null spike`, `High-baseline income null spike`, `Fully null target column`, `Missing target column`
  - **Test first:** A high-baseline-null fixture exposes the existing no-op output while an all-null fixture exposes its silent success.
  - **Done when:** Tests directly compare source and generated null rates, prove a non-null value was converted, reject the all-null case without output, and retain the existing row-count-drop and schema-drift assertions.

- [x] Enforce eligible deterministic null-spike mutation in the HMDA synthetic generator.
  - **Done when:** `null_spike` selects non-null target values from the deterministic sample, emits a null rate strictly above the original source rate, raises `SyntheticCaseError` for an impossible all-null target before output creation, and preserves its public signature and source isolation.

- [x] Restore per-year `null_fraction` mutation semantics (review P2).
  - **Covers:** Multi-year clean fixture proving each year receives its requested fraction of mutations, not concentrated in one year.
  - **Test first:** Multi-year all-non-null fixture detects mutation concentration in a single year.
  - **Done when:** Mutation count is computed and applied per `activity_year` partition, the per-year requested fraction behavior is preserved, and the global strict-increase invariant still holds.

- [x] Add `null_fraction` magnitude oracle (review P3).
  - **Covers:** Clean all-non-null fixture verifying that the requested `null_fraction` is reflected in observable output null counts.
  - **Test first:** Oracle asserts each year's null count matches `ceil(year_count * null_fraction)` on a clean input.
  - **Done when:** The magnitude oracle and original-relative oracle coexist, and a hypothetical regression that ignores `null_fraction` would fail the magnitude test.

- [x] Eliminate floating-point threshold dependency with integer arithmetic (review P2 follow-up).
  - **Covers:** Non-binary-exact source ratio with partial sampling boundary.
  - **Test first:** A 70% null source with 90% sample and 1% null fraction fails strict inequality when using float math.
  - **Done when:** Threshold calculation uses exact integer arithmetic (`source_null_count * year_count // source_count + 1`), and test verifies strict inequality using integer products (`output_null_count * source_total > source_nulls * output_total`).
