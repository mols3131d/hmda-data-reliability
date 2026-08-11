# Evidence

runtime evidence는 목적이 아니라 **복원 질문에 답하기 위한 surface**다. 새 체계를 만들기보다 가장 적합한 기존 owner를 보강하거나 정리한다.

## Choose The Owner

| Surface | Prefer when |
| --- | --- |
| Result / return | caller가 완료 결과나 상태를 사용해야 한다 |
| Exception context | 실패 대상, 단계, 원인을 caller가 진단해야 한다 |
| Artifact / framework metadata | 실행 결과가 durable record로 남아야 하거나 framework가 그 사실을 소유한다 |
| Logging | 시간적 흐름, 내부 결정 또는 경계 통과를 실행 중 복원해야 한다 |
| Correlation field | 서로 분리된 evidence를 같은 실행으로 연결해야 한다 |

## Choose The Intervention

새 evidence 추가만 해법으로 보지 않는다.

| Debt form | Prefer |
| --- | --- |
| Missing | 기존 owner에 필요한 context만 보강한다. |
| Duplicate | owning surface 하나를 남기고 의미 없는 복제를 제거하거나 병합한다. |
| Misowned | contract를 깨지 않는 범위에서 owning boundary로 옮기거나 상위 layer에는 필요한 의미만 projection한다. |
| Noisy | 질문에 답하지 않는 event/field를 제거·병합하고 반복성을 줄인다. |
| Disconnected | 기존 stable identifier를 재사용하고, 그것으로 부족할 때만 correlation field를 추가한다. |

기존 consumer가 의존하는 result, event, field가 명시적 contract라면 clarification만으로 제거하거나 이동하지 않는다.

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

## Common Decisions

| Situation | Preferred decision |
| --- | --- |
| result가 필요한 상태 전이와 최종 action을 이미 충분히 노출한다 | 추가 log 없이 result를 owner로 유지한다. |
| 같은 failure를 하위·중간·상위 layer가 모두 기록한다 | failure를 소유하거나 처리하는 boundary를 남기고 반복 evidence를 제거한다. |
| Dagster asset이 durable 결과를 `MaterializeResult.metadata`에 남기고 같은 값을 completion log에도 반복한다 | durable result는 metadata가 소유하고, log는 별도 operator-visible 사건이 필요할 때만 남긴다. |
| dbt build 결과나 실패를 이해해야 한다 | [dbt Runtime Evidence](dbt-evidence.md)의 artifact-first 기준을 따른다. |

이 예시는 해법을 고정하지 않는다. 실제 reconstruction question과 기존 consumer contract가 우선한다.

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
