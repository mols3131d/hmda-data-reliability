# Test Instructions

이 디렉터리의 테스트는 검증 코드이자 실행 가능한 개발 문서다.

테스트를 추가하거나 수정할 때는 요구사항, 테스트 의도, 실제 테스트 코드가 서로 일치하도록 유지한다.

## Scope

이 지침은 `tests/`와 모든 하위 디렉터리에 적용한다.

하위 디렉터리에 더 구체적인 `AGENTS.md`가 있으면 해당 범위에서는 하위 지침을 우선한다.

## Test Ownership

테스트 작업에서는 다음 파일을 수정할 수 있다.

- `test_*.py`
- `conftest.py`
- 테스트 전용 fixture, helper, sample data
- 대응하는 `test_*.design.md`

production code, OpenSpec artifact, application configuration은 수정하지 않는다.

테스트 과정에서 production defect나 specification gap을 발견하면 테스트를 왜곡하지 말고 근거와 함께 상위 agent에게 보고한다.

## Documentation Strategy

### Default: Docstrings

대부분의 테스트 설계는 테스트 파일 안에서 관리한다.

Module docstring에는 필요한 범위에서 다음을 기록한다.

- 테스트 대상과 목적
- 보호하는 contract
- 주요 risk
- test level과 boundary
- 의도적으로 제외한 범위

```python
"""Tests for incident profile comparison.

Contract:
    - Detect material row-count decreases.
    - Preserve measured values in incident evidence.

Scope:
    Unit-level comparison rules only.
"""
```

개별 test docstring은 테스트 이름만으로 드러나지 않는 의도, 경계값 의미, regression 배경이 있을 때만 사용한다.

```python
def test_ignores_change_at_exact_threshold() -> None:
    """The configured threshold is exclusive."""
```

코드를 그대로 다시 설명하는 docstring은 작성하지 않는다.

### Complex Cases: Design Documents

Docstring만으로 테스트 의도와 구조를 명확히 유지하기 어려운 경우에만 별도 design 문서를 만든다.

```text
test_incident_lifecycle.py
test_incident_lifecycle.design.md
```

다음과 같은 경우 design 문서를 고려한다.

- 여러 contract와 component를 함께 검증한다.
- 상태 전이, retry, rollback 또는 분기가 복잡하다.
- 시나리오 매트릭스가 필요하다.
- 데이터 흐름이나 orchestration 설명이 필요하다.
- Mermaid나 표가 이해에 실질적으로 도움이 된다.
- 제외 범위, 운영 위험 또는 regression 배경이 길다.

단순 테스트에는 design 문서를 만들지 않는다.

## Design Document Contract

`test_<subject>.design.md`는 대응하는 `test_<subject>.py`와 같은 디렉터리에 둔다.

Design 문서는 필요에 따라 다음 내용을 포함한다.

- Purpose
- Contracts
- System boundary
- Risks
- Scenario matrix
- Test levels
- Exclusions
- 대응 test cases

각 scenario는 가능한 한 실제 test function과 연결한다.

```markdown
| Scenario | Test |
| --- | --- |
| 여러 incident를 독립적으로 보존 | `test_preserves_multiple_incidents` |
| threshold와 동일한 값은 무시 | `test_ignores_change_at_exact_threshold` |
```

실행 결과나 일시적인 pass count는 design 문서에 기록하지 않는다.

## Synchronization

대응하는 `.design.md`가 존재하면 `.py`와 하나의 변경 단위로 취급한다.

다음 변경에서는 두 파일을 함께 검토한다.

- test case 추가 또는 삭제
- contract 또는 expected behavior 변경
- fixture와 system boundary 변경
- test level 또는 marker 변경
- 파일 이름 변경 또는 이동
- 제외 범위 변경

문서와 코드가 충돌하면 실제 요구사항과 관찰된 behavior를 기준으로 둘 다 수정한다. 문서를 그대로 두고 코드만 맞추거나, 테스트를 문서에 억지로 맞추지 않는다.

## Test Design

각 테스트는 다음 관계를 표현해야 한다.

```text
requirement → scenario → setup → action → observable result
```

- 외부에서 관찰 가능한 behavior를 우선한다.
- 구현 세부사항에 불필요하게 결합하지 않는다.
- 하나의 테스트는 하나의 논리적 behavior에 집중한다.
- 실패한 테스트 이름만으로 깨진 contract를 파악할 수 있어야 한다.
- 경계, 오류 경로, 회귀 위험을 happy path와 함께 고려한다.

## Test Implementation

- 기존 fixture, helper, marker convention을 우선 재사용한다.
- shared mutable state와 test order dependency를 피한다.
- 시간, network, 실제 외부 service에 의존하는 flaky test를 만들지 않는다.
- mock은 system boundary를 통제하는 데 필요한 만큼만 사용한다.
- parameterization이 의미 있는 중복을 줄일 때 사용한다.
- 넓은 입력 공간의 invariant 검증에 가치가 있을 때만 Hypothesis를 사용한다.
- assertion 약화, broad exception swallowing, 무조건적인 skip으로 실패를 숨기지 않는다.

## Test Levels

repository에 정의된 marker를 사용한다.

| Marker | Responsibility |
| ------------- | --------------------------------------- |
| `unit` | pure function과 isolated domain behavior |
| `component` | package-level behavior와 local boundary |
| `integration` | 여러 subsystem을 가로지르는 workflow |
| `memory` | representative memory-budget validation |
| `stress` | worst-case resource behavior |

가장 낮은 비용으로 contract를 신뢰성 있게 검증할 수 있는 level을 선택한다.

## Validation

변경한 테스트와 가장 가까운 focused target부터 실행한다.

1. 변경한 test function 또는 module
1. 관련 package test suite
1. 영향 범위에 필요한 상위 suite

실행하지 않은 테스트를 통과했다고 기록하지 않는다.

실패는 다음과 같이 구분한다.

| Failure | Action |
| ------------------- | -------------------------- |
| Test defect | `tests/`에서 수정하고 재실행 |
| Production defect | 재현 조건과 observed result 보고 |
| Specification gap | 정의되지 않은 behavior 보고 |
| Environment failure | 누락된 dependency나 service 보고 |
| Unrelated failure | 현재 변경과 분리하여 보고 |

## Completion

테스트 작업은 다음 조건을 만족해야 한다.

- 테스트 의도와 requirement가 연결되어 있다.
- module docstring이 현재 테스트 범위를 반영한다.
- 필요한 경우 `.design.md`와 test code가 일치한다.
- focused test가 실제로 실행되었다.
- 실패, 미실행 영역, remaining risk가 숨겨지지 않았다.
- production defect를 테스트 수정으로 우회하지 않았다.
