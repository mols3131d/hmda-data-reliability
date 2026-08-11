# Directive

이 문서는 `pivot-clarify-runtime`의 인간 주도 규범적 기준선이다. 사용자의 명시적 요청 없이 수정하지 않는다. 실행 절차보다 목적, 요구사항과 설계 결정을 소유한다.

## Purpose

기능을 추가하거나 domain behavior를 변경하지 않고 runtime 이해 부채를 줄인다.

runtime 이해 부채는 실행 후 중요한 경로, 결정, 상태 변화 또는 실패 원인을 기존 evidence만으로 신뢰할 수 있게 복원하기 어려운 상태다. 문제는 evidence의 부족뿐 아니라 품질과 소유권에서도 생길 수 있다.

목표는 evidence의 양을 늘리는 것이 아니라 필요한 실행 의미를 적절한 책임 경계에서 최소하고 명확하게 보존하는 것이다.

특정 관찰 수단의 확대, 포괄적인 observability 구축 또는 다른 책임의 문제 해결은 목적이 아니다.

## Requirements

| ID | Requirement |
| --- | --- |
| R-01 | domain behavior와 기존 caller/consumer contract를 보존해야 한다. |
| R-02 | 오해 비용이 가장 큰 복원 문제 하나를 우선해야 한다. |
| R-03 | 복원 문제를 해소할 가장 작은 evidence 변경을 선택하고 기존 evidence를 새 관찰 수단보다 우선해야 한다. |
| R-04 | evidence의 의미는 그 사실이나 결정을 소유하는 책임 경계에 두고 같은 의미를 불필요하게 분산하거나 중복하지 않아야 한다. |
| R-05 | runtime evidence는 실행을 설명해야 하며 requirement, domain policy 또는 canonical contract를 대신 정의하지 않아야 한다. |
| R-06 | 민감 정보나 복원 문제에 필요하지 않은 데이터를 runtime evidence로 노출하지 않아야 한다. |
| R-07 | 주된 문제가 runtime 이해 부채가 아니라면 이 스킬의 범위를 확대하지 않고 해당 책임으로 분리해야 한다. |
| R-08 | 선택한 복원 문제가 해소되면 추가 관찰이나 정리를 위해 scope를 확대하지 않고 중단해야 한다. |

## Decisions

| Decision | Rationale |
| --- | --- |
| runtime clarification을 동작 보존 변경으로 제한한다. | 이해 개선과 domain behavior 변경을 분리해야 변경 이유와 검증 범위가 명확하게 유지되기 때문이다. |
| runtime clarification을 특정 관찰 수단과 동일시하지 않는다. | 핵심 문제는 도구의 부재가 아니라 실행 의미를 복원할 evidence의 품질과 소유권에 있기 때문이다. |
| 하나의 복원 문제를 작업 단위로 삼는다. | 변경 범위를 실제 이해 비용과 직접 연결해 과잉 관찰과 일반적인 정리 작업으로의 확장을 막기 위해서다. |
| 최소한의 기존 evidence를 우선한다. | 새로운 관찰 수단 자체가 추가 이해 부채를 만들 수 있기 때문이다. |
| evidence의 양보다 복원 가능성을 우선한다. | runtime 이해 부채는 evidence의 부족과 과잉 모두에서 생길 수 있기 때문이다. |
| evidence와 domain contract를 분리한다. | 실행 관찰이 요구사항이나 정책의 우회적인 정의가 되는 것을 방지하기 위해서다. |
| evidence 의미는 책임 경계 가까이에 둔다. | 의미의 소유 위치가 분산되면 해석, 중복과 변경 비용이 증가하기 때문이다. |
| 복원 문제가 해소되면 중단한다. | 더 많은 evidence나 정리가 항상 더 나은 runtime 이해를 만들지는 않기 때문이다. |
