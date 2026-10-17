---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Positive Degradation Detection Boundaries
description: 유효한 zero threshold에서 무변화를 감소·결측 증가로 탐지하지 않도록 하고 양수 경계와 독립 규칙의 의미를 보존합니다.
---

## Why

현재 volume/null threshold에 `0`을 입력하면 같은 행 수와 null rate도 감소·증가 incident로 보고한다. 공개 입력 호환성을 유지하면서 실제 악화가 있어야 한다는 의미와 양수 threshold equality를 함께 명확히 해야 한다.

## What Changes

- Volume/null은 실제 양의 악화가 있고 악화량이 설정 기준 이상일 때 탐지한다. `0`은 어떤 양의 악화도 탐지하는 유효한 설정으로 유지한다.
- Normal comparison 문구를 규칙별 조건과 일치시킨다. Freshness의 절대 age 경계와 schema 비교는 유지한다.

## Boundaries

- **In Scope:** Reliability의 volume/null 경계, 독립 규칙 보존과 결정론적 회귀 검증.
- **Out of Scope:** null-rate 누락 baseline의 새 정책, 절대 품질 기능, 컬럼별 정책 엔진, float 허용 오차, 실제 AI 리뷰 품질·유용성 평가와 live 실험.

## Capabilities

### Modified Capabilities

#### `reliability-incident-detection`

- Zero threshold에서도 감소·증가의 실제 양수 조건을 요구하고, 기존 양수 threshold equality와 독립 freshness/schema 규칙을 보존한다.

## Impact

- 기존 valid threshold 설정과 공개 API 형태는 유지된다. `0`을 명시한 caller의 무변화 경보만 제거된다.
- Quality gate의 고정 baseline과 양수 threshold 및 blocking 정책은 유지된다.
