---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: "Limit Review Validation to Structured Facts"
description: "Review AI deterministic validation을 structured input과 직접 비교 가능한 facts에 한정하고 free-text advisory semantics를 blocking policy에서 제거합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
---

## Why

현재 Review AI validator는 Evidence·incident identity·canonical facts의 deterministic consistency와 free-text command·authority 의미를 추정하는 자연어 regex guard를 함께 소유한다. 자연어 guard는 punctuation과 표현 조합에 따라 false positive와 false negative를 만들지만, 통과한 review text가 실제 approval 또는 mutation authority를 획득하는 execution boundary는 아니다. Deterministic validation의 authoritative 범위를 구조적으로 검증 가능한 facts로 명확히 제한해야 한다.

## What Changes

- Deterministic validator는 output이 제공된 Evidence만 참조하는지, incident identity가 같은지, canonical target과 numeric facts가 deterministic input과 같은지만 authoritative하게 검증한다.
- Free-text advisory wording은 deterministic acceptance를 차단하지 않으며 active validation은 `authority_escalation`, `forbidden_action` violation과 `forbidden-action-policy-v1` identity를 생성하지 않는다.
- Validation provenance는 structured-fact semantics를 식별하는 새 policy identity를 사용하고, 기존 `forbidden-action-policy-v1` record는 historical evidence로 계속 읽을 수 있게 한다.
- Typed result, accepted-result provenance requirement, immutable invocation evidence와 deterministic violation ordering·uniqueness는 유지한다.
- Accepted review text는 wording과 무관하게 advisory output으로만 반환되며 `Approval`, `RecoveryProposal` 또는 mutation request로 변환되지 않는다.
- Offline evaluation은 regex phrase corpus 대신 structured contradiction, untrusted prompt-injection-like data, side-effect absence와 provenance consistency를 검증한다.

## Boundaries

- **In Scope:** `reliability-agentic-review` validation behavior, obsolete violation/policy contract, invocation evidence compatibility, validator/service tests와 직접 관련된 Review AI documentation
- **Out of Scope:** prompt policy 변경, 자연어 classifier 또는 LLM judge 추가, 별도 evaluation subsystem 신설, `review_ai`/`runtime_ai` ownership 재설계, approval/recovery contract 변경, mutation capability 확대

## Capabilities

### Modified Capabilities

#### `reliability-agentic-review`

- Deterministic output validation을 structured evidence reference, incident identity와 canonical facts consistency에 한정한다.
- Free-text advisory semantics를 blocking acceptance policy에서 제거하되 review output의 advisory-only/read-only boundary와 typed provenance contract를 유지한다.
- Deterministic evaluation contract를 structured validation과 authority separation을 직접 검증하는 scenario로 정렬한다.

## Impact

- `src/hmda_reliability/review_ai/validator.py`, `contracts.py`, review invocation evidence와 관련 tests에서 active natural-language policy surface가 제거되고 historical record compatibility가 명시된다.
- `openspec/changes/reliability-agentic-review/`가 정의한 validation 및 evaluation behavior를 명시적으로 변경하는 후속 delta Spec이 필요하다.
- `review-ai-extract-runtime`이 만든 ownership과 dependency boundary는 prerequisite로 유지되며 이 Change에서 다시 설계하지 않는다.
