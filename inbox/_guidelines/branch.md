# Inbox Branch Delivery

`inbox/` 전용 branch delivery 예외를 정의한다. 일반 branch naming, change unit, Pull Request workflow는 [`docs/development/vcs-git/`](../../docs/development/vcs-git/README.md)를 따른다.

## Boundary

이 guide는 dedicated `inbox` branch를 사용하는 제한된 delivery 예외만 소유한다. Artifact ownership은 runtime capability나 저장 편의가 아니라 **현재 작업 context**로 결정한다.

특정 branch나 Pull Request의 작업을 계속하거나 지원하기 위해 생성한 checkpoint, handoff, review, plan과 기타 working artifact는 해당 작업 branch 또는 Pull Request head가 소유한다. 경로가 `inbox/`여도 같은 branch에 저장하고 그 branch에서 소비한다.

Dedicated `inbox` branch는 다음 조건을 **모두** 만족할 때만 사용할 수 있다.

1. 사용자가 standalone working artifact를 `inbox/`에 저장하라고 명시했다.
1. 현재 작업 branch나 Pull Request head가 그 artifact를 소유하지 않는다.
1. Artifact가 특정 branch나 Pull Request 작업의 continuation, handoff 또는 support를 위해 생성된 것이 아니다.

다른 branch나 Pull Request를 조사·리뷰했다는 사실만으로 그 branch가 artifact owner가 되지는 않는다. 반대로 현재 작업의 owner가 이미 정해져 있다면 runtime에 local checkout이 없거나 해당 branch를 직접 사용할 수 없다는 이유로 dedicated `inbox` branch로 우회하지 않는다. Owning branch에 전달할 수 없으면 limitation을 보고한다.

## Delivery

- Dedicated `inbox` branch를 사용하는 경우에만 요청된 `inbox/YYYY-MM-DD/**` standalone artifact를 Pull Request 없이 direct push할 수 있다. `AGENTS.md`, `README.md`, `_guidelines/`, `_templates/` 같은 운영 자산은 이 예외에 포함하지 않는다.
- 현재 작업 branch나 Pull Request head가 artifact를 소유하면 명시적 요청이 없는 한 그 branch에 함께 두고 정상 branch/Pull Request workflow를 따른다.
- Delivery guidance는 항상 current default branch의 owning guidance에서 결정한다. Dedicated `inbox` branch는 storage ref이며 그 안의 오래된 guidance copy를 authority로 사용하지 않는다.
- Direct push 직전에 remote `inbox` state를 다시 확인하고 기존 output을 보존한다. Conflict는 최신 state에서 요청된 artifact만 다시 적용해 해결하며 force-update나 history rewrite를 사용하지 않는다.
- Dedicated `inbox` branch가 없을 때만 current remote `main`에서 생성할 수 있다. `main`을 `inbox`에 sync하거나 `inbox`를 `main`이나 다른 작업 branch로 merge, rebase, cherry-pick하지 않는다.

## Related

- [Inbox](../AGENTS.md): artifact content, structure와 lifecycle
- [Branches](../../docs/development/vcs-git/branch.md): 일반 branch 정책
- [Pull Requests](../../docs/development/vcs-git/pull-request.md): 일반 Pull Request 정책
