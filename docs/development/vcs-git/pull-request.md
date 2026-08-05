# Pull Requests

Pull request는 branch의 변경을 검토하고 repository에 반영할지 결정하는 경계다.

## Scope

하나의 pull request는 하나의 변경 목적을 가진다. 같은 목적의 변경은 함께 다루고, 독립적인 새 목적은 별도의 branch와 pull request로 분리한다.

변경 단위와 branch naming은 [Branches](branch.md)를 따른다.

## Description

Pull request에는 변경을 판단하는 데 필요한 내용만 기록한다.

```markdown
## Summary

- 변경 내용과 목적

## Validation

- 수행한 검증과 결과
- 수행하지 못한 검증과 이유

## Notes

- 중요한 결정, 위험 또는 제한
```

관련 Issue, OpenSpec change 또는 개발 문서가 있으면 연결한다. 내용이 없는 section은 생략할 수 있다.

## Review And Validation

Validation과 review 범위는 변경의 위험과 영향에 비례한다. 수행한 검증과 수행하지 못한 검증을 구분하고, 기존 review의 근거를 바꾸는 수정은 다시 검토한다.

필요한 review와 required check가 완료되고 중요한 conflict가 해결된 뒤 merge한다.

## Lifecycle

진행 중이거나 조기 검토가 필요한 변경은 Draft로 공유한다. 채택하지 않는 pull request는 close하며, commit, diff와 discussion은 의사결정 이력으로 유지한다.

동일한 변경 목적은 기존 pull request를 이어갈 수 있다. 목적이나 접근 방식이 달라지면 새 branch와 pull request를 사용한다.

## Agent

- Repository content 변경은 Draft pull request로 전달한다.
- 인간의 명시적 요청 없이 Ready 전환, 승인, merge 또는 auto-merge를 수행하지 않는다.
- 인간의 판단 없이 review thread를 해결 처리하지 않는다.
- 실패하거나 수행하지 못한 validation을 숨기지 않으며, 불명확한 응답을 승인으로 해석하지 않는다.

## Related

- [Branches](branch.md): pull request가 소유하는 변경 목적과 branch 기준
- [Commits](commit.md): pull request history를 구성하는 commit 기준
