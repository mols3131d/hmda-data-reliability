---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Ground Review AI Output Explanations
description: 수치·근거 충실성을 비교할 v3 후보와 독립적인 품질 사례를 제공합니다.
---

## Why

PR #278의 accepted 출력은 structured facts를 보존하면서도 증가율과 threshold를 잘못 설명하고 v2 예시를 복사했다. Schema 통과만으로 정확성이나 검토 가치를 판단할 수 없다.

## What Changes

- 기존 v1/v2를 보존하면서 수치 단위·제공된 evidence·실제 draft에 집중하는 선택 가능한 v3 후보를 제공한다.
- 독립 수치 oracle과 의미적 결함을 분리한 합성 control을 유지하고 현재 자동 검증의 탐지 경계를 명시한다.
- 같은 revision의 baseline/candidate 실행 및 실제 사람 평가로 채택을 판단할 수 있는 절차를 제공한다. v3 지원 자체는 개선·채택의 증거가 아니다.

## Boundaries

- **In Scope:** Review AI prompt version, test-only 품질 사례, 평가 절차.
- **Out of Scope:** 기본 prompt 전환, 임의 prose blocking guard, 자동 judge, provider/runtime 변경, Thinking/context 설정 변경, Langfuse 활성화, approval/recovery 권한 변경.

## Capabilities

### Modified Capabilities

#### `reliability-agentic-review`

- v3 prompt identity와 수치·근거 충실성 instruction을 지원하며 v1/v2 replay를 유지한다.

## Impact

- `review_ai`의 prompt 계약·렌더링, 관련 offline tests와 평가 가이드에 한정한다. 기존 evaluation serialization, input projection과 runtime acceptance는 보존한다.
