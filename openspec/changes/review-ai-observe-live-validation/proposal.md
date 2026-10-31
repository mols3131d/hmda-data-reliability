---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Observe Live Review Validation
description: 실제 provider 검증을 evaluation 모듈로 옮기고 단계 상태와 대기 시간을 안전하게 표시합니다.
---

## Why

실제 provider로 합성 사례를 실행하면 현재 CLI는 호출이 끝날 때까지 단계 상태와 대기 시간을 보여 주지 않는다. 사용자는 진행 중인지 판단하기 어렵고 실제 출력 검증의 진입점도 평가 모듈 밖에 있다. 현재 한국어 단계 실행의 결과와 provenance를 유지하면서 통합 검증의 위치와 진행 표시를 명확히 한다.

## What Changes

- 실제 provider 검증의 유일한 실행 진입점을 `python -m hmda_reliability.review_ai.evaluation.live`로 이동하고 기존 script와 wrapper를 제거한다.
- 표준 오류에 한국어 단계 시작·완료·실패와 경과 시간을 표시한다.
- 동기 provider 호출을 기다리는 동안 기본 5초 간격으로 로컬 대기 시간을 표시하고 종료 시 관찰 자원을 정리한다.
- 표준 출력의 최종 JSON·종료 의미·명시적 live 활성화·시간 예산·원문 보존·provenance 검증은 유지한다.

## Boundaries

- **In Scope:** Live 평가 진입점·stage 관찰 사건·안전한 표준 오류 표시·대기 heartbeat·실행 안내와 관련 회귀.
- **Out of Scope:** 모델 내부 진행률·토큰 streaming·추론 강제 취소·새 provider·retry 정책 변경·실제 모델 자동 pytest·다중 사례 자동 실행기·자동 품질 채점·사람 평가 대체·기존 script 호환 wrapper.
- 진행 표시는 로컬 관찰이며 실제 모델의 진척도나 출력 품질을 증명하지 않는다.

## Capabilities

### Modified Capabilities

#### `reliability-agentic-review`

- 명시적으로 활성화한 실제 provider 검증의 모듈 진입점과 부작용 없는 단계·대기 관찰을 정의한다.

## Impact

- Live 실행의 CLI 경로와 개발·평가 안내를 갱신한다.
- 일반 Review API에는 선택적 관찰 경계를 추가하되 기본 호출은 표준 오류 출력이나 heartbeat를 만들지 않는다.
