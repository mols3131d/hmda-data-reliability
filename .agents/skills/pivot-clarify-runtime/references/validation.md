# Validation

Runtime clarification은 evidence를 의도적으로 바꾸지만 **domain behavior는 보존**해야 한다.

## Behavior Envelope

대상에 실제로 관련된 surface만 확인한다.

| Surface | Preserve / Check |
| --- | --- |
| Return / result | 값, type, ordering, caller-visible semantics |
| Exceptions | type, trigger condition, causal chain; 의도한 context 보강만 허용 |
| State | mutation, persistence, idempotency, commit timing |
| Side effects | file/database/process/network action과 ordering |
| Gates | approval, validation, promotion acceptance/rejection 기준 |
| Runtime evidence | 의도한 event/context/metadata가 필요한 경우에만 추가·변경됨 |

관찰 가능성이 좋아졌다는 이유로 실행 순서나 실패 조건을 바꾸지 않는다.

## Before and After

가능하면 같은 좁은 validation을 변경 전후에 사용한다.

1. 기존 test나 재현 가능한 실행으로 baseline behavior와 현재 evidence를 확인한다.
1. runtime clarification을 적용한다.
1. 같은 validation을 다시 실행한다.
1. return, exception, state와 side effect가 의도치 않게 달라지지 않았는지 확인한다.
1. 새 evidence가 선택한 reconstruction question에 실제로 답하는지 확인한다.
1. 불필요한 field/event가 있으면 제거한다.

기존 safeguard가 충분하면 instrumentation 검증만을 위해 넓은 test suite나 새로운 test infrastructure를 만들지 않는다.

## Evidence Validation

로그 문자열 자체보다 의미를 검증한다.

- 필요한 event가 적절한 경계에서 발생하는가?
- 중요한 context가 안정적인 field로 남는가?
- failure path에서도 causal context가 보존되는가?
- skip/retry/fallback 등 대상 branch를 구분할 수 있는가?
- secret이나 대용량 payload가 노출되지 않는가?

정확한 formatting이나 incidental message wording을 contract로 고정하지 않는다. 기존 test가 이미 public/operator-visible log contract를 명시한 경우에는 그 contract를 따른다.

## Validation Gaps

실행할 수 없으면 static inspection, caller/result 비교, exception chain 확인, framework metadata 구조 확인 등 가능한 evidence를 사용하고 한계를 명시한다.

실행하지 않은 test나 runtime observation을 수행했다고 표현하지 않는다. 검증 중 defect가 발견되면 runtime clarification 범위를 넘어 수정하지 않고 별도 review/debugging 대상으로 분리한다.
