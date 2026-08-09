# Branches

브랜치는 하나의 변경 목적을 격리하고 검토 가능한 단위로 전달한다.

Research, Plan, Implementation, Review는 branch 구조가 아니라 artifact와 commit으로 구분한다.

## Application

인간은 변경의 맥락과 위험에 따라 이 기준을 유연하게 적용할 수 있다. Agent는 `Agent Instructions` section의 제약을 따른다.

Repository protection, security policy와 권한은 항상 우선한다.

## Naming

```text
[<actor>/]<type>/<topic>
```

| Part | Meaning |
| --- | --- |
| `actor` | 작업 주체를 구분하는 optional namespace |
| `type` | 변경 성격 |
| `topic` | 변경 목적 |

Agent는 actor namespace로 `agent`를 사용한다. 인간은 특별한 구분이 필요하지 않다면 actor를 생략할 수 있다.

```text
feat/reliability-profile
mols/feat/reliability-profile
agent/docs/vcs-git-guides
agent/feat/review-engine
```

Type은 [`.gitmessage`](../../../.gitmessage)의 Conventional Commit type을 사용한다. Topic은 소문자 kebab-case로 변경 목적을 표현한다.

## Change Unit

하나의 branch는 함께 검토하고 병합하며 되돌릴 수 있는 하나의 변경 목적을 가진다.

같은 목적의 spec, 문서, test와 구현은 같은 branch에서 함께 변경할 수 있다. 독립적으로 검토하거나 되돌릴 새 목적은 별도의 branch와 pull request로 분리한다.

## Base And Reuse

작업 branch는 원칙적으로 원격 저장소의 현재 `main` head에서 생성한다. 별도의 기준 branch가 지정되면 해당 branch를 사용한다.

기존 branch는 동일 작업의 후속 수정일 때만 재사용한다. `inbox`와 `inbox-promotion`은 반복되는 동일 운영 목적을 위해 유지하는 예외 branch다.

## Inbox Branch

`inbox`는 non-canonical artifact를 지속적으로 생성하고 보관하는 장기 유지 branch다. Routine inbox artifact에만 일반 naming과 pull request delivery의 예외를 허용한다.

작업에 계속 유용한 inbox artifact는 선택적으로 `main:/inbox/**`에 승격할 수 있으며, 위치와 관계없이 non-canonical 상태를 유지한다.

`inbox` branch가 없으면 current remote `main`에서 한 번 생성한다.

### Direct Push

허용 경로:

```text
inbox/YYYY-MM-DD/**
inbox/archive/**
```

- Routine artifact는 `inbox`에 직접 commit하고 push하며 Pull Request를 만들지 않는다.
- 하나의 commit에는 하나의 artifact 또는 함께 소비되는 하나의 bundle만 포함한다.
- Routine artifact push에는 routine artifact commit만 포함한다.
- Commit message는 [Commits](commit.md) 규칙을 따른다.
- 그 밖의 경로는 최신 `main`에서 일반 작업 branch와 Draft Pull Request로 변경한다.

Push 전에는 다음을 확인한다.

1. Local branch와 push destination이 모두 `inbox`다.
1. Remote `inbox`를 갱신했고 push가 fast-forward다.
1. Push에 포함된 모든 commit의 변경 경로가 허용 범위 안이다.
1. 예상하지 못한 변경이나 unresolved conflict가 없다.

Remote가 앞서 있으면 먼저 반영하고 다시 검증한다. Force-push, remote history rewrite, 다른 작업자의 변경을 덮어쓰기 위한 reset 또는 branch replacement는 금지한다. Scope가 불명확하면 일반 작업 branch와 Draft Pull Request를 사용한다.

### Main Sync

`main`의 최신 운영 자산은 routine artifact push와 분리된 sync push로 current remote `main`을 merge해 반영한다.

- Sync commit에 수동 수정이나 routine artifact 변경을 섞지 않는다.
- Sync push에는 sync commit만 포함한다.
- Merge conflict가 발생하면 중단한다.
- Sync는 `inbox` content를 `main`에 반영하는 근거가 아니다.

### Promotion

