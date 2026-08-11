# Evidence

runtime evidence는 목적이 아니라 **실행을 복원하기 위한 surface**다. 같은 사실을 가장 적절한 owner 하나에 둔다.

## Surface Selection

| Surface | Prefer when | Avoid when |
| --- | --- | --- |
| Result / return | caller가 완료 결과나 상태를 사용해야 한다 | 내부 진행 과정만 설명하려 한다 |
| Exception context | 실패 대상·단계·원인을 caller가 진단해야 한다 | 정상 경로의 진행 상황을 기록하려 한다 |
| Framework metadata | Dagster 등 framework 실행 결과를 operator가 봐야 한다 | domain API contract를 대신하려 한다 |
| Logging | 시간적 흐름, 내부 결정 또는 경계 통과를 실행 중 복원해야 한다 | 이미 result/metadata/context로 충분하다 |
| Correlation field | 분리된 evidence를 같은 실행으로 연결해야 한다 | 단일 call 안에서 이미 관계가 명확하다 |

새 surface를 만들기 전에 기존 surface를 보강할 수 있는지 확인한다.

## Minimum Useful Evidence

선택한 관찰 공백에 직접 필요한 정보만 남긴다.

좋은 evidence는 보통 다음 중 일부만 필요하다.

- operation 또는 execution boundary
- 대상 asset/table/partition/artifact 등 안정적인 식별자
- 중요한 선택 결과와 필요한 경우 그 근거
- mutation 또는 validation의 전후 상태
- 성공·실패·skip 같은 결과
- 실패를 재구성하는 최소 causal context

모든 field를 표준화하려고 하지 않는다. 해당 질문에 답하지 않는 field는 추가하지 않는다.

## Ownership

같은 사실을 여러 surface에 복제하지 않는다.

- caller contract에 필요한 사실은 result가 소유한다.
- failure-specific detail은 exception context가 소유한다.
- framework execution fact는 framework metadata가 소유한다.
- log는 다른 surface가 소유하지 않는 시간적·결정적 맥락을 보완한다.

상위 계층이 하위 계층의 같은 사건을 다시 기록해야 한다면 새로운 의미를 추가하는지 확인한다. 단순 반복이면 제거한다.

## Data Safety

다음을 runtime evidence에 남기지 않는다.

- credential, token, secret
- 필요하지 않은 원본 row나 전체 payload
- 전체 subprocess stdout/stderr의 무제한 복제
- 민감하거나 규모가 큰 파일 내용

필요하면 식별자, count, bounded summary, path 등 더 작은 표현으로 대체한다.

## Contract Boundary

Runtime evidence는 현재 실행을 설명한다. requirement, domain policy 또는 business contract를 새로 정의하지 않는다. 넓은 규칙은 canonical owner가 소유한다.
