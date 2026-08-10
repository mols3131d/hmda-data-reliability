# Pull Requests

Pull request는 branch의 변경을 검토하고 repository에 반영할지 결정하는 경계다.

## Scope

하나의 pull request는 하나의 변경 목적을 가진다. 같은 목적의 변경은 함께 다루고, 독립적인 새 목적은 별도의 branch와 pull request로 분리한다.

변경 단위와 branch naming은 [Branches](branch.md)를 따른다.

## Description

Pull request에는 현재 변경을 판단하는 데 필요한 내용만 기록한다. 기본 형식은 [Pull Request Template](../../../.github/templates/pull-request.md)을 따른다.

- `Summary`는 **왜 변경하는지와 기대 결과**를 먼저 설명한다.
- `Changes`는 시행착오나 되돌린 시도가 아니라 최종 net change를 기록한다.
- `Boundaries`는 의도적으로 제외한 범위나 scope 오해 가능성이 있을 때만 사용한다.
- `Validation`은 수행한 검증과 그 evidence를 연결하고, 실패하거나 확인하지 못한 결과를 숨기지 않는다.
- `Review Focus`는 인간 또는 다음 reviewer의 판단이 특히 필요한 부분이 있을 때만 사용한다.
- `Risks`와 `References`는 실제 내용이 있을 때만 유지한다.

Agent의 작업 과정, 상세 reasoning, RPI 단계별 진행 기록, 시행착오와 commit별 변경 내역은 PR description에 복제하지 않는다. 그 과정 자체가 보존할 가치가 있으면 owning artifact에 기록하고 PR에서는 최종 결과나 필요한 reference만 남긴다.

GitHub UI나 CI가 이미 충분히 제공하는 정보도 판단에 필요한 추가 맥락이 없다면 반복하지 않는다. 관련 OpenSpec change, inbox artifact 또는 canonical document가 있으면 `References`에서 연결하며, 요구사항이나 acceptance criteria의 source를 PR 본문에 다시 복제하지 않는다.

Template 상단의 YAML code block과 `author` 규칙은 [GitHub Templates](../../../.github/templates/README.md)를 따른다.

## Review And Validation

Validation과 review 범위는 변경의 위험과 영향에 비례한다. 수행한 검증과 수행하지 못한 검증을 구분하고, 기존 review의 근거를 바꾸는 수정은 다시 검토한다.

Pull Request review의 기록 형식과 finding 기준은 [Pull Request Reviews](pull-request-review.md)를 따른다.

필요한 review와 required check가 완료되고 중요한 conflict가 해결된 뒤 merge한다.

## Lifecycle

```text
Draft PR → 변경 갱신 → 인간 검토 → merge 또는 명시적 close
```

수정 요청이 있으면 변경 갱신과 인간 검토를 반복한다. 동일한 변경 목적은 기존 Draft PR을 이어가며, 목적이나 접근 방식이 달라지면 새 branch와 pull request를 사용한다.

## Agent Instructions

- Repository content 변경은 Draft pull request로 전달한다. 단, [Inbox Branch](branch.md#inbox-branch)의 routine artifact direct push 예외를 따른다.
- 인간의 명시적 요청 없이 Ready 전환, 승인, merge, close 또는 auto-merge를 수행하지 않는다.
- 인간의 판단 없이 review thread를 해결 처리하지 않는다.
- 실패하거나 수행하지 못한 validation을 숨기지 않으며, 불명확한 응답을 승인으로 해석하지 않는다.

## Related

- [Branches](branch.md): pull request가 소유하는 변경 목적과 branch 기준
- [Commits](commit.md): pull request history를 구성하는 commit 기준
- [Pull Request Reviews](pull-request-review.md): pull request review 기준과 기록 방식
- [GitHub Templates](../../../.github/templates/README.md): Pull Request와 review template metadata 규칙
