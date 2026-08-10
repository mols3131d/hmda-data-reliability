# Pull Request Reviews

Pull Request review는 변경을 채택하기 전에 correctness, risk와 repository contract 일관성을 검토하고 actionable finding을 기록한다.

## Scope

Review는 Pull Request diff를 중심으로 변경 목적, owning contract, 관련 test와 validation evidence를 필요한 범위에서 확인한다. 변경과 직접 관련 없는 개선 제안은 현재 review finding과 분리한다.

## Findings

Review body는 [Pull Request Review Template](../../../.github/templates/pull-request-review.md)을 기본 형식으로 사용한다.

Finding은 중요도와 함께 문제, 근거, 영향, 필요한 수정을 명확히 기록한다. 근거 없이 가능성만 제시하거나 변경 범위를 벗어난 선호를 blocker로 만들지 않는다.

발견 사항이 없으면 `Findings`에 `None`을 기록한다.

Review decision은 GitHub가 소유하므로 review body에 `Approve`, `Comment`, `Request Changes`를 별도 metadata로 반복하지 않는다.

## Validation

검토한 범위와 사용한 근거를 기록한다. 실행하지 못한 validation, 접근할 수 없는 evidence 또는 확인하지 않은 범위가 review 판단에 영향을 줄 수 있으면 명시한다.

Pull Request가 변경되어 기존 finding이나 validation 근거가 달라지면 영향을 받는 부분을 다시 검토한다.

## Metadata

Template 상단의 YAML code block과 `author` 규칙은 [GitHub Templates](../../../.github/templates/README.md)를 따른다. GitHub가 이미 제공하는 reviewer 계정이나 review decision은 중복 기록하지 않는다.

## Agent Instructions

Agent의 review action과 lifecycle 제약은 [Pull Requests](pull-request.md#agent-instructions)를 따른다. 인간의 명시적 요청 없이 review thread를 해결하거나 approval을 대신 확정하지 않는다.

## Related

- [Pull Requests](pull-request.md): Pull Request scope, lifecycle과 validation 기준
- [Pull Request Review Template](../../../.github/templates/pull-request-review.md): review body 형식
- [GitHub Templates](../../../.github/templates/README.md): 공통 metadata header와 `author` 규칙
