# Diagnosis

가독성 문제를 모두 고치지 않는다. **오해 비용이 가장 큰 병목 하나**를 먼저 찾는다.

## Usage Surface

Caller는 명시적인 Python 호출부에 한정되지 않는다.

- public import와 직접 caller
- framework가 발견·호출하는 asset, callback, hook, plugin entrypoint
- config나 runtime registration으로 연결되는 entrypoint

rename이나 extraction 전에 대상 이름·경로·등록 방식이 caller-visible contract인지 확인한다.

## Diagnose and Intervene

| Bottleneck | Signal | Smallest useful intervention |
| --- | --- | --- |
| Intent | 이름과 call site만으로 목적이 불분명하다 | internal rename, local regrouping |
| Caller contract | type·signature로 표현되지 않는 사용 의미가 숨어 있다 | docstring, 더 정확한 type/name |
| Rationale | 정책, invariant, 예외, 순서의 이유가 복원되지 않는다 | intent comment |
| Responsibility | 독립적인 책임이 한 함수에 섞인다 | 경계가 선명할 때만 extract |
| Control flow | nesting이나 abstraction level 혼합이 흐름을 가린다 | guard clause, local simplification |
| Navigation | wrapper/helper가 새 의미 없이 이동만 늘린다 | inline, merge, indirection 제거 |

시각적 복잡성보다 **잘못 이해했을 때의 영향**을 우선한다: destructive side effect, approval/validation gate, ordering, invariant → caller contract → maintainer rationale → local structure.

선택한 병목에서는 다음 원칙으로 가장 작은 해법을 고른다.

- Caller-visible name이나 import path는 clarification만을 위해 변경하지 않는다.
- Internal name이나 local structure로 충분하면 prose를 추가하지 않는다.
- Caller가 알아야 할 숨은 contract는 docstring으로 보완한다.
- Maintainer에게 필요한 code-local 이유는 comment로 보완한다.
- 독립 책임이 있고 call site가 선명해질 때만 extraction을 고려한다.
- abstraction이 의미보다 navigation cost를 더 만들면 축소한다.

판단이 clarification 범위를 벗어나면 `SKILL.md`의 Boundaries를 따른다.
