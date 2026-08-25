# Pull Request Reviews

Pull Request review는 변경을 채택하기 전에 correctness, risk와 repository contract 일관성을 검토하고 evidence-backed finding을 기록한다.

## Scope

Review는 Pull Request diff를 중심으로 변경 목적, owning contract, 관련 test와 validation evidence를 필요한 범위에서 확인한다. 변경과 직접 관련 없는 개선 제안은 현재 review finding과 분리한다.

전체 PR을 일반 기준으로 검토했다면 별도 `Scope` section은 생략할 수 있다. 일부만 검토했거나 특별한 기준을 적용했다면 검토 범위와 미검토 영역을 명시한다.

## Review Body

Review의 결론과 가장 중요한 근거를 먼저 요약한다. 실제 section 구성과 작성 형식은 [Pull Request Review Template](../../../.github/templates/pull-request-review.md)을 따른다.

GitHub가 소유하는 review decision(`Approve`, `Comment`, `Request Changes`)은 review body에 반복하지 않는다.

## Findings

Finding은 root cause별로 독립적인 ID를 부여하고 location, evidence, impact와 required change를 연결한다. 근거 없이 가능성만 제시하거나 변경 범위를 벗어난 선호를 blocker로 만들지 않는다.

중요도는 impact와 urgency를 기준으로 표시한다. 색상만으로 의미를 전달하지 않고 text label을 함께 사용한다.

| Importance | Meaning |
| --- | --- |
| `🔴 Critical` | merge 또는 운영을 중단해야 할 수준의 치명적 영향 |
| `🟠 High` | correctness, data integrity 또는 주요 contract에 큰 영향을 주는 문제 |
| `🟡 Medium` | 영향이 제한적이지만 현재 변경에서 명확히 다룰 가치가 있는 문제 |
| `🔵 Low` | 영향이 작지만 구체적이고 재현 가능한 개선 필요 사항 |

중요도는 확신도를 의미하지 않는다. 확인되지 않은 전제나 validation 한계가 finding의 확실성에 영향을 주면 `Uncertainty`로 별도 기록한다.

Finding heading과 no-finding 표기 같은 작성 형식은 [Pull Request Review Template](../../../.github/templates/pull-request-review.md)에 위임한다.

## Validation

수행한 check, result와 evidence를 구분해 기록한다. 실행하지 못한 validation, 접근할 수 없는 evidence 또는 확인하지 않은 범위가 review 판단에 영향을 줄 수 있으면 명시한다.

Automation pass는 finding 부재를 증명하지 않으며, 실행하지 않은 validation을 수행한 것처럼 표현하지 않는다.

Pull Request가 실질적으로 변경되어 기존 finding이나 validation 근거가 달라지면 영향을 받는 부분을 다시 검토한다.

Validation의 list/table 선택과 상태 표기 형식은 [Pull Request Review Template](../../../.github/templates/pull-request-review.md)을 따른다.

## Remaining Risks

수정 후에도 남는 위험, review 범위 밖의 중요한 제한 또는 후속 확인이 있을 때만 기록한다. 별도 작업으로 분리해야 하는 개선 사항을 현재 PR의 required change로 만들지 않는다.

## Metadata

Optional metadata의 사용 조건과 형식은 [GitHub Templates](../../../.github/templates/README.md)에 위임한다. GitHub가 이미 제공하는 reviewer 계정이나 review decision은 중복 기록하지 않는다.

## Agent Instructions

Agent의 review action과 lifecycle 제약은 [Pull Requests](pull-request.md#agent-instructions)를 따른다. 인간의 명시적 요청 없이 review thread를 해결하거나 approval을 대신 확정하지 않는다.

## Related

- [Pull Requests](pull-request.md): Pull Request scope, lifecycle과 validation 기준
- [Pull Request Review Template](../../../.github/templates/pull-request-review.md): review body의 section 구성과 작성 형식
- [GitHub Templates](../../../.github/templates/README.md): 공통 metadata 규칙
