---
title: "CI Change Impact"
description: "변경에 필요한 검증을 선택하거나 영향이 불확실한 경로와 CI 자체 변경을 처리할 때 사용하는 검증 선택 계약입니다."
categories:
  - software-engineering
tags:
  - ci
  - testing
---

# CI Change Impact

소스, 테스트, 설정과 계약의 변경에 필요한 검증을 선택하는 기준이다. 위험에 비례한 검증 패턴은 [Continuous Integration](README.md#change-impact), 병합 대상 상태는 [Admission Boundary](admission.md)를 따른다.

## Selection and Failure

- 소스, 테스트, 설정과 계약의 변경 영향부터 검증한다.
- 공용 영역 등 영향이 넓은 변경은 검증도 넓힌다.
- 안전하게 범위를 좁힐 수 있으면 전체 검증보다 우선한다.
- **영향이 불명확하면 검증을 넓히거나 검증 선택기(selector)를 실패시킨다.** 불완전한 검증을 성공으로 처리하지 않는다.
- 경로 분류 때문에 중요한 검증이 조용히 누락되지 않게 한다.
- Step 분기와 반복되는 변경 파일 수집은 독립 script로 검증한다. CI script를 바꾸면 대응 contract test도 선택한다.

아래는 적용 예시이며 정확한 경로별 target과 실행 명령을 대신하지 않는다.

| Change | Expected Result |
| --- | --- |
| 영향이 해당 CI script에 한정 | 대응 contract test로 검증한다. |
| CI script와 소스 또는 의존성을 함께 변경 | CI 계약 검사로 다른 변경의 검증을 대체하지 않고 각 영향을 검증한다. |
| 공용 영역 또는 영향 불명확 | 검증을 넓히거나 선택을 실패시킨다. 모르는 범위를 제외하지 않는다. |

## Implementation Boundary

| Source | Responsibility |
| --- | --- |
| [`classify_changes.py`](../../../scripts/ci/classify_changes.py) | 정확한 glob과 routing table |
| [`classify_openspec.py`](../../../scripts/ci/classify_openspec.py) | Classifier가 호출하는 OpenSpec capability mapping과 연관 Change 탐색 |
| [Testing Guide](../testing.md#pull-request-ci), [`run_checks.py`](../../../scripts/ci/run_checks.py) | 선택된 검사의 실행과 복합 변경의 현재 보완 규칙 |
| [CI 계약 테스트](../../../tests/scripts/ci/) | 검증 선택과 실행의 회귀 검증 |

선택값이나 호출 계약을 검증했다고 해서 실제 domain runtime까지 통과했다고 주장하지 않는다.
