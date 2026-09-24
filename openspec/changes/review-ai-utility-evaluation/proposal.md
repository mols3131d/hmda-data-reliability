---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: "Review AI Utility Proofs"
description: "Bounded review context와 human-rubric comparison으로 Review AI의 MVP utility를 증명한다."
---

## Why

현재 Review AI는 deterministic facts, Evidence reference와 invocation provenance는 검증하지만, 사람이 다음 조사·복구 판단에 실제로 도움이 되는지와 변경 전후 utility를 비교할 contract가 없다. MVP acceptance의 네 Utility Proofs를 같은 representative case에서 재현 가능하게 닫아야 한다.

## What Changes

- `reliability-agentic-review`에 incident 주변 evidence를 bounded projection으로 선택하고 provenance와 context gap을 보존하는 Review Context contract를 추가한다.
- Agentic output에 deterministic facts와 `RemediationDraft` 재진술을 넘어서는 구조화된 utility contribution을 추가한다.
- `rubric_v1`의 다섯 human evaluation criterion을 구현하고 positive/restatement-negative/hedging-negative 사례를 test fixture로 사용한다.
- baseline과 candidate output을 같은 case와 rubric으로 평가하고 human decision, rationale, invocation identity와 change-under-test를 comparison evidence로 연결한다.
- 기존 advisory/read-only 및 proposal-bound approval 경계를 유지하고, 실제 provider와 자동 LLM judge를 MVP proof의 authority로 사용하지 않는다.

## Boundaries

- **In Scope:** `review_ai` contracts, context projection, human utility evaluation/comparison models, deterministic tests, representative fixtures와 관련 문서.
- **Out of Scope:** incident detection, `RemediationDraft` 또는 recovery authority 변경, automatic recovery, LLM-as-a-judge, 외부 evaluation platform, live provider 운영 자동화.

## Capabilities

기존 `reliability-agentic-review` capability의 review input/output와 provenance 계약을 확장한다. 새 capability는 만들지 않는다.

## Impact

| Surface | Impact |
| --- | --- |
| **Code / Systems** | `review_ai`가 bounded context projection과 utility evaluation/comparison을 소유한다. 기존 `reliability` deterministic contract와 `runtime_ai` provider mechanics는 변경하지 않는다. |
| **Data / Contracts** | context provenance/gap, utility contribution, human rubric score와 comparison decision의 frozen Pydantic contract를 추가한다. |
| **Interfaces / APIs** | 기존 review prompt가 bounded context를 사용하고, caller가 human-scored output을 비교 가능한 contract로 구성한다. |
| **Evidence** | human evaluation과 baseline/candidate comparison을 identity와 rationale에 연결하되 전용 persistence를 요구하지 않는다. |
| **Safety** | utility output은 advisory evidence일 뿐 approval, proposal, recovery 또는 mutation authority가 아니다. |
