---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Enforce HMDA null-spike increase tasks
description: Implement and verify deterministic null-spike generation that always creates a real, original-relative null increase.
tasks_completed: 2
tasks_total: 2
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
