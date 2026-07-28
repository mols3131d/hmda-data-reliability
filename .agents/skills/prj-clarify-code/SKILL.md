---
name: prj-clarify-code
description: "Use when improving the readability of complex project code without changing behavior. Apply for naming, intent comments, responsibility boundaries, or minimal refactoring. Do not use for feature work, performance work, documentation, or general code review."
---

# Clarify Code

Preserve behavior. Remove the main reading bottleneck. Make the smallest change.

## Use When

- Complex function or module
- Mixed responsibilities or unclear call-site intent
- Vague names or comments that explain `what`, not `why`

## Do Not Use When

- Feature, API, performance, or architecture changes
- Correctness-focused code review
- User-facing documentation

## Workflow

1. Read the target, direct callers, and related tests. Expand only for shared contracts.
2. Name the bottleneck: scattered flow, mixed responsibility, hidden policy, or complex expression.
3. Choose the smallest fix:
   - vague name: rename;
   - hidden policy or constraint: add one intent comment;
   - independent responsibility with a clearer call site: extract a function;
   - nested or mixed abstraction levels: simplify control flow.
4. Preserve public APIs, return values, exceptions, state, side-effect order, logs, and validation.
5. Run relevant tests before and after. Without tests, use static, type, or I/O checks and report the gap.
6. Remove unrelated formatting and future-only abstractions.

## Guardrails

- Comment only on policies, exceptions, ordering, or constraints the code cannot clarify.
- Do not extract helpers only to reduce line count.
- Do not add one-use abstractions, future extension points, or navigation overhead.
- Use one name or comment for each intent; do not duplicate explanations.
- Preserve error handling, validation, and observability.

## Report

Report briefly:

- Bottleneck and change
- Preserved behavior
- Validation
- Gaps and risks

If no change is needed, report why and what would justify one.
