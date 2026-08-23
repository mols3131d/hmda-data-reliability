# Test Review

Test code, fixture, oracle와 validation 신뢰성을 검토할 때 읽습니다.

## Review The Test As Evidence

Test의 존재나 pass 여부가 아니라 실제 defect를 검출할 수 있는지를 평가합니다.

```text
contract → risk → scenario → oracle → assertion → observed failure
```

Test가 production implementation과 같은 가정이나 algorithm을 복제하면 둘이 함께 잘못될 수 있습니다.

## Review Axes

### Contract And Scenario Coverage

- in-scope requirement와 중요한 risk가 scenario 또는 명시적 exclusion에 연결되는가
- normal case만 반복하고 boundary, failure 또는 regression path를 놓치지 않는가
- scenario가 실제 externally observable behavior를 검증하는가
- 변경과 직접 관련 없는 case를 늘려 coverage처럼 보이게 하지 않는가
- test 이름과 설명이 검증하는 behavior를 정확히 나타내는가

모든 조합을 요구하지 않습니다. 실패 영향과 회귀 가능성이 높은 대표 scenario를 우선합니다.

### Independent Oracle

- expected result가 spec, 단순한 invariant 또는 독립적으로 계산 가능한 값에서 오는가
- production algorithm을 test 안에서 다시 구현하지 않는가
- mock call count가 public result나 state 검증을 대신하지 않는가
- snapshot이 의미 있는 contract 차이를 드러내는가
- broad truthiness, non-empty 또는 type-only assertion으로 중요한 오류를 놓치지 않는가

Oracle이 모호하거나 구현에 종속되면 test pass를 강한 evidence로 취급하지 않습니다.

### False Green Risks

다음을 우선 확인합니다.

- assertion이 없거나 핵심 결과를 확인하지 않음
- broad exception capture가 예상하지 않은 failure도 통과시킴
- unconditional skip, xfail 또는 early return
- mock이 검증해야 할 domain behavior 자체를 대신 구현함
- fixture default 때문에 중요한 branch에 도달하지 않음
- parameterization이 서로 다른 case를 같은 weak assertion으로 덮음
- snapshot 또는 golden file을 변경 결과에 맞춰 무비판적으로 갱신함
- test가 실행되거나 수집되지 않는데 suite pass로 오인함

False green은 구체적인 defect가 통과할 수 있는 조건을 보여줄 때 finding으로 작성합니다.

### Isolation And Determinism

- shared mutable state나 test order에 의존하는가
- clock, randomness, locale, timezone 또는 environment를 적절히 통제하는가
- 실제 network나 shared service에 불필요하게 의존하는가
- temporary resource와 patch가 실패 후에도 정리되는가
- parallel execution에서 충돌 가능한 path나 identifier를 사용하는가
- retry로 flaky failure를 숨기지 않는가

Project가 병렬 실행이나 특정 fixture 정책을 정의하면 해당 로컬 규칙을 우선합니다.

### Level And Cost

- 가장 낮은 비용의 신뢰 가능한 boundary에서 검증하는가
- unit test로 실제 file, database 또는 protocol contract를 흉내만 내지 않는가
- integration test가 isolated rule 하나를 위해 과도한 setup을 요구하지 않는가
- 느린 test가 더 강한 evidence를 제공하는가
- broad suite 실행만 있고 변경을 직접 검증하는 focused test가 없는가

Test level은 빠르기보다 contract를 실제로 관찰할 수 있는 가장 낮은 수준으로 판단합니다.

### Fixtures, Helpers And Documentation

- fixture와 helper가 scenario의 중요한 차이를 숨기지 않는가
- default data가 production-like edge case를 제거하지 않는가
- helper가 assertion까지 감춰 failure location을 모호하게 하지 않는가
- test-specific data가 이해 가능하고 최소한인가
- 대응 design document나 docstring이 있다면 현재 scenario와 일치하는가

Repository의 test directory instruction과 testing guide가 있으면 해당 범위에서 적용합니다.

### Relationship With Implementation

구현과 테스트가 함께 변경되었으면 다음을 교차 확인합니다.

- test가 변경된 contract가 아니라 현재 implementation detail에 맞춰졌는가
- production defect를 test assertion 약화로 숨겼는가
- 새 behavior에 test가 없더라도 기존 test나 invariant가 충분히 보호하는가
- test failure가 production defect, test defect, contract gap 또는 environment failure 중 무엇인가
- focused test 통과를 broader compatibility의 증명으로 과장하는가

## Validation Evidence

Test execution을 검토할 때 다음을 구분합니다.

- 실제 실행한 command
- 수집된 test와 적용된 marker·filter
- pass, fail, skip, xfail 수와 핵심 failure
- 실행하지 못한 범위와 이유
- focused result로부터 추론할 수 없는 broader claim

실행 log가 없으면 pass를 가정하지 않습니다. 기존 CI badge나 이전 run이 현재 target을 검증하는지도 확인합니다.

## Evidence

Test finding에는 가능한 한 다음을 연결합니다.

- 문제가 있는 test, fixture 또는 helper 위치
- 통과할 수 있는 실제 defect 또는 검증되지 않는 contract
- false green이 발생하는 setup과 assertion path
- 해당 gap이 변경의 confidence에 미치는 영향
- 필요한 경우 가장 작은 재현 또는 validation command
