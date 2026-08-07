# Inbox Branch

`inbox` branch는 `inbox/`의 non-canonical artifact를 지속적으로 저장하기 위한 장기 유지 branch다.

기본 Git 운영은 [Branches](../../docs/development/vcs-git/branch.md), [Pull Requests](../../docs/development/vcs-git/pull-request.md), [Commits](../../docs/development/vcs-git/commit.md)를 따른다. 이 문서는 routine inbox artifact에 필요한 제한된 예외만 정의한다.

## Scope

직접 commit과 push가 허용되는 범위는 다음뿐이다.

```text
inbox/YYYY-MM-DD/**
inbox/archive/**
```

다음 운영 자산과 다른 repository content는 직접 push 대상이 아니다.

```text
inbox/AGENTS.md
inbox/README.md
inbox/_guidelines/**
inbox/_templates/**
```

이 범위를 변경해야 하면 최신 `main`에서 일반 작업 branch를 만들고 Draft Pull Request로 전달한다.

## Delivery

- Routine inbox artifact는 `inbox` branch에 직접 commit하고 push한다. Pull Request는 만들지 않는다.
- 하나의 commit에는 하나의 artifact 또는 함께 소비되는 하나의 bundle만 포함한다.
- Commit message는 repository commit 규칙을 따른다.
- `inbox` branch 전체를 `main`에 merge하거나 Pull Request로 전달하지 않는다.

## Safety Gate

직접 push 전에 다음을 모두 확인한다.

1. 현재 target branch가 정확히 `inbox`인지 확인한다.
1. Remote `inbox`를 갱신하고 push가 fast-forward인지 확인한다.
1. Push 대상 diff의 모든 경로가 허용 범위 안인지 확인한다.
1. Remote가 앞서 있으면 먼저 변경을 반영한 뒤 diff와 범위를 다시 검증한다.
1. 허용되지 않은 경로, 예상하지 못한 변경 또는 해결되지 않은 충돌이 있으면 직접 push하지 않는다.

- Force-push하거나 remote history를 rewrite하지 않는다.
- 다른 작업자의 변경을 덮어쓰기 위해 reset, branch replacement 또는 강제 갱신을 사용하지 않는다.
- Scope가 불명확하면 예외를 확대하지 말고 일반 작업 branch와 Draft Pull Request를 사용한다.

## Sync

`main`의 inbox 운영 규칙을 반영해야 하면 remote history를 rewrite하지 않는 방식으로 `main`의 변경을 `inbox`에 반영한다. 이 sync는 inbox content의 promotion을 의미하지 않는다.

## Promotion

Inbox content가 채택되면 최신 `main`에서 일반 작업 branch를 만들고 필요한 결론이나 변경만 owning artifact에 다시 작성한다.

Inbox file이나 `inbox` branch 자체를 canonical artifact로 승격하지 않는다.
