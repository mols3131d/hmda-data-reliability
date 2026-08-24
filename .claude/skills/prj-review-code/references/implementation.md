# Implementation Review

Production code와 runtime behavior를 검토할 때 읽습니다.

## Review From Behavior

Line-level style보다 변경이 observable contract를 어떻게 바꾸는지 먼저 확인합니다.

```text
contract → changed path → reachable behavior → observable result → impact
```

변경된 function만 고립해서 보지 않고 public boundary, caller, data flow와 failure propagation을 필요한 만큼 추적합니다.

## Review Axes

### Completeness And Correctness

- in-scope requirement와 task가 실제 behavior로 구현되었는가
- 정상 입력, boundary와 invalid input에서 contract가 성립하는가
- 조건, 계산, 변환과 state transition이 의도와 일치하는가
- 일부 branch나 integration path가 누락되지 않았는가
- 반환값, side effect, event와 persisted state가 일관되는가

### Contracts And Compatibility

- public API, schema, file format와 protocol을 조용히 깨뜨리지 않는가
- caller와 callee의 precondition·postcondition이 맞는가
- optional, null, default와 version compatibility가 유지되는가
- configuration과 environment 차이가 behavior를 예기치 않게 바꾸지 않는가
- migration 또는 fallback이 필요한 변경인가

### State And Data Integrity

- partial update, duplicate execution과 retry에서 invariant가 유지되는가
- transaction 또는 cleanup boundary가 충분한가
- stale, missing, malformed와 out-of-order data를 안전하게 처리하는가
- 실패 후 복구 가능한 상태를 남기는가
- idempotency, ordering과 ownership assumption이 실제로 보장되는가

### Failure And Reachability

관련된 경우에만 다음을 검토합니다.

- error가 삼켜지거나 잘못 변환되는가
- timeout, cancellation, retry와 fallback이 잘못 상호작용하는가
- concurrency나 reentrancy가 invalid state를 만들 수 있는가
- trust boundary를 넘는 input이 검증되는가
- resource exhaustion, memory 또는 unbounded work가 reachable한가
- safeguard가 failure 전에 실제로 동작하는가

가능성만 나열하지 않고 구체적인 진입 조건과 실행 경로를 확인합니다.

### Regression

- baseline에서 유지되던 externally observable behavior가 바뀌는가
- 새 분기나 default가 기존 caller를 다른 path로 보내는가
- error type, ordering, precision, timing 또는 side effect가 달라지는가
- 변경과 직접 관련된 기존 test·contract가 보호되지 않는가
- 문제를 고치면서 다른 valid case를 거부하지 않는가

### Maintainability

Maintainability는 구체적인 defect 가능성 또는 변경 비용과 연결될 때만 finding으로 다룹니다.

- 한 책임의 변경이 여러 위치에 중복되어 불일치할 가능성이 큰가
- 숨은 coupling이나 global state가 behavior 이해와 검증을 방해하는가
- branch와 state 조합이 실제로 누락 또는 잘못된 처리를 만들기 쉬운가
- abstraction이 contract를 숨기거나 잘못된 재사용을 강제하는가
- 불필요한 complexity가 이미 correctness 또는 testability 문제를 만드는가

단순한 이름, formatting, 개인적인 abstraction 선호는 제외합니다.

## Safeguards

다음은 defect를 완전히 부정하지는 않지만 candidate를 검증할 때 확인해야 합니다.

- input validation과 type constraint
- database constraint와 transaction
- retry limit, timeout과 circuit breaker
- feature flag와 rollout boundary
- caller-side normalization 또는 guard
- focused test와 runtime assertion

Safeguard가 실제 path에서 적용되는지 확인하지 않고 존재만으로 안전하다고 판단하지 않습니다.

## Evidence

구현 finding에는 가능한 한 다음을 연결합니다.

- defect가 시작되는 file과 symbol 또는 line
- 도달 가능한 caller나 input condition
- 위반되는 contract 또는 baseline behavior
- 관찰되거나 논리적으로 필연적인 result
- 사용자, data, compatibility 또는 operation에 미치는 impact

해결책은 defect를 이해하는 데 필요한 수준으로만 언급합니다. 선택적 redesign을 finding으로 바꾸지 않습니다.
