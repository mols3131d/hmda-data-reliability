# Directive

이 문서는 `pivot-clarify-runtime`의 인간 주도 규범적 기준선이다. 사용자의 명시적 요청 없이 수정하지 않는다. 실행 절차보다 목적, 요구사항과 설계 결정을 소유한다.

## Purpose

기능과 domain behavior를 불필요하게 변경하지 않으면서 runtime 이해 부채를 줄인다.

실행 후 중요한 경로, 결정, 상태 변화 또는 실패 원인을 복원하기 어려운 지점을 찾아 **가장 작은 유효한 runtime evidence로 답할 수 있게 만든다.**

logging 자체를 늘리거나 포괄적인 observability 체계를 구축하는 것은 목적이 아니다.

## Requirements

| ID | Requirement |
| --- | --- |
| R-01 | runtime evidence를 개선하되 domain behavior와 caller-visible contract를 불필요하게 변경하지 않아야 한다. |
| R-02 | 실행 후 답하기 어려우며 오해 비용이 가장 큰 복원 질문 하나를 우선해야 한다. |
| R-03 | 관찰 공백을 해소할 가장 작은 evidence를 선택하고 기존 surface를 우선 재사용해야 한다. |
| R-04 | evidence는 그 사실이나 결정을 가장 잘 아는 책임 경계가 소유해야 한다. |
| R-05 | 같은 의미를 여러 result, exception, artifact, metadata 또는 log에 불필요하게 중복하지 않아야 한다. |
| R-06 | secret, 민감 정보, 불필요한 raw payload 또는 대용량 데이터를 runtime evidence로 남기지 않아야 한다. |
| R-07 | debugging, correctness review, testing, monitoring, performance 또는 architecture가 주된 문제라면 해당 책임으로 분리해야 한다. |
| R-08 | 선택한 복원 질문에 충분히 답할 수 있으면 추가 instrumentation을 위해 scope를 확대하지 않고 중단해야 한다. |

## Decisions

| Decision | Rationale |
| --- | --- |
| runtime clarification을 logging과 동일시하지 않는다. | 문제는 특정 도구의 부재가 아니라 실행을 복원할 evidence가 부족한 데 있기 때문이다. |
| 하나의 복원 질문을 작업 단위로 삼는다. | instrumentation 범위를 질문과 직접 연결해 과잉 관찰을 막기 쉽다. |
| 기존 evidence surface를 먼저 보강한다. | 새 logging, tracing 또는 metadata 체계 자체가 추가 이해 부채가 될 수 있다. |
| evidence를 책임 경계 가까이에 둔다. | 의미의 소유 위치가 분산되면 해석·중복·변경 비용이 증가한다. |
| 질문이 해소되면 중단한다. | 더 많은 evidence가 항상 더 나은 이해를 만들지는 않으며 noise와 관리 부채를 만든다. |
