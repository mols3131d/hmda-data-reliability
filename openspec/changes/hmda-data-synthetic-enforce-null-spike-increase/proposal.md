---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Enforce HMDA null-spike increase
description: Ensure deterministic null-spike output actually increases the target null rate and rejects an impossible all-null request.
tags:
  - "domain:hmda-data"
  - "capability:synthetic-defects"
  - "null-spike"
---

## Why

The canonical synthetic-defects contract requires a `null_spike` output to have a target-column null rate greater than its source. The current generator ranks every sampled row before assigning `NULL`, so it can select rows that are already null and emit no increase. The existing test only checks an absolute output ratio, allowing that false green.

## What Changes

- Select existing non-null target values when injecting a `null_spike`, so a valid request creates an actual null-rate increase.
- Reject an all-null target column as a `SyntheticCaseError` instead of emitting a no-op synthetic defect.
- Add original-relative null-rate and failure-oracle coverage while preserving current row-count drop, schema-drift, and Reliability consumer behavior.

## Boundaries

- **In Scope:** Deterministic HMDA `null_spike` generation, its canonical synthetic-defect contract, and focused executable specifications.
- **Out of Scope:** New incident types, freshness semantics, recovery/evaluation redesign, Agentic/LLM work, schema-drift expansion, and dashboard updates.

## Capabilities

### Modified Capabilities

#### `hmda-data-synthetic-defects`

- Make the existing null-spike requirement explicit for high-baseline-null inputs and the impossible all-null target state.

## Impact

- `src/hmda_reliability/hmda_data/synthetic/cases.py`
- `tests/hmda_data/test_synthetic.py`
- `openspec/specs/hmda-data-synthetic-defects/spec.md`
- Focused Reliability null-spike evaluation validation only; no public API or Reliability implementation change is intended.
