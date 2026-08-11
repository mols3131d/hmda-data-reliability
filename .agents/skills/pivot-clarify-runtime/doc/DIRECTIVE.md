# Directive

이 문서는 `pivot-clarify-runtime`의 인간 주도 규범적 기준선이다. 사용자의 명시적 요청 없이 수정하지 않는다. 실행 절차보다 목적, 요구사항과 설계 결정을 소유한다.

## Purpose

기능과 domain behavior를 불필요하게 변경하지 않으면서 runtime 이해 부채를 줄인다.

실행 결과와 남겨진 evidence만으로 중요한 실행 경로, 결정, 상태 전이와 실패 원인을 복원하기 어려운 지점을 찾아 가장 작은 유효한 관찰 수단으로 해소한다.

logging 자체를 늘리거나 포괄적인 observability 체계를 구축하는 것은 목적이 아니다.

## Requirements

| ID | Requirement |
| --- | --- |
| R-01 | runtime 이해를 위해 domain behavior나 public contract를 불필요하게 변경하지 않아야 한다. |
| R-02 | 복원하기 어려울 때 오해 비용이 가장 큰 runtime blind spot 하나를 우선해야 한다. |
| R-03 | blind spot을 해소할 가장 작은 runtime evidence를 선택해야 한다. |
| R-04 | result, metadata, exception context, logging 등 기존 surface로 충분하면 새로운 관찰 체계를 만들지 않아야 한다. |
| R-05 | 중요한 실행 경로, 결정, 상태 전이 또는 실패 원인 중 해당 병목에 필요한 정보만 복원 가능하게 해야 한다. |
| R-06 | 같은 의미를 여러 surface에 중복 기록하지 않고 evidence의 소유 위치를 명확하게 해야 한다. |
| R-07 | secret, 민감 정보, 불필요한 raw payload 또는 대용량 데이터를 runtime evidence로 남기지 않아야 한다. |
| R-08 | debugging, correctness review, testing, monitoring 또는 architecture redesign이 주된 문제라면 해당 책임으로 분리해야 한다. |
| R-09 | 선택한 runtime blind spot이 해소되면 추가 instrumentation을 위해 scope를 확대하지 않고 중단해야 한다. |

## Decisions

| Decision | Rationale |
| --- | --- |
| runtime clarification을 logging과 동일시하지 않는다. | 문제는 특정 도구의 부재가 아니라 실행을 복원할 evidence가 부족한 데 있기 때문이다. |
| 하나의 가장 중요한 runtime blind spot을 우선한다. | 광범위한 instrumentation은 신호 대비 noise와 유지보수 비용을 빠르게 늘린다. |
| 기존 runtime surface를 우선 재사용한다. | 새로운 logging, tracing 또는 metadata 체계 자체가 추가적인 이해 부채가 될 수 있다. |
| evidence는 결정과 상태 변화가 발생하는 책임 경계 가까이에 둔다. | runtime 의미의 소유 위치가 분산되면 해석과 변경 비용이 증가한다. |
| runtime evidence와 domain contract를 구분한다. | 관찰 수단이 요구사항이나 business contract의 대체 근거가 되는 것을 방지한다. |
| comprehensive observability는 기본 범위에서 제외한다. | 이 스킬의 목적은 운영 플랫폼 구축이 아니라 이해 병목의 최소 해소다. |
| blind spot이 해소되면 중단한다. | 더 많은 evidence가 항상 더 나은 이해를 만들지는 않으며 noise와 관리 부채를 만들 수 있다. |
