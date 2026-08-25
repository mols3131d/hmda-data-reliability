# Inbox Branch Delivery

`inbox/` 전용 branch delivery 예외를 정의한다. 일반 branch naming, change unit, Pull Request workflow는 [`docs/development/vcs-git/`](../../docs/development/vcs-git/README.md)를 따른다.

## Boundary

이 guide는 dedicated `inbox` branch를 사용하는 제한된 delivery 예외만 소유한다. 이 예외는 actor 이름이 아니라 **delivery context와 artifact ownership**으로 결정한다.

Dedicated `inbox` branch는 다음 조건을 **모두** 만족할 때만 사용할 수 있다.

1. 사용자가 standalone working artifact를 `inbox/`에 저장하라고 명시했다.
1. 기존 작업 branch나 Pull Request가 그 artifact를 소유하지 않는다.
1. 현재 runtime이 일반 작업 branch 없이 remote artifact delivery를 수행한다.

Local working agent처럼 자신의 일반 작업 branch를 사용할 수 있는 runtime은 artifact 저장만을 이유로 dedicated `inbox` branch를 만들거나 전환하지 않는다. 정상 branch/Pull Request workflow를 사용한다.

## Delivery

- Dedicated `inbox` branch를 사용하는 경우에만 요청된 `inbox/YYYY-MM-DD/**` artifact를 Pull Request 없이 direct push할 수 있다. `AGENTS.md`, `README.md`, `_guidelines/`, `_templates/` 같은 운영 자산은 이 예외에 포함하지 않는다.
- 현재 작업 branch나 Pull Request가 artifact를 소유하면 명시적 요청이 없는 한 그 branch에 함께 둔다. 다른 branch나 Pull Request를 조사·리뷰했다는 사실만으로 그 branch가 artifact owner가 되지는 않는다.
- Delivery guidance는 항상 current default branch의 owning guidance에서 결정한다. Dedicated `inbox` branch는 storage ref이며 그 안의 오래된 guidance copy를 authority로 사용하지 않는다.
- Direct push 직전에 remote `inbox` state를 다시 확인하고 기존 output을 보존한다. Conflict는 최신 state에서 요청된 artifact만 다시 적용해 해결하며 force-update나 history rewrite를 사용하지 않는다.
- Dedicated `inbox` branch가 없을 때만 current remote `main`에서 생성할 수 있다. `main`을 `inbox`에 sync하거나 `inbox`를 `main`이나 다른 작업 branch로 merge, rebase, cherry-pick하지 않는다.

## Related

- [Inbox](../AGENTS.md): artifact content, structure와 lifecycle
- [Branches](../../docs/development/vcs-git/branch.md): 일반 branch 정책
- [Pull Requests](../../docs/development/vcs-git/pull-request.md): 일반 Pull Request 정책
