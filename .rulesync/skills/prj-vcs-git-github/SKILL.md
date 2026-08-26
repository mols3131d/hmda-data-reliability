---
name: prj-vcs-git-github
description: >-
  Load repository-specific Git and GitHub guidance for branch, commit, Pull Request,
  review, merge, and related VCS work. Select only the guides and templates relevant
  to the current operation, and verify mutable GitHub state when it can change the
  decision. Do not perform the operation itself.
targets: [claudecode, codexcli, antigravity-ide, antigravity-cli]
---

# Git and GitHub Context

Git과 GitHub 작업 전에 현재 operation에 필요한 repository context만 로드한다. 세부 정책과 작성 형식은 아래 source가 소유하며, 이 Skill은 선택만 소유한다.

## Load

| Task | Read |
| --- | --- |
| 작업 종류가 아직 불명확함 | [`docs/development/vcs-git/README.md`](../../../docs/development/vcs-git/README.md) |
| Branch 생성·재사용·운영·삭제 | [`branch.md`](../../../docs/development/vcs-git/branch.md) |
| `inbox/` dedicated branch delivery | [`branch.md`](../../../docs/development/vcs-git/branch.md), [`inbox/_guidelines/branch.md`](../../../inbox/_guidelines/branch.md) |
| Stage 또는 commit | [`commit.md`](../../../docs/development/vcs-git/commit.md), commit message를 작성할 때 [`.gitmessage`](../../../.gitmessage) |
| Amend, rebase, reset, history rewrite | [`commit.md`](../../../docs/development/vcs-git/commit.md), branch 정책이 결정에 영향을 줄 때 [`branch.md`](../../../docs/development/vcs-git/branch.md) |
| Pull Request 생성·갱신 | [`pull-request.md`](../../../docs/development/vcs-git/pull-request.md), body를 작성할 때 [Pull Request template](../../../.github/templates/pull-request.md) |
| Pull Request review | [`pull-request-review.md`](../../../docs/development/vcs-git/pull-request-review.md), review body를 작성할 때 [review template](../../../.github/templates/pull-request-review.md) |
| Ready, close, merge, auto-merge | [`pull-request.md`](../../../docs/development/vcs-git/pull-request.md), review readiness 판단이 필요할 때 [`pull-request-review.md`](../../../docs/development/vcs-git/pull-request-review.md) |
| PR/review optional metadata | [GitHub templates guidance](../../../.github/templates/README.md) |

## Live State

Branch/head, remote history, Pull Request state, checks, approvals, mergeability, protection 또는 ruleset이 판단에 영향을 줄 때만 live GitHub state를 확인한다. Target이나 operation이 materially 바뀌면 필요한 context를 다시 계산한다.

## Boundary

Context loading은 mutation 권한을 부여하지 않는다. Stage, commit, push, branch/PR/review/merge action과 code review·testing 방법론은 해당 작업 capability가 소유한다.
