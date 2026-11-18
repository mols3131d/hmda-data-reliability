---
type: brief
title: "Primary Marker Implementation Handoff"
description: "PR #290에서 마커 수집 정확성을 수정할 로컬 에이전트의 현재 상태와 검증 지점을 전달한다."
---

# Primary Marker Implementation Handoff

> [!IMPORTANT]
> **PR #290은 Draft이며 아직 marker 수정 및 테스트 검증 전이다.** 목표는 문서 완료가 아니라 단일 primary marker 정합성의 구현·검증이다. `main`을 직접 변경하거나 임의로 merge하지 않는다.

## Continuation

- Owning PR: [#290](https://github.com/mols3131d/hmda-data-reliability/pull/290)
- Owning branch: `agent/test/align-primary-pytest-markers`
- Initial base: `main@35d099c748cbe08ae6a12ce60acd7574fe086719` (후속 작업 시 live base/head 재확인).
- Starting evidence: [Research](00-research-testing-primary-marker-accuracy.md). Work / acceptance: [Plan](01-plan-testing-primary-marker-selection.md).
- Confirmed static examples: `tests/reliability_ai/test_execution_service.py`의 `unit + integration`, `tests/reliability_ai/test_investigation_agent.py`의 `integration + component`.

## Next Action

1. 현재 head, 원격 `main`, 사용자/로컬 harness와 적용되는 repo context를 확인하고 기존 변경을 보호한다.
2. 실제 pytest collection에서 primary marker 충돌을 재현하고 각 test의 true boundary를 확인한다.
3. 최소 coherent code/test 변경을 수행하고 선택 정확성, 테스트 동작 보존, CI를 검증한다.
4. 수행한 검증/미수행 항목 및 주요 판단을 PR 본문에 반영하고 review를 요청한다. **Ready 전환과 merge는 별도 인간 결정**이다.

## Safeguards

- 사용자가 지정한 계정 `mols3131d` / `mols3131d@gmail.com`만 사용한다.
- 마커 이름을 바꾸기 전에 실제 테스트가 보호하는 동작을 확인한다. 리뷰 의견도 무조건 수용하지 않고 로컬 실행·근거로 재검토한다.
- Scope는 pytest marker 정확성이다. 다른 테스트 구조 문제, LLM 평가, framework 도입을 결합하지 않는다.
- 이번 준비 단계에서 테스트 실행 없음. 이전 PR의 PASS 기록은 현재 PR에 대한 검증이 아니다.
