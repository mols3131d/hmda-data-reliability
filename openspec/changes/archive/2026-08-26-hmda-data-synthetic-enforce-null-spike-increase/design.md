---
type: openspec-spec-driven-tdd-design
category: design
title: Deterministic null-spike selection
description: Preserve synthetic output cardinality while choosing eligible values and enough mutations to meet the original-relative null-rate contract.
---

## Approach

`null_spike` will measure the source and deterministic sampled set before writing an output. The sampled set keeps its current per-`activity_year` cardinality, but ranks non-null target values ahead of already-null values so a successful case has eligible values to mutate. The generator will convert a deterministic set of those eligible values, using the requested fraction as a minimum and increasing the count only when needed to make the emitted null rate strictly greater than the original source rate.

When the target column has no non-null source value, the function will raise the existing `SyntheticCaseError` before `write_case_file` creates a case directory. The public signature, source-file isolation, output schema, and Reliability evaluator boundary remain unchanged.

## Boundaries

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| HMDA synthetic generator | deterministic sample/value selection, synthetic output, impossible-input rejection | incident detection or recovery verdicts |
| Reliability evaluator | consuming the generated full-sample defect and enforcing its existing lifecycle gates | repairing synthetic source generation |

## Decisions

### D1. Compare against the original source rate

- **Decision:** Use source and sampled row/null counts to determine the minimum number of non-null values to convert.
- **Rationale:** A fixed count derived only from sampled rows can leave an emitted partial sample at or below the original source null rate. The count-based comparison preserves a strict result without floating-point ambiguity.

### D2. Reject an impossible case before output creation

- **Decision:** An all-null target raises `SyntheticCaseError` rather than returning a no-op Parquet file.
- **Rationale:** The existing error type already owns invalid synthetic-input/output contracts, and a no-op cannot satisfy the required increase.

## Verification

Focused component tests will compare original and generated null rates directly, including a high-baseline-null source and an all-null rejection with no output. Existing row-count-drop and schema-drift assertions remain as local regressions. The existing Reliability null-spike integration suite validates that the full-sample consumer contract remains intact.