현재 또는 후속 작업의 근거로 유지할 가치가 있는 inbox artifact는 `main:/inbox/**`에 승격할 수 있다.

승격에는 장기 유지 branch `inbox-promotion` 하나만 사용한다. Artifact, 날짜 또는 승격 요청마다 새 branch를 만들지 않는다.

```text
inbox ── select artifact ──> inbox-promotion ── Draft PR ──> main
                                  ▲                         │
                                  └──── fast-forward ───────┘
```

`inbox-promotion`이 없으면 current remote `main`에서 한 번 생성한다. Promotion Pull Request가 열려 있지 않은 idle 상태에서는 `inbox-promotion`이 `main`과 같은 history를 가리켜야 한다.

#### Promotion Cycle

1. 열린 promotion Pull Request와 `main`에 없는 기존 promotion commit이 없는지 확인한다.
1. `inbox-promotion`을 current remote `main`으로 fast-forward한다. Fast-forward할 수 없으면 중단한다.
1. `inbox`에서 이번 batch에 승격할 artifact만 같은 경로로 가져온다.
1. `main`에 같은 path가 이미 있으면 비교한다. 내용이 같으면 제외하고, 다르면 의도한 갱신인지 확인한 뒤 포함한다.
1. 함께 검토할 artifact를 하나의 promotion batch로 commit하고 Draft Pull Request 하나를 연다.
1. Promotion Pull Request는 merge commit 방식으로 병합한다. Squash 또는 rebase merge는 장기 branch 재사용 history를 깨뜨리므로 사용하지 않는다.
1. Merge 후 `inbox-promotion`을 새 `main` merge commit으로 fast-forward해 다시 idle 상태로 만든다.

Promotion Pull Request는 동시에 하나만 유지한다. 이미 열려 있으면 같은 review scope의 artifact만 현재 batch에 추가하고, 독립적인 승격은 기존 batch가 끝난 뒤 시작한다.

승격 대상으로 허용하는 경로는 routine artifact 경로와 같다.

```text
inbox/YYYY-MM-DD/**
inbox/archive/**
```

`inbox/AGENTS.md`, `inbox/_guidelines/**`, `inbox/_templates/**`는 운영 자산이며 promotion artifact가 아니다.

- 필요한 artifact만 선택적으로 가져오며 `inbox` branch 자체를 `main`에 merge하지 않는다.
- Promotion branch에는 선택한 inbox artifact와 필요한 `main` synchronization 외의 변경을 포함하지 않는다.
- Source code, canonical document, configuration 또는 승격과 무관한 수정은 포함하지 않는다.
- Artifact 내용을 크게 고쳐야 하면 먼저 `inbox`에서 개선한 뒤 그 결과를 승격한다.
- Pull Request가 열린 뒤 `main` 변경을 반영해야 할 때는 scope 변경 없이 `main`을 merge한다. Conflict가 발생하면 자동으로 의미를 결정하지 않고 중단한다.
- Force-push, history rewrite와 branch replacement는 금지한다.
- 승격된 artifact도 non-canonical이다.
- Canonical contract와 결정은 owning artifact에 자족적으로 기록한다. Inbox artifact는 근거로 참조할 수 있지만 규범적 내용을 대신 소유하지 않는다.
- 내용이 canonical contract나 결정으로 채택되면 필요한 부분을 owning artifact에 다시 작성한다.
- 독립적인 작업·근거 가치가 사라진 promoted artifact는 삭제하거나 archive한다.

## Agent Instructions

- `agent` actor namespace와 자신의 작업 branch를 사용한다. Routine inbox artifact와 inbox promotion은 `Inbox Branch` 규칙을 따른다.
- 요청된 변경 목적과 범위만 수정한다.
- `main`, 보호 branch 또는 다른 작업 주체의 branch를 명시적 요청 없이 변경하지 않는다.
- 명시적 요청 없이 force-push, history rewrite 또는 미병합 branch 삭제를 수행하지 않는다.
- 규칙이나 권한이 충돌하면 우회하지 않고 보고한다.

## Related

- [Commits](commit.md): 변경을 commit으로 구성하는 기준
- [Pull Requests](pull-request.md): 변경을 검토와 채택 경계로 전달하는 기준
