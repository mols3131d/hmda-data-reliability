# Branches

브랜치는 하나의 변경 목적을 격리하고 검토 가능한 단위로 전달한다. Research, Plan, Implementation, Review는 branch 구조가 아니라 artifact와 commit으로 구분한다.

## Application

인간은 변경의 맥락과 위험에 따라 이 기준을 유연하게 적용할 수 있다. Agent는 `Agent Instructions` section의 제약을 따른다.

Repository protection, security policy와 권한은 항상 우선한다.

## Change Unit

하나의 branch는 함께 검토하고 병합하며 되돌릴 수 있는 하나의 변경 목적을 가진다.

같은 목적의 spec, 문서, test와 구현은 같은 branch에서 함께 변경할 수 있다. 독립적으로 검토하거나 되돌릴 새 목적은 별도의 branch와 Pull Request로 분리한다.

## Base And Reuse

작업 branch는 원칙적으로 원격 저장소의 현재 `main` head에서 생성한다. 별도의 기준 branch가 지정되면 해당 branch를 사용한다.

기존 branch는 동일 작업의 후속 수정일 때만 재사용한다.

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

`type`은 [`.gitmessage`](../../../.gitmessage)의 Conventional Commit type을 사용한다. `topic`은 변경 목적을 소문자 kebab-case로 표현한다.

## Standalone Inbox Delivery

Standalone `inbox/` artifact delivery는 actor 이름이 아니라 **delivery context와 artifact ownership**으로 결정하는 제한된 예외다.

Dedicated `inbox` branch는 다음 조건을 **모두** 만족할 때만 사용할 수 있다.

1. 사용자가 standalone working artifact를 `inbox/`에 저장하라고 명시했다.
2. 기존 작업 branch나 Pull Request가 그 artifact를 소유하지 않는다.
3. 현재 runtime이 일반 작업 branch 없이 remote artifact delivery를 수행한다.

Delivery에는 다음 규칙을 적용한다.

- Local working agent처럼 자신의 일반 작업 branch를 사용할 수 있는 runtime은 artifact 저장만을 이유로 dedicated `inbox` branch를 만들거나 전환하지 않는다. 정상 branch/Pull Request workflow를 사용한다.
- Dedicated `inbox` branch를 사용하는 경우에만 요청된 `inbox/YYYY-MM-DD/**` artifact를 Pull Request 없이 direct push할 수 있다. `AGENTS.md`, `README.md`, `_guidelines/`, `_templates/` 같은 운영 자산은 이 예외에 포함하지 않는다.
- 현재 작업 branch나 Pull Request가 artifact를 소유하면 명시적 요청이 없는 한 그 branch에 함께 둔다. 다른 branch나 Pull Request를 조사·리뷰했다는 사실만으로 그 branch가 artifact owner가 되지는 않는다.
- Delivery guidance는 항상 current default branch의 owning guidance에서 결정한다. Dedicated `inbox` branch 안의 오래된 guidance copy를 authority로 사용하지 않는다.
- Direct push 직전에 remote `inbox` state를 다시 확인하고 기존 output을 보존한다. Conflict는 최신 state에서 요청된 artifact만 다시 적용해 해결하며 force-update나 history rewrite를 사용하지 않는다.
- Dedicated `inbox` branch가 없을 때만 current remote `main`에서 생성할 수 있다. `main`을 `inbox`에 sync하거나 `inbox`를 `main`이나 다른 작업 branch로 merge, rebase, cherry-pick하지 않는다.

## Agent Instructions

- `agent` actor namespace와 자신의 작업 branch를 사용한다.
- 요청된 변경 목적과 범위만 수정한다.
- `main`, 보호 branch 또는 다른 작업 주체의 branch를 명시적 요청 없이 변경하지 않는다.
- `Standalone Inbox Delivery`의 remote delivery 조건을 충족하는 경우에만 dedicated `inbox` branch direct push 예외를 사용한다.
- 명시적 요청 없이 force-push, history rewrite 또는 미병합 branch 삭제를 수행하지 않는다.
- 규칙이나 권한이 충돌하면 우회하지 않고 보고한다.

## Related

- [Commits](commit.md): 변경을 commit으로 구성하는 기준
- [Pull Requests](pull-request.md): 변경을 검토와 채택 경계로 전달하는 기준
