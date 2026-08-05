# Commits

Commit은 하나의 논리적 변경을 기록하고 review 가능한 history를 만든다.

Commit message의 형식, type, 길이와 언어는 [`.gitmessage`](../../../.gitmessage)를 canonical source로 사용한다.

## Change Unit

- 하나의 commit은 하나의 논리적 변경을 표현한다.
- 관련 file은 작업 단위로 묶고 file마다 기계적으로 commit하지 않는다.
- 서로 다른 목적이나 요청 범위 밖의 변경을 섞지 않는다.
- 작업 중 commit은 의미 있는 진행 단위일 때만 남긴다.

하나의 branch에 여러 commit이 있어도 된다. 각 commit은 무엇이 달라졌는지 독립적으로 이해할 수 있어야 한다.

## Message

Commit type은 branch type이 아니라 해당 commit의 성격을 따른다. 실행하지 않은 test나 validation을 수행했다고 기록하지 않는다.

## Staging

변경은 논리적 변경 단위로 stage한다.

같은 목적의 변경은 함께 포함하고, 다른 목적의 변경은 별도 commit으로 분리한다. File 단위로 기계적으로 나누지 않으며, 관련 없는 변경은 포함하거나 되돌리지 않는다.

## History

Review가 시작된 commit history는 합의 없이 rewrite하지 않는다. History를 단순하게 유지할 필요가 있으면 merge 시 squash를 사용할 수 있다.

## Agent

- 사용자가 만든 관련 없는 변경을 commit하거나 되돌리지 않는다.
- 사용자의 명시적 요청 없이 amend, rebase, reset 또는 force-push로 공개 history를 바꾸지 않는다.

## Related

- [Branches](branch.md): commit이 속하는 변경 목적과 branch naming
- [Pull Requests](pull-request.md): validation과 review 결과를 전달하는 기준
