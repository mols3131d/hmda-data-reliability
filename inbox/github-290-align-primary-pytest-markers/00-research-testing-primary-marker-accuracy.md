---
type: research
title: "Pytest Primary Marker Accuracy"
description: "현재 pytest level marker가 실제 수집 및 선택 결과와 일치하는지 확인하고 수정 범위를 판단한다."
---

# Pytest Primary Marker Accuracy

> [!NOTE]
> `main`의 두 test module에서 module-level primary marker와 function-level primary marker가 중첩된다. pytest marker는 교체가 아니라 누적되므로, 서로 다른 level을 함께 선택할 수 있다. 현재 근거는 정적 코드 확인이며 repository-wide collection 검사와 수정 후 실행은 아직 수행하지 않았다.

## Question

`unit`, `component`, `integration`의 실제 pytest 선택이 테스트의 의도한 단일 primary level과 일치하는가?

## Scope

기준: `main` commit `35d099c748cbe08ae6a12ce60acd7574fe086719` (2026-11-19 확인). 분류 계약은 [Test Design](../../docs/development/test-design.md), [Testing Guide](../../docs/development/testing.md), [pytest markers](../../pyproject.toml)를 따른다.

## Findings

### Module and function markers overlap

- [`tests/reliability_ai/test_execution_service.py`](../../tests/reliability_ai/test_execution_service.py): module `pytestmark = pytest.mark.unit`와 `test_delegated_task_reports_real_backfill_and_domain_approval_block`의 `@pytest.mark.integration`이 중첩된다.
- [`tests/reliability_ai/test_investigation_agent.py`](../../tests/reliability_ai/test_investigation_agent.py): module `pytestmark = pytest.mark.integration`와 `test_native_sdk_records_sibling_generations_and_tool_history`의 `@pytest.mark.component`가 중첩된다.

이는 `pytest -m unit`과 `pytest -m integration` 등의 테스트 수집 결과를 왜곡할 수 있으나, 테스트 assertion의 정오나 기존 CI 실패를 입증하는 증거는 아니다.

### Classification policy is already explicit

`docs/development/test-design.md`와 `docs/development/testing.md`는 일반 테스트에 `unit` / `component` / `integration` 중 하나의 primary marker를 요구한다. `memory` / `stress`는 추가 resource marker이므로 중복으로 간주하지 않는다.

### Current evidence is static

확인한 두 사례 외의 전역 중복 여부와 pytest effective marker count는 별도 수집으로 확인해야 한다. 이 준비 단계에서 테스트 실행이나 코드 변경은 수행하지 않았다.

## Implications

- 변경 전 `pytest --collect-only` 기반으로 각 test item의 effective primary marker를 확인해 목록과 실제 범위를 확정한다.
- 각 테스트의 실제 I/O·component 경계를 기준으로 최소 수정하고 `-m unit`, `-m component`, `-m integration` 선택 결과를 재검증한다.
- 중복 억제를 위해 marker 계약이나 CI를 전면 개편하지 않는다. 지속적인 회귀 방지 검사가 필요하면 비용과 효용을 확인한 뒤 최소 범위로 추가한다.
