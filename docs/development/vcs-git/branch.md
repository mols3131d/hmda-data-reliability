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

기존 branch는 동일 작업의 후속 수정일 때만 재사용한다.

## Inbox Branch

`inbox`는 non-canonical artifact를 지속적으로 저장하는 장기 유지 branch다. Routine inbox artifact에 한해 일반 naming과 pull request delivery의 제한된 예외로 사용한다.

### Scope

직접 commit과 push가 허용되는 범위는 다음뿐이다.

```text
inbox/YYYY-MM-DD/**
inbox/archive/**
```

`inbox/AGENTS.md`, `inbox/README.md`, `inbox/_guidelines/**`, `inbox/_templates/**`와 그 밖의 repository content는 최신 `main`에서 일반 작업 branch를 만들고 Draft Pull Request로 변경한다.

### Delivery

- Routine inbox artifact는 `inbox`에 직접 commit하고 push하며 Pull Request를 만들지 않는다.
- 하나의 commit에는 하나의 artifact 또는 함께 소비되는 하나의 bundle만 포함한다.
- Commit message는 [Commits](commit.md) 규칙을 따른다.
- `inbox` branch 전체를 `main`에 merge하거나 Pull Request로 전달하지 않는다.

### Safety Gate

Routine artifact를 push하기 전에 다음을 모두 확인한다.

1. Local branch와 push destination이 정확히 `inbox`인지 확인한다.
1. Remote `inbox`를 갱신하고 push가 fast-forward인지 확인한다.
1. Remote `inbox` 이후 추가되는 artifact commit의 모든 변경 경로가 허용 범위 안인지 확인한다.
1. Remote가 앞서 있으면 변경을 덮어쓰지 말고 먼저 반영한 뒤 diff와 범위를 다시 검증한다.
1. 허용되지 않은 경로, 예상하지 못한 변경 또는 해결되지 않은 conflict가 있으면 직접 push하지 않는다.

Force-push, remote history rewrite, 다른 작업자의 변경을 덮어쓰기 위한 reset 또는 branch replacement를 사용하지 않는다. Scope가 불명확하면 일반 작업 branch와 Draft Pull Request를 사용한다.

### Main Sync

`main`의 최신 운영 자산을 `inbox`에 반영하는 sync는 routine artifact push와 별도 작업이다.

- Current remote `main`을 `inbox`에 merge하는 방식으로만 sync한다.
- Sync commit에 `main`에서 가져온 변경 외의 수동 수정을 섞지 않는다.
- 다른 repository path가 변경되더라도 해당 내용은 current remote `main`과 동일해야 한다.
- Merge conflict가 발생하면 sync를 중단하며 `inbox`에서 임의로 해결하거나 force-push하지 않는다.
- Sync 후에도 `inbox` content를 `main`으로 역병합하지 않는다.

### Promotion

Inbox content가 채택되면 최신 `main`에서 일반 작업 branch를 만들고 필요한 결론이나 변경만 owning artifact에 다시 작성한다. Inbox file이나 `inbox` branch 자체를 canonical artifact로 승격하지 않는다.

## Agent Instructions

- `agent` actor namespace와 자신의 작업 branch를 사용한다. Routine inbox artifact는 `Inbox Branch` 규칙을 따른다.
- 요청된 변경 목적과 범위만 수정한다.
- `main`, 보호 branch 또는 다른 작업 주체의 branch를 명시적 요청 없이 변경하지 않는다.
- 명시적 요청 없이 force-push, history rewrite 또는 미병합 branch 삭제를 수행하지 않는다.
- 규칙이나 권한이 충돌하면 우회하지 않고 보고한다.

## Related

- [Commits](commit.md): 변경을 commit으로 구성하는 기준
- [Pull Requests](pull-request.md): 변경을 검토와 채택 경계로 전달하는 기준
