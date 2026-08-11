# Validation

Runtime clarification은 evidence를 의도적으로 바꾸지만 **domain behavior와 caller contract는 보존**해야 한다.

## Behavior Envelope

대상과 실제 관련된 surface만 확인한다.

| Surface | Preserve / Check |
| --- | --- |
| Return / result | 값, type, ordering, caller-visible semantics |
| Exceptions | type, trigger condition, causal chain; 의도한 context 보강만 허용 |
| State | mutation, persistence, idempotency, commit timing |
| Side effects | file, database, process, network action과 ordering |
| Gates | approval, validation, promotion acceptance/rejection 기준 |
| Runtime evidence | 선택한 질문에 필요한 event/context/metadata만 의도대로 변경됨 |

관찰 가능성이 좋아졌다는 이유로 실행 순서나 실패 조건을 바꾸지 않는다.

## Before And After

가능하면 같은 좁은 validation을 변경 전후에 사용한다.

1. 기존 test나 재현 가능한 실행으로 baseline behavior와 현재 evidence를 확인한다.
1. runtime clarification을 적용한다.
1. 같은 validation으로 return, exception, state와 side effect가 의도치 않게 달라지지 않았는지 확인한다.
1. 새 evidence만 보고 선택한 복원 질문에 실제로 답할 수 있는지 확인한다.
1. 질문에 필요하지 않은 field, event 또는 duplication을 제거한다.

기존 safeguard가 충분하면 instrumentation 검증만을 위해 넓은 test suite나 새로운 test infrastructure를 만들지 않는다.

## Validate Meaning

로그 문자열 자체보다 의미를 검증한다.

- 필요한 evidence가 owning boundary에서 남는가?
- 중요한 target/outcome/reason이 안정적인 field로 구분되는가?
- failure path의 causal context가 보존되는가?
- skip, retry, fallback 같은 대상 경로를 필요한 경우 구분할 수 있는가?
- 민감하거나 과도한 데이터가 추가되지 않았는가?

정확한 formatting이나 incidental wording을 contract로 고정하지 않는다. 기존 test나 외부 consumer가 이미 log/event contract를 명시한 경우에는 그 contract를 따른다.

## Validation Gaps

실행할 수 없으면 static inspection, caller/result 비교, exception chain, artifact 또는 framework metadata 구조 확인 등 가능한 evidence를 사용하고 한계를 명시한다.

실행하지 않은 test나 runtime observation을 수행했다고 표현하지 않는다. 검증 중 defect가 발견되면 runtime clarification 범위를 넘어 수정하지 않고 별도 review/debugging 대상으로 분리한다.
