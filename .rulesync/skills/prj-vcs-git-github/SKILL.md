---
name: prj-vcs-git-github
description: >-
  Load repository-specific Git and GitHub workflow context for branch, commit, Pull
  Request, review, merge, and related VCS operations. Use the routing table to read
  only the relevant guides and templates, and resolve live GitHub state when mutable
  repository state can affect the action. Do not perform the VCS operation itself.
targets: [claudecode, codexcli, antigravity-ide, antigravity-cli]
---

# Git and GitHub Context

이 Skill은 Git과 GitHub 작업에 필요한 repository context를 선택해 로드한다. 정책과 형식은 각 guide와 template이 소유하고, 실제 작업 실행은 downstream capability가 소유한다.

## Contract

- 현재 작업을 아래 table의 하나 이상 case로 분류하고 해당 context만 로드한다.
- 여러 case가 동시에 적용되면 필요한 문서를 합치되 이미 읽은 context는 중복 로드하지 않는다.
- Repository guide와 template은 정책과 작성 형식의 authority로, live GitHub state는 branch head, Pull Request 상태, check, protection처럼 변경 가능한 사실의 authority로 사용한다.
- Task intent, target ref 또는 GitHub object가 materially 바뀌면 applicable context를 다시 계산한다.
- Context loading은 mutation 권한을 부여하지 않는다. destructive 또는 finalizing action은 사용자 요청과 applicable guide의 제약을 별도로 따른다.

## Routing

| When | Repository Context | Live GitHub Context |
| --- | --- | --- |
| General Git/GitHub orientation 또는 아직 작업 종류가 불명확함 | [`docs/development/vcs-git/README.md`](../../../docs/development/vcs-git/README.md) | 작업을 분류하는 데 필요한 repository/ref/object만 확인 |
| Branch 생성, 재사용, 운영 또는 삭제 | [`branch.md`](../../../docs/development/vcs-git/branch.md) | base/head, 기존 branch, protection 또는 ruleset이 결정에 영향을 줄 때 확인 |
| `inbox/` dedicated branch delivery | [`branch.md`](../../../docs/development/vcs-git/branch.md), [`inbox/_guidelines/branch.md`](../../../inbox/_guidelines/branch.md) | 대상 branch와 현재 delivery 상태 확인 |
| Stage 또는 commit 작성 | [`commit.md`](../../../docs/development/vcs-git/commit.md), [`.gitmessage`](../../../.gitmessage) | 현재 ref나 staged/remote 상태가 작업 경계에 영향을 줄 때만 확인 |
| Amend, rebase, reset 또는 history rewrite | [`commit.md`](../../../docs/development/vcs-git/commit.md), 필요하면 [`branch.md`](../../../docs/development/vcs-git/branch.md) | 대상 ref, 공개 여부, protection과 remote 상태 확인 |
| Pull Request 생성 또는 갱신 | [`pull-request.md`](../../../docs/development/vcs-git/pull-request.md), [Pull Request template](../../../.github/templates/pull-request.md) | base/head, 기존 PR, checks 또는 protection이 현재 작업에 영향을 줄 때 확인 |
| Pull Request review | [`pull-request-review.md`](../../../docs/development/vcs-git/pull-request-review.md), [review template](../../../.github/templates/pull-request-review.md) | diff, reviews, threads, checks와 필요한 base/head state 확인 |
| Ready 전환, close, merge 또는 auto-merge 등 Pull Request lifecycle | [`pull-request.md`](../../../docs/development/vcs-git/pull-request.md), review 상태 판단이 필요하면 [`pull-request-review.md`](../../../docs/development/vcs-git/pull-request-review.md) | draft/ready state, mergeability, approvals, required checks와 protection 확인 |
| PR 또는 review optional metadata를 작성·보존 | [GitHub templates guidance](../../../.github/templates/README.md) | 기존 metadata가 있으면 현재 revision과 함께 확인 |

## Boundary

- 이 Skill은 stage, commit, push, branch mutation, review action, merge 또는 다른 GitHub mutation을 직접 소유하지 않는다.
- Code review methodology는 `prj-review-code`, test context는 `prj-load-context-testing`처럼 별도 Skill이 선택될 수 있다.
- 작업과 무관한 VCS 문서나 GitHub object를 미리 전부 읽지 않는다.
