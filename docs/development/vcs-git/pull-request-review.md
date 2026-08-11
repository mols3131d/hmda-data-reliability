# Pull Request Reviews

Pull Request review는 변경을 채택하기 전에 correctness, risk와 repository contract 일관성을 검토하고 evidence-backed finding을 기록한다.

## Scope

Review는 Pull Request diff를 중심으로 변경 목적, owning contract, 관련 test와 validation evidence를 필요한 범위에서 확인한다. 변경과 직접 관련 없는 개선 제안은 현재 review finding과 분리한다.

전체 PR을 일반 기준으로 검토했다면 별도 `Scope` section은 생략할 수 있다. 일부만 검토했거나 특별한 기준을 적용했다면 범위와 미검토 영역을 명시한다.

## Findings

Review body는 [Pull Request Review Template](../../../.github/templates/pull-request-review.md)을 기본 형식으로 사용한다.

Review의 결론과 가장 중요한 근거를 먼저 요약한다. Finding은 독립적인 ID를 사용하고 location, evidence, impact와 required change를 연결한다.

Finding의 중요도는 impact와 urgency를 기준으로 표시한다. 색상만으로 의미를 전달하지 않고 text label을 함께 사용한다.

- `🔴 Critical`: merge 또는 운영을 중단해야 할 수준의 치명적 영향
- `🟠 High`: correctness, data integrity 또는 주요 contract에 큰 영향을 주는 문제
- `🟡 Medium`: 영향이 제한적이지만 현재 변경에서 명확히 다룰 가치가 있는 문제
- `🔵 Low`: 영향이 작지만 구체적이고 재현 가능한 개선 필요 사항

Heading은 `### 🟠 High — F1 · <finding title>` 형식을 사용한다. 중요도는 확신도를 의미하지 않으며, 판단의 불확실성은 `Uncertainty`로 별도 기록한다.

확인되지 않은 전제나 validation 한계가 finding의 확실성에 영향을 주면 uncertainty를 명시한다. 근거 없이 가능성만 제시하거나 변경 범위를 벗어난 선호를 blocker로 만들지 않는다.

발견 사항이 없으면 `Findings`의 `<finding 결과>`를 `✅ No findings`로 교체한다. 문제가 있으면 placeholder를 제거하고 root cause별 finding을 작성한다.

Review decision은 GitHub가 소유하므로 review body에 `Approve`, `Comment`, `Request Changes`를 별도 metadata로 반복하지 않는다.

## Validation

수행한 check와 evidence, result를 구분해 기록한다. 실행하지 못한 validation, 접근할 수 없는 evidence 또는 확인하지 않은 범위가 review 판단에 영향을 줄 수 있으면 명시한다.

항목이 적으면 list를 사용한다. 비교 가능한 check가 많아 `Check / Result / Evidence`를 반복해야 하면 table을 사용할 수 있다. 상태는 `✅ Pass`, `❌ Fail`, `⚪ Not Verified` 중 실제 결과로 `<status>` placeholder를 교체한다.

Automation pass는 finding 부재를 증명하지 않으며, 실행하지 않은 validation을 수행한 것처럼 표현하지 않는다.

Pull Request가 실질적으로 변경되어 기존 finding이나 validation 근거가 달라지면 영향을 받는 부분을 다시 검토한다.

## Remaining Risks

수정 후에도 남는 위험, review 범위 밖의 중요한 제한 또는 후속 확인이 있을 때만 기록한다. 별도 작업으로 분리해야 하는 개선 사항을 현재 PR의 required change로 만들지 않는다.

## Metadata

Optional `author`와 `revision` metadata는 [GitHub Templates](../../../.github/templates/README.md)를 따른다. `revision`은 review가 실제로 검토한 exact base/head commit pair를 기록하며, 이후 PR head가 변경되어도 과거 review의 기준은 바꾸지 않는다. GitHub가 이미 제공하는 reviewer 계정이나 review decision은 중복 기록하지 않는다.

## Agent Instructions

Agent의 review action과 lifecycle 제약은 [Pull Requests](pull-request.md#agent-instructions)를 따른다. 인간의 명시적 요청 없이 review thread를 해결하거나 approval을 대신 확정하지 않는다.

## Related

- [Pull Requests](pull-request.md): Pull Request scope, lifecycle과 validation 기준
- [Pull Request Review Template](../../../.github/templates/pull-request-review.md): review body 형식
- [GitHub Templates](../../../.github/templates/README.md): 공통 metadata와 `author`, `revision` 규칙
