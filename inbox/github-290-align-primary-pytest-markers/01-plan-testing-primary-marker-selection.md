---
type: plan
title: "Primary Marker Selection Remediation Plan"
description: "pytest 수집 마커의 중복을 정리하고 실행 선택·회귀 검증까지 완료하기 위한 작업 계획이다."
---

# Primary Marker Selection Remediation Plan

## Goal

기존 pytest test의 실제 검증 경계에 맞춰 `unit` / `component` / `integration` 중 **정확한 하나의 primary level**로 선택되도록 수정한다. `memory` / `stress`는 별도 resource marker로 보존한다. 현재 확인된 두 중복 사례부터 시작하며, 추가 사례는 실제 collection 근거로만 범위에 포함한다. 이 PR의 완료 목표는 **실제 마커 정합성 수정 + 검증**이다. 문서 작성만으로 완료 처리하지 않는다.

## Work

1. `main` 대비 변경을 확인하고 `pytest --collect-only`로 실제 item의 effective marker를 점검한다. `item.iter_markers()`에서 세 primary marker의 unique name set 및 필요 시 중복 발생 위치를 기록한다. `pytest -m` 필터의 실제 선택 결과도 확인한다.
1. 조사에서 확인된 두 사례를 우선 검토한다.
   - `tests/reliability_ai/test_execution_service.py`: module `unit` + `test_delegated_task_reports_real_backfill_and_domain_approval_block`의 `integration`.
   - `tests/reliability_ai/test_investigation_agent.py`: module `integration` + `test_native_sdk_records_sibling_generations_and_tool_history`의 `component`.
1. **이름만 따라 수정하지 않는다.** 각 테스트가 실제 관찰하는 I/O와 component 경계로 primary level을 재판단한다. module과 class marker는 function marker로 override되지 않고 누적된다. 따라서 class 분리만으로 module-level 중복을 해결했다고 간주하지 않는다. 예외 test를 적절한 module로 이동하거나 module-level marker를 제거하고 필요한 test에 개별 마커를 지정하는 대안을 비교하여 fixture·test ID·oracle 보존 비용이 가장 낮은 방식을 택한다.
1. 다른 중복 사례가 수집 결과로 확인되면 같은 목적과 위험 범위 안에서 함께 정리한다. 불분명한 테스트는 계약과 책임 경계를 확인한 뒤 결정한다.
1. 필요할 때만 lightweight collection regression guard를 추가한다. 기존 fixture, production source, CI 설정을 광범위하게 재설계하지 않는다.

## Acceptance

- 수정한 test의 effective primary **name set**이 정확히 하나이며, 전체 수집에서도 다른 primary 충돌이 없는지 확인한다. 이미 있던 무표식 test나 같은 이름의 중복 mark가 나오면 실제 의미와 이 PR의 범위를 판단해 별도 기록한다. Resource marker `memory` / `stress`는 보존한다.
- `-m unit`, `-m component`, `-m integration` 선택에서 수정 대상 item이 중복 선택되지 않으며, 예상한 level에 포함되는지 확인한다. `iter_markers()`가 반환하는 실제 mark와 unique name을 모두 관찰한다.
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
uv run pytest --collect-only -q -m 'unit and not memory and not stress' tests/reliability_ai
uv run pytest --collect-only -q -m 'component and not memory and not stress' tests/reliability_ai
uv run pytest --collect-only -q -m 'integration and not memory and not stress' tests/reliability_ai
uv run pytest tests/reliability_ai
```

위 명령은 선택 결과 확인용이며 아직 실행하지 않았다. 명시한 `-m`은 기본 addopts의 `-m 'not memory and not stress'`를 대체할 수 있으므로, 일반 테스트 선택에는 resource exclusion을 표현식에 함께 적는다. Resource test까지 포함한 collection audit는 `-o addopts='--timeout=60 --strict-markers'`와 임시 collection hook 등 읽기 전용 수집 방식으로 별도 확인한다. 실제 수행한 결과만 기록한다.

## References

- [Research](00-research-testing-primary-marker-accuracy.md)
- [Test Design](../../docs/development/test-design.md)
- [Testing Guide](../../docs/development/testing.md)
