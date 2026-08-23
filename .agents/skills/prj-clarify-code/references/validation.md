# Validation

Clarification은 behavior-preserving change다. 가독성 개선을 이유로 동작 drift를 허용하지 않는다.

## Behavior Envelope

대상에서 실제로 관찰 가능한 surface만 포함한다.

| Surface | Check |
| --- | --- |
| API / registration | import path, call shape, framework entrypoint identity |
| Return | value, type, ordering, shape, sentinel 의미 |
| Exceptions | type, trigger condition, causal context |
| State | mutation, persistence, idempotency |
| Side effects | file/database/network write, overwrite/delete, 실행 순서 |
| Validation | acceptance/rejection 기준과 timing |
| Observability | log/event 의미와 실패 가시성 |

모든 항목을 기계적으로 조사하지 않는다. rename·move·extraction은 explicit caller가 없어도 framework registration이나 runtime discovery를 깨뜨릴 수 있는지 확인한다.

## Before and After

가능하면 같은 좁은 validation을 변경 전후에 적용한다.

1. 기존 test 또는 재현 가능한 입력으로 baseline을 확인한다.
1. clarification을 적용한다.
1. 같은 validation을 다시 실행한다.
1. 예상하지 않은 output, exception, state, side-effect, registration 차이가 없는지 본다.
1. type/lint/static check는 보조 evidence로 사용한다.

기존 safeguard가 충분하면 새 test를 만들지 않는다.

중요한 behavior에 safeguard가 없고 다른 검증으로 refactor 위험을 줄일 수 없을 때만 작은 characterization test를 고려한다. 현재 observable contract만 고정하고 implementation detail이나 새 requirement는 추가하지 않는다.

## Validation Gaps

검증할 수 없으면 가능한 대체 evidence를 사용하고 한계를 명시한다: static/type check, deterministic I/O 비교, import/registration 확인, caller와 test oracle 대조.

대체 evidence를 test 실행과 동등하게 표현하지 않는다. 검증 중 clarification 범위를 벗어난 문제가 드러나면 `SKILL.md`의 Boundaries를 따른다.
