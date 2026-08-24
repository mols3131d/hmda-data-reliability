# Findings

Candidate를 검증하고 evidence-linked Review 결과를 작성할 때 읽습니다.

## Candidate Before Finding

처음 발견한 이상은 확정 finding이 아니라 candidate입니다.

Candidate마다 다음을 확인합니다.

- in-scope target과 직접 관련되는가
- contract 또는 observable behavior를 위반하는가
- 실제로 도달 가능한 condition과 path가 있는가
- baseline에도 동일하게 존재하는가
- safeguard가 이미 방지하거나 제한하는가
- impact가 구체적이고 현재 evidence에 비례하는가
- 다른 candidate와 같은 root cause인가

이 기준을 통과하지 못하면 기각하거나 불확실성으로 보존합니다.

## Finding Contract

각 finding은 다음 질문에 독립적으로 답할 수 있어야 합니다.

| Field | Question |
| --- | --- |
| Claim | 무엇이 잘못되었는가? |
| Location | 어디에서 시작되거나 드러나는가? |
| Evidence | 어떤 code, contract 또는 실행 결과가 이를 뒷받침하는가? |
| Reachability | 어떤 입력, state 또는 call path에서 발생하는가? |
| Impact | 사용자, data, compatibility, operation 또는 validation에 어떤 영향을 주는가? |
| Uncertainty | 무엇을 아직 확인하지 못했는가? |

Severity와 verdict는 호출자의 Review 계약을 따릅니다. 이 스킬은 특정 severity taxonomy를 강제하지 않습니다.

## Recommended Shape

```markdown
### <간결한 defect 또는 risk 설명>

- **Location:** `path:line` 또는 `path#symbol`
- **Evidence:** contract, code path 또는 observed result
- **Reachability:** 발생 조건과 실행 경로
- **Impact:** 구체적인 실패 결과
- **Uncertainty:** 남은 제한이 있을 때만 작성
```

형식을 기계적으로 채우지 않습니다. 한 문단으로 더 명확하면 합쳐도 되지만 location, evidence와 impact는 잃지 않습니다.

## Evidence Strength

| Strength | Meaning |
| --- | --- |
| Observed | 실제 실행 또는 직접 관찰로 확인했습니다. |
| Demonstrated | code path와 input으로 재현 가능하게 입증했습니다. |
| Reasoned | contract와 reachable path에서 논리적으로 도출했습니다. |
| Uncertain | 중요한 전제 또는 environment를 확인하지 못했습니다. |

Reasoned finding도 유효할 수 있지만 실행한 것처럼 표현하지 않습니다. Uncertain candidate는 확정 defect와 구분합니다.

## High-Value Findings

다음 finding을 우선합니다.

- contract 또는 required behavior 실패
- data loss, corruption 또는 invalid persisted state
- reachable crash, incorrect result 또는 silent failure
- compatibility와 regression
- authorization, trust boundary 또는 sensitive-data exposure
- recovery 불가, unbounded retry 또는 resource exhaustion
- false green으로 중요한 defect가 검출되지 않음
- validation evidence가 실제 target을 검증하지 않음

Maintainability finding은 구체적인 correctness, regression 또는 검증 위험과 연결될 때만 포함합니다.

## Reject Low-Value Findings

다음은 기본적으로 finding으로 만들지 않습니다.

- repository rule과 연결되지 않은 style 선호
- 영향이 없는 naming 또는 formatting
- target과 무관한 기존 defect
- 구체적인 reachable path가 없는 이론적 가능성
- 충분한 근거 없이 더 나은 architecture를 제안하는 redesign
- 이미 safeguard로 완전히 차단된 scenario
- 같은 root cause를 반복한 여러 표현
- 동작을 바꾸지 않는 선택적 test 추가 제안

## Distinguish Change And Existing State

Baseline 비교가 가능하면 다음을 구분합니다.

- 변경이 새로 도입한 defect
- 변경이 기존 defect를 확장하거나 노출한 경우
- 변경과 무관한 pre-existing issue
- baseline을 확인할 수 없어 introduced 여부가 불명확한 경우

Pre-existing issue가 현재 변경을 안전하게 적용할 수 없게 만들면 관련성은 보고하되 새로 도입된 문제처럼 표현하지 않습니다.

## Validation Reporting

Validation은 finding과 별도로 정확히 기록합니다.

- 실행한 command와 scope
- observed result
- finding을 확인하거나 반박한 내용
- 실행하지 못한 범위와 이유
- 전체 suite 또는 production behavior로 일반화할 수 없는 제한

Automation pass는 finding 부재의 증명이 아니며, failure는 항상 target defect를 의미하지 않습니다.

## Synthesis

여러 Review 결과를 종합할 때는 다음을 수행합니다.

- 같은 root cause를 하나로 통합합니다.
- 독립 evidence가 같은 claim을 지지하는지 확인합니다.
- 서로 충돌하는 claim의 전제와 scope를 비교합니다.
- 증거가 약하거나 이미 반박된 candidate를 제거합니다.
- 확인되지 않은 불확실성을 조용히 누락하지 않습니다.

종합은 세 번째 전체 Review가 아니라 기존 candidate의 검증과 정리입니다.
