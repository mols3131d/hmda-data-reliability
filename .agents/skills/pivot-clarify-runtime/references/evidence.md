# Evidence

runtime evidence는 목적이 아니라 **복원 질문에 답하기 위한 surface**다. 새 체계를 만들기보다 가장 적합한 기존 owner를 보강한다.

## Choose The Owner

| Surface | Prefer when |
| --- | --- |
| Result / return | caller가 완료 결과나 상태를 사용해야 한다 |
| Exception context | 실패 대상, 단계, 원인을 caller가 진단해야 한다 |
| Artifact / framework metadata | 실행 결과가 durable record로 남아야 하거나 framework가 그 사실을 소유한다 |
| Logging | 시간적 흐름, 내부 결정 또는 경계 통과를 실행 중 복원해야 한다 |
| Correlation field | 서로 분리된 evidence를 같은 실행으로 연결해야 한다 |

## Selection Rules

1. **누가 이 사실을 알아야 하는가?** caller, operator, maintainer 중 실제 독자를 정한다.
1. **기존 durable evidence가 있는가?** result, exception, artifact 또는 metadata로 충분하면 log를 추가하지 않는다.
1. **시간 순서가 필요한가?** 실행 중 사건의 순서나 선택을 복원해야 할 때 logging을 고려한다.
1. **연결이 필요한가?** 서로 다른 surface의 관계가 이미 명확하면 correlation field를 추가하지 않는다.

모든 runtime evidence를 하나의 공통 schema로 표준화하려 하지 않는다. 선택한 질문에 필요하지 않은 field는 추가하지 않는다.

## Ownership

같은 사실은 가능한 한 한 surface가 소유한다.

- caller-visible outcome → result
- failure-specific detail → exception context
- framework/tool execution fact → artifact 또는 framework metadata
- 다른 surface가 표현하지 못하는 temporal/decision context → log

상위 계층은 새로운 의미를 추가할 때만 하위 계층의 evidence를 projection한다. 단순 복제는 제거한다.

## Minimum Context

필요한 경우 다음 중 일부만 남긴다.

- operation 또는 execution boundary
- asset, table, partition, artifact 같은 안정적인 target identifier
- 중요한 outcome, action 또는 reason
- mutation/validation 전후를 구분하는 최소 상태
- 분리된 evidence를 연결하는 stable execution identifier

## Data Safety

남기지 않는다.

- credential, token, secret
- 불필요한 raw row, 전체 request/model dump 또는 payload
- 무제한 subprocess stdout/stderr
- 쉽게 변하는 대형 object representation

가능하면 identifier, count, bounded summary 또는 path처럼 작은 표현을 사용한다.

## Contract Boundary

runtime evidence는 현재 실행을 설명한다. requirement, domain policy 또는 business contract를 새로 정의하지 않는다.
