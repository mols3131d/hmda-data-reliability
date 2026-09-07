# Test Directory Context

`tests/`는 domain별 executable specification이다. 이 파일은 `tests/`를 수정하는 agent에게만 적용되는 최소 context를 제공한다.

## Write Boundary

수정 가능한 authored file은 다음으로 한정한다.

- `test_*.py`, `conftest.py`
- test 전용 fixture, helper, sample data
- 필요한 경우 대응하는 `test_*.design.md`

production source, OpenSpec artifact, project configuration, dependency와 CI는 수정하지 않는다. Production defect 또는 specification gap을 발견하면 test를 약화하지 말고 재현 조건과 observed result를 보고한다.

## Local Conventions

- observable contract를 소유하는 기존 test area, fixture, helper와 marker를 먼저 재사용한다. `src/` 구조를 기계적으로 mirror하지 않고, 새 test area는 기존 분류로 배치할 수 없을 때만 만든다.
- `scripts/`의 entrypoint, helper 또는 wrapper 자체를 직접 검증하는 test는 `tests/scripts/`에 둔다. Domain behavior를 검증하면서 script를 호출하는 test는 해당 domain test area에 둔다.
- module docstring은 contract, scope, 중요한 risk 또는 exclusion이 있을 때만 짧게 유지한다.
- function docstring은 test 이름으로 드러나지 않는 policy, boundary 또는 regression 맥락에만 쓴다.
- `test_*.design.md`는 여러 contract, 복잡한 flow 또는 scenario matrix가 있을 때만 만들고 대응 `.py`와 함께 갱신한다.
- 하나의 test는 하나의 observable behavior를 검증한다.
- shared mutable state, test order dependency, 실제 network service 의존을 만들지 않는다.
- mock은 external boundary를 통제하는 데만 사용하며 domain behavior를 숨기지 않는다.
- assertion을 약화하거나 broad exception, unconditional skip으로 false green을 만들지 않는다.

## Validation

변경한 test 또는 module부터 실행하고 필요한 경우 관련 package suite로 넓힌다. 실행 방법과 marker는 [`docs/development/testing.md`](../docs/development/testing.md)를, requirement-to-scenario와 oracle 설계는 [`docs/development/test-design.md`](../docs/development/test-design.md)를 따른다.

실행하지 않은 test를 통과로 기록하지 않는다. 실패는 test defect, production defect, specification gap, environment failure, unrelated failure로 구분한다.
