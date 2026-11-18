---
type: plan
title: "Primary Marker Selection Remediation Plan"
description: "pytest 수집 마커의 중복을 정리하고 실행 선택·회귀 검증까지 완료하기 위한 작업 계획이다."
---

# Primary Marker Selection Remediation Plan

## Goal

모든 in-scope pytest test item이 `unit` / `component` / `integration` 중 의도한 primary marker **하나만** 가지며, 각 `-m` 선택이 그 분류와 일치하도록 수정한다. 이 PR의 완료 목표는 **실제 마커 정합성 수정 + 검증**이다. 문서 작성만으로 완료 처리하지 않는다.

## Work

1. `main` 대비 변경을 확인하고 `pytest --collect-only`로 실제 item의 effective marker를 점검한다. `item.iter_markers()`에서 세 primary marker의 unique name set 및 필요 시 중복 발생 위치를 기록한다. `pytest -m` 필터의 실제 선택 결과도 확인한다.
2. 조사에서 확인된 두 사례를 우선 검토한다.
   - `tests/reliability_ai/test_execution_service.py`: module `unit` + `test_delegated_task_reports_real_backfill_and_domain_approval_block`의 `integration`.
   - `tests/reliability_ai/test_investigation_agent.py`: module `integration` + `test_native_sdk_records_sibling_generations_and_tool_history`의 `component`.
3. **이름만 따라 수정하지 않는다.** 각 테스트가 실제 관찰하는 I/O와 component 경계로 primary level을 재판단한다. Module 전체 marker를 유지하면 예외 test를 성격이 맞는 기존/신규 module로 이동하거나 class 단위 그룹화하는 식으로 상속 충돌을 제거한다. Fixture나 helper의 이동이 과도하면 가장 작은 대안을 선택한다.
4. 다른 중복 사례가 수집 결과로 확인되면 같은 목적과 위험 범위 안에서 함께 정리한다. 불분명한 테스트는 계약과 책임 경계를 확인한 뒤 결정한다.
5. 필요할 때만 lightweight collection regression guard를 추가한다. 기존 fixture, production source, CI 설정을 광범위하게 재설계하지 않는다.

## Acceptance

- collection 결과 일반 test item마다 effective primary **name set**이 정확히 하나다. Resource marker `memory` / `stress`는 추가될 수 있다.
- `-m unit`, `-m component`, `-m integration`의 각 선택 범위가 상호 중복 없이 의도한 수준을 반영한다. 실제 물리적 marker 객체 개수와 unique name 차이도 확인하여 우연히 통과하지 않도록 한다.
- 변경된 테스트의 observable behavior assertion과 oracle은 약화되지 않는다. Test relocation 후 fixture, test ID, collection, marker 선택이 정상이다.
- Focused tests → 해당 domain suites → 영향에 비례한 non-resource suite를 실행하고 결과를 evidence로 남긴다. CI Lite의 최신 prospective merge 결과를 확인한다.
- 변경된 코드와 인박스의 최종 상태, 미해결 gap을 PR 본문과 인계 문서에 일치시킨다.

## Boundaries

- production 코드를 변경하지 않는다. 테스트 이관에 필요하지 않은 marker 정책 변경은 하지 않는다.
- `pytestmark`와 function decorator 중첩은 function marker가 module marker를 override한다는 가정으로 해결하지 않는다.
- Skip, xfail, mock, assertion 변경으로 수집 문제를 가리지 않는다.
- 본 계획의 static finding을 실행 검증 PASS라고 보고하지 않는다.

## Verification

```bash
uv run pytest --collect-only -q tests/reliability_ai
uv run pytest --collect-only -q -m unit tests/reliability_ai
uv run pytest --collect-only -q -m component tests/reliability_ai
uv run pytest --collect-only -q -m integration tests/reliability_ai
uv run pytest tests/reliability_ai
```

위 명령은 선택 결과 파악용 시작점이다. 전체 분류 무결성 검사에서는 기본 `not memory and not stress` 필터가 resource test를 제외한다는 점을 고려해 명시적으로 pytest option을 조정한다. 실제 수행한 결과만 기록한다.

## References

- [Research](00-research-testing-primary-marker-accuracy.md)
- [Test Design](../../docs/development/test-design.md)
- [Testing Guide](../../docs/development/testing.md)
