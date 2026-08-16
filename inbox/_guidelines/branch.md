# Inbox Branch

이 문서는 dedicated `inbox` branch의 transport와 sync 예외를 소유한다. 일반 branch naming과 변경 단위는 [`docs/development/vcs-git/branch.md`](../../docs/development/vcs-git/branch.md), commit 형식은 [`commit.md`](../../docs/development/vcs-git/commit.md), Pull Request 규칙은 [`pull-request.md`](../../docs/development/vcs-git/pull-request.md)가 소유한다. Inbox artifact의 내용·경로·lifecycle contract는 [`../AGENTS.md`](../AGENTS.md)가 소유한다.

## Role

`inbox`는 [`../AGENTS.md`](../AGENTS.md)가 정의한 routine artifact를 위한 장기 유지 branch 예외다. Branch가 없으면 current remote `main`에서 한 번 생성한다.

## Direct Push

Routine artifact direct push를 허용하는 경로는 다음뿐이다.

```text
inbox/YYYY-MM-DD/**
inbox/archive/**
```

- Routine artifact는 `inbox`에 직접 commit하고 push하며 Pull Request를 만들지 않는다.
- 하나의 commit에는 하나의 artifact 또는 함께 소비되는 하나의 bundle만 포함한다.
- Routine artifact push에는 routine artifact 변경만 포함한다.
- Merge base 기준 `inbox` 고유 content는 위 허용 경로에만 존재해야 한다.
- `inbox/AGENTS.md`, `inbox/README.md`, `inbox/_guidelines/**`, `inbox/_templates/**`는 운영 자산이며 direct push 예외에 포함하지 않는다.
- 운영 자산과 그 밖의 repository content는 최신 `main`에서 일반 작업 branch와 Draft Pull Request로 변경한다.

Push 전에는 다음만 확인한다.

1. Local branch와 push destination이 모두 `inbox`다.
1. Remote `inbox`를 갱신했고 push가 fast-forward다.
1. Push에 포함된 변경이 허용 경로 안에만 있다.
1. 예상하지 못한 변경이나 unresolved conflict가 없다.

Remote가 앞서 있으면 먼저 반영한다. Force-push, remote history rewrite, 다른 작업자의 변경을 덮어쓰기 위한 reset 또는 branch replacement는 금지한다.

## Formatting

Repository-managed automation은 routine artifact push 뒤 변경된 Markdown artifact에 `rumdl fmt`를 적용하고 필요한 formatting change를 `inbox`에 별도 commit할 수 있다.

- Formatting은 content validation gate가 아니라 mechanical normalization이다.
- Formatter는 해당 push에서 변경된 routine artifact만 수정하고 repository의 current Markdown formatter configuration을 따른다.
- 운영 자산이나 다른 repository path를 수정하지 않는다.
- Formatting commit에는 formatter가 만든 변경 외의 내용을 섞지 않는다.
- 동시 update는 직렬화하거나 push 직전 remote `inbox`를 다시 읽어 stale ref를 덮어쓰지 않는다. Force-push는 사용하지 않는다.
- Formatter 실패는 artifact의 의미를 승인하거나 거부하는 판단으로 해석하지 않는다.

Automation이 아직 구성되지 않았거나 일시적으로 실패한 경우에도 routine artifact delivery 자체를 별도 Pull Request로 우회하지 않는다.

## Main Sync

`inbox`가 최신 repository context를 필요로 할 때 `main`을 `inbox`에 merge한다. `main`에서 이 guideline 또는 `inbox/**` 운영 자산이 변경되면 다음 routine artifact 작업 전에 sync한다. 방향은 항상 **`main` → `inbox`**이며, sync를 이유로 `inbox` content를 `main`에 merge하지 않는다.

- Sync commit에는 `main` 반영 외의 변경을 섞지 않는다.
- Conflict나 예상하지 못한 path가 생기면 자동으로 의미를 결정하지 않고 중단한다.
- Force-push, rebase, history rewrite 또는 branch replacement로 sync하지 않는다.
- Routine artifact writer는 `main` sync와 artifact commit을 하나의 commit에 섞지 않는다.

## Main Inbox Index

Index의 의미와 lifecycle은 [`../README.md`](../README.md)와 [`../AGENTS.md`](../AGENTS.md)가 소유한다. 이 section은 `main:/inbox/README.md`의 automation write 예외만 정의한다.

Repository-managed automation은 index 갱신에 한해 `main:/inbox/README.md`를 직접 갱신할 수 있다.

- 변경 대상은 `main:/inbox/README.md` 하나뿐이다.
- Artifact content를 `main`에 복제하지 않는다.
- Routine artifact writer는 artifact 작업의 side effect로 index를 수동 갱신하지 않는다.
- Direct update 직전에 current `main`을 다시 읽고, branch가 이동했으면 최신 `main` 기준으로 index commit을 다시 만든다.
- Force-push는 사용하지 않는다.

Index automation이 아직 구성되지 않았거나 실패한 경우에도 routine artifact delivery는 `inbox` branch에서 완료된 것으로 본다. Automation 자체의 구현과 변경은 일반 Draft Pull Request workflow를 따른다.
