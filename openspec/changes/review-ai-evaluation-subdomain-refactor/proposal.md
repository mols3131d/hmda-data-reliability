---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Review AI Evaluation Subdomain Refactor
description: Review AI 평가 코드의 ownership과 Python module surface를 review_ai.evaluation 아래에 정리한다.
tags:
  - "domain:review-ai"
  - "subdomain:evaluation"
---

## Why

Review AI 실행, human evaluation과 Langfuse adapter가 모두 `review_ai`의 같은 package level에 있어 어느 코드가 review 결과를 만들고 어느 코드가 평가 책임을 소유하는지 구분하기 어렵다. Evaluation contract는 이미 baseline/candidate comparison, human rubric과 exact output identity를 묶는 독립 의미가 있으므로 그 책임을 `review_ai.evaluation` 아래에 모은다.

Review AI 이외의 두 번째 AI evaluation consumer는 아직 없다. 따라서 공통 top-level evaluation domain을 도입하면 공유 근거보다 추상화 비용이 앞선다. Recovery/replay evaluation은 계속 `reliability`가 소유한다.

## What Changes

- Review AI evaluation contracts와 Langfuse adapter를 `review_ai.evaluation` package로 이동한다.
- Evaluation Python API에서 `utility` 이름을 `review value` 이름으로 정리하면서 기존 rubric 의미, wire data와 output digest 동작을 보존한다.
- 이동 후에도 public package surface, live-harness child process 경계와 문서 경로가 올바른 module을 가리키게 한다.

## Boundaries

- **In Scope:** Evaluation module ownership, Python symbol names, package exports, Langfuse invocation path, tests, canonical Review AI Spec과 관련 guide.
- **Out of Scope:** `reliability.evaluation` 통합, generic evaluation framework, automatic LLM judge, rubric scoring 변경, `utility_contributions` provider contract 변경, remote Langfuse proof.

## Capabilities

### Modified Capabilities

#### `reliability-agentic-review`

- Preserve the existing human rubric, same-case comparison rules, provenance binding, serialized field/value contract and fail-closed behavior while naming the public evaluation artifacts as Review Value.
- Keep Langfuse an optional adapter; preserve child-process isolation, timeout, environment allowlist, media upload disable and sanitized failure behavior.

## Impact

- `src/hmda_reliability/review_ai/` evaluation modules and package exports.
- `scripts/run_agentic_review_live.py` child invocation path.
- `tests/review_ai/` evaluation, Langfuse and public-surface tests.
- `openspec/specs/reliability-agentic-review/spec.md` and Review AI/testing documentation.
