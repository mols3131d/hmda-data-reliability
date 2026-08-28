---
name: prj-vcs-git-github
description: >-
  Load repository-specific Git and GitHub guidance for branch, commit, Pull Request,
  review, merge, and related VCS work. Select only the guides and templates relevant
  to the current operation, and verify mutable GitHub state when it can change the
  decision. Do not perform the operation itself.
---

# Git and GitHub Context

Git과 GitHub 작업 전에 필요한 repository context만 로드한다. 세부 정책과 작성 형식은 아래 source가 소유하고, 이 Skill은 선택만 소유한다.

## Load

| Task | Read |
| --- | --- |
| 작업 종류가 아직 불명확함 | [`docs/development/vcs-git/README.md`](../../../docs/development/vcs-git/README.md) |
| Branch 작업 | [`branch.md`](../../../docs/development/vcs-git/branch.md); `inbox/` dedicated delivery면 [`inbox/_guidelines/branch.md`](../../../inbox/_guidelines/branch.md)도 읽음 |
| Stage, commit, amend, rebase, reset, history rewrite | [`commit.md`](../../../docs/development/vcs-git/commit.md); commit message를 작성하면 [`.gitmessage`](../../../.gitmessage), branch 정책이 판단에 영향을 주면 [`branch.md`](../../../docs/development/vcs-git/branch.md)도 읽음 |
| Pull Request 생성·갱신·lifecycle | [`pull-request.md`](../../../docs/development/vcs-git/pull-request.md); body를 작성하면 [Pull Request template](../../../.github/templates/pull-request.md)도 읽음 |
| Pull Request review | [`pull-request-review.md`](../../../docs/development/vcs-git/pull-request-review.md); review body를 작성하면 [review template](../../../.github/templates/pull-request-review.md)도 읽음 |
| PR/review optional metadata | [GitHub templates guidance](../../../.github/templates/README.md) |

## Live State

Branch/head, remote history, Pull Request state, checks, approvals, mergeability, protection 또는 ruleset이 판단에 영향을 줄 때만 live GitHub state를 확인한다. Target이나 operation이 바뀌면 필요한 context를 다시 계산한다.

## Boundary

Context loading은 mutation 권한을 부여하지 않는다. 실제 Git/GitHub action과 code review·testing 방법론은 해당 작업 capability가 소유한다.
