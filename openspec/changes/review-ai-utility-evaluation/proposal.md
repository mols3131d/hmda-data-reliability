---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: "Review AI Utility Proofs"
description: "Bounded review context와 human-rubric comparison으로 Review AI의 MVP utility를 증명한다."
---

## Why

현재 Review AI는 deterministic facts, Evidence reference와 invocation provenance는 검증하지만, 사람이 다음 조사·복구 판단에 실제로 도움이 되는지와 변경 전후 utility를 비교할 수 있는 durable proof가 없다. MVP acceptance의 네 Utility Proofs를 같은 representative case에서 재현 가능하게 닫아야 한다.

## What Changes

- `reliability-agentic-review`에 incident 주변 evidence를 bounded projection으로 선택하고 provenance와 context gap을 보존하는 Review Context contract를 추가한다.
- Agentic output에 deterministic facts와 `RemediationDraft` 재진술을 넘어서는 구조화된 utility contribution을 추가한다.
- `rubric_v1`의 다섯 human evaluation criterion과 positive/negative control discrimination을 local fixture로 고정한다.
- baseline과 candidate output을 같은 case와 rubric으로 평가하고 human decision, rationale, invocation identity와 change-under-test를 durable comparison evidence로 기록한다.
- 기존 advisory/read-only 및 proposal-bound approval 경계를 유지하고, 실제 provider와 자동 LLM judge를 MVP proof의 authority로 사용하지 않는다.

## Boundaries

- **In Scope:** `review_ai` contracts, context projection, utility evaluation models/runner/store, deterministic tests, controlled representative proof fixture와 관련 문서.
- **Out of Scope:** incident detection, `RemediationDraft` 또는 recovery authority 변경, automatic recovery, LLM-as-a-judge, 외부 evaluation platform, live provider 운영 자동화.

## Capabilities

기존 `reliability-agentic-review` capability의 review input/output와 provenance 계약을 확장한다. 새 capability는 만들지 않는다.

## Impact

| Surface | Impact |
| --- | --- |
| **Code / Systems** | `review_ai`가 bounded context projection과 utility evaluation/comparison을 소유한다. 기존 `reliability` deterministic contract와 `runtime_ai` provider mechanics는 변경하지 않는다. |
| **Data / Contracts** | context provenance/gap, utility contribution, rubric score, control result, comparison decision의 frozen Pydantic contract를 추가한다. |
| **Interfaces / APIs** | 기존 review prompt가 bounded context를 사용하고, 별도 local evaluator가 human-scored output을 비교 evidence로 만든다. |
| **Evidence** | representative case와 `rubric_v1` control validation, baseline/candidate comparison을 JSON/Markdown으로 재구성할 수 있게 한다. |
| **Safety** | utility output은 advisory evidence일 뿐 approval, proposal, recovery 또는 mutation authority가 아니다. |
