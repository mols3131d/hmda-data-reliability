# Pull Requests

Pull request는 branch의 변경을 검토하고 repository에 반영할지 결정하는 경계다.

## Scope

- 하나의 pull request는 하나의 변경 목적을 가진다.
- 검토 가능한 크기와 범위로 유지한다.
- 관련 없는 formatting, refactoring 또는 dependency 변경을 함께 포함하지 않는다.
- 목적이 달라지면 기존 pull request를 확장하지 않고 별도 작업으로 분리한다.

변경 단위와 branch naming은 [Branches](branch.md)를 따른다.

## State

| State | Use when |
| --- | --- |
| Draft | 구현이나 validation이 끝나지 않았거나 조기 검토가 필요할 때 |
| Ready | 변경 범위가 안정되고 필요한 review를 요청할 수 있을 때 |
| Closed | 변경을 채택하지 않거나 더 이상 진행하지 않을 때 |
| Merged | 검토된 변경을 기준 branch에 반영했을 때 |

Draft는 미완료 상태를 숨기지 않고 공유하기 위한 상태다. Ready 전환은 완료 선언이 아니라 정식 review 요청을 의미한다.

## Description

Pull request에는 변경을 판단하는 데 필요한 내용만 기록한다.

```markdown
## Summary

- 변경 내용
- 변경 목적

## Validation

- 수행한 검증과 결과
- 수행하지 못한 검증과 이유

## Notes

- 중요한 결정
- 남은 위험 또는 제한
```

관련 Issue, OpenSpec change 또는 개발 문서가 있으면 연결한다. 내용이 없는 section은 형식적으로 유지하지 않아도 된다.

## Review

- 변경의 목적, 동작, test와 문서의 정합성을 검토한다.
- comment가 변경 요청, 질문 또는 제안인지 구분한다.
- 변경 요청을 반영하면 영향 범위에 맞는 validation을 다시 수행한다.
- 중요한 unresolved comment와 conflict를 남긴 채 merge하지 않는다.
- 큰 수정으로 기존 review의 근거가 달라졌다면 다시 검토한다.

Validation과 review 범위는 변경의 위험과 영향에 비례한다. 모든 pull request에 전체 test suite나 동일한 review 수준을 요구하지 않는다.

## Merge And Close

필요한 review와 required check가 완료되고 중요한 conflict가 해결된 뒤 merge한다. Merge 방식은 repository 설정과 변경 성격에 따라 결정한다.

채택하지 않는 pull request는 Close한다. Close된 pull request의 commit, diff와 discussion은 의사결정 이력으로 유지한다.

병합된 branch는 repository의 자동 삭제 설정이나 권한 있는 주체가 정리한다. 기존 변경을 그대로 이어갈 수 있으면 pull request를 reopen하고, 목적이나 접근 방식이 달라졌다면 새 branch와 pull request를 만든다.

## Agent

- Repository content 변경은 Draft pull request로 전달한다.
- 수행한 validation과 수행하지 못한 validation을 구분한다.
- CI 또는 review 실패를 조용히 무시하지 않는다.
- 인간의 명시적 요청 없이 Ready 전환, 승인, merge 또는 auto-merge 설정을 수행하지 않는다.
- 인간의 판단 없이 review thread를 해결 처리하지 않는다.
- 승인 여부가 불명확하면 승인으로 해석하지 않는다.

## Related

- [Branches](branch.md): pull request가 소유하는 변경 목적과 branch 규칙
- [Commits](commit.md): pull request history를 구성하는 commit 기준
