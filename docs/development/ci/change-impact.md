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

변경된 소스, 테스트, 설정과 계약에서 필요한 검증을 선택하는 책임을 정의한다. 위험에 비례해 검증을 좁히거나 넓히는 일반 패턴은 [Continuous Integration](README.md#change-impact), 병합 대상 상태는 [Admission Boundary](admission.md)를 따른다.

## Selection and Failure

- 변경된 소스, 테스트, 설정과 계약의 영향 범위를 우선 검증한다.
- 공용 영역처럼 영향이 넓은 변경은 검증 범위도 넓힌다.
- 영향 범위를 안전하게 좁힐 수 있으면 전체 검증보다 우선한다.
- 영향 범위를 결정할 수 없으면 검증을 넓히거나 selector를 실패시킨다. 불완전한 검증을 정상 결과로 처리하지 않는다.
- 중요한 검증이 path 분류 때문에 조용히 빠지지 않게 한다.
- Step 분기와 반복되는 변경 파일 수집은 독립 script로 검증하며, CI script 자체의 변경도 대응 contract test를 선택한다.

다음 사례는 위 규칙의 적용을 보여준다. 정확한 경로별 target이나 실행 명령을 대신하지 않는다.

| Change | Expected Result |
| --- | --- |
| 영향이 해당 CI script에 한정된 변경 | 대응 contract test로 그 경계를 검증한다 |
| CI script와 source·dependency를 함께 변경 | CI 계약 검사만으로 다른 변경의 검증을 대체하지 않고 각각의 영향 범위를 고려한다 |
| 공용 영역 또는 영향 범위를 결정할 수 없는 변경 | 필요한 검증을 넓히거나 선택을 실패시키며, 모르는 범위를 조용히 제외하지 않는다 |

## Implementation Boundary

정확한 glob과 routing table은 [`classify_changes.sh`](../../../scripts/ci/classify_changes.sh)에 둔다. OpenSpec의 capability mapping과 연관 Change 탐색은 classifier가 불러오는 [`classify_openspec.sh`](../../../scripts/ci/classify_openspec.sh)에 모은다.

선택된 test의 실행과 복합 변경의 현재 보완 규칙은 [Testing Guide](../testing.md#pull-request-ci)와 [`pytest.sh`](../../../scripts/ci/pytest.sh)에서 확인한다. 선택·실행의 회귀 검증은 [CI 계약 테스트](../../../tests/scripts/ci/)에서 확인하되, 선택값이나 호출 계약의 검증만으로 실제 domain runtime까지 통과했다고 주장하지 않는다.
