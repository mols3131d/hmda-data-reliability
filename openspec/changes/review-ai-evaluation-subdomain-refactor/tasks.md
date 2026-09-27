---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Review AI Evaluation Subdomain Refactor
description: Move evaluation ownership into a bounded Review AI subpackage and preserve runtime, Python API boundaries and serialized evidence guarantees.
tasks_completed: 4
tasks_total: 4
---

## Tasks

- [x] Move evaluation value contracts into `review_ai.evaluation` and rename the Python evaluation API to Review Value.
  - **Covers:** Versioned human utility evaluation; baseline and candidate utility comparison evidence.
  - **Test first:** Update/add tests for `ReviewValueRubric`, `ReviewValueAssessment`, comparison, rendering, digest and the intended package-root export set. Pin a representative serialized comparison and output digest before moving code; confirm these tests fail on the current surface.
  - **Done when:** The value contracts live in `review_ai/evaluation/value.py`; `review_ai.evaluation` and the curated `review_ai` root expose only intended new names; rubric behavior, fail-closed comparison, JSON fields/enum values and the digest vector match the pre-migration evidence.

- [x] Move the optional Langfuse adapter and update its script and child-process entrypoints.
  - **Test first:** Update projection tests to import the future module path, assert the spawned argv uses `python -m hmda_reliability.review_ai.evaluation.langfuse`, and verify disabled export never spawns a child. Add an importable-module assertion; the old mocked command tests alone are insufficient.
  - **Done when:** Projection and annotation helpers live in `review_ai/evaluation/langfuse.py`; the live harness and subprocess launcher use the new path; timeout, environment allowlist, forced media-disable, sanitized errors and `submitted_unverified` status retain their current behavior.

- [x] Update canonical and human-facing references for the new owner and API names.
  - **Covers:** Versioned human utility evaluation; baseline and candidate utility comparison evidence.
  - **Done when:** The canonical Review AI Spec, `docs/domains/review-ai.md`, `docs/development/testing.md`, package public-surface test and internal call sites consistently use the new module/symbol names; MVP utility acceptance and `utility_contributions` wire fields remain unchanged.

- [x] Verify the complete migration against focused and repository-wide contracts.
  - **Done when:** Review AI evaluation/Langfuse tests, Review AI and Runtime AI suites, project type/lint checks, Tach, strict OpenSpec validation, changed Markdown and Inbox checks pass; no `reliability.evaluation` files/tests or live Langfuse destination were changed.
