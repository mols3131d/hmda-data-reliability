# Branch Strategy Report

> Snapshot: 2026-08-02, commit `b757b1a`

## Decision

Project Pivot에는 **사용자 주도 GPT chat 단위의 workspace 분리 + OpenSpec change 단위의 short-lived branch + trunk-based `main`** 전략을 권장한다.

- `main`은 언제나 merge 가능한 상태를 유지한다.
- 하나의 독립 작업은 하나의 사용자 주도 GPT chat과 workspace에서 진행하고, 필요하면 그 작업에 branch/worktree를 배정한다.
- 하나의 OpenSpec change는 하나의 통합 branch가 Research 또는 OpenSpec 준비부터 Implement와 Review까지 운반한다.
- Research, OpenSpec, Implement, Review를 각각 별도 branch로 나누지 않는다.
- agent는 GPT chat 안에서 위임되는 실행 단위다. agent마다 branch나 worktree를 만들지 않는다.
- 작은 commit은 논리 단위로 유지하고, 검증 가능한 상태에서 PR로 `main`에 병합한다.

이 전략은 현재 repository의 RPI artifact 구조와 사용자의 다중 GPT chat 운영 방식에 맞고, GitFlow의 release/develop/hotfix branch 운영 비용을 추가하지 않는다.

## Chat And Agent Are Different

GPT chat과 agent는 같은 작업 주체가 아니다. branch/worktree의 단위도 둘을 구분해 결정해야 한다.

| 주체 | 역할 | 사용자 의존성 | Git/workspace 권한 |
| --- | --- | --- | --- |
| GPT chat | 사용자가 목표와 우선순위를 정하고 여러 단계의 작업을 조정하는 협업 workspace | 반드시 사용자가 참여하고 판단한다 | 독립 작업이면 branch와 worktree를 배정할 수 있다 |
| Agent | GPT chat이 위임한 한정된 실행 단위 | 부모 GPT chat의 scope와 결정에 의존한다 | 기본적으로 branch/worktree를 만들거나 merge하지 않는다 |

따라서 3개의 GPT chat을 동시에 운용한다면 서로 다른 작업은 3개의 workspace로 분리할 수 있다. 한 GPT chat 안에서 3개의 agent를 사용하는 경우에는 기본적으로 하나의 workspace와 하나의 작업 branch를 공유한다.

```text
GPT chat A ── workspace A ── branch/worktree A
  ├── agent: research
  ├── agent: test
  └── agent: implementation

GPT chat B ── workspace B ── branch/worktree B
  └── agent: documentation
```

GPT chat이 직접 조정하지 않는 agent 전용 branch를 늘리면 context handoff와 integration 비용만 증가한다.

## Current Snapshot

| 항목 | 관찰된 상태 | 근거 |
| --- | --- | --- |
| 현재 branch | `main` | `git status --short --branch` |
| local HEAD | `b757b1a` | `git log` |
| remote tracking | `origin/main` | local branch metadata |
| local delivery gap | `main`이 `origin/main`보다 8 commits 앞섬 | Git status snapshot |
| 등록된 주요 local branch | `agents/model-inquiry`, `feature/foundation`, `pivot/hmda-loans`, `refactor/incident-lifecycle` | `git branch -a -vv` |
| active change evidence | `openspec/changes/hmda-eda-foundation-extension/` | repository tree와 최근 commit |
| RPI phase artifact | Research, OpenSpec, Implement, Review가 서로 다른 artifact owner를 가짐 | `.agents/skills/pivot-openspec-rpi/references/workflow.md` |
| branch protection / PR 상태 | 확인하지 못함 | GitHub remote metadata와 local Git만 확인 가능 |

`main`이 remote보다 앞서 있다는 것은 local commit이 아직 remote에 push되지 않았다는 뜻이지, release readiness나 Review approval을 뜻하지 않는다.

## Recommended Model

```text
main
  └── change/<openspec-change-id>
        ├── Research artifact
        ├── OpenSpec proposal/design/spec/tasks
        ├── implementation + tests
        └── Review artifact
```

### Branch Naming

| 목적 | Pattern | Example |
| --- | --- | --- |
| 일반 OpenSpec change | `change/<change-id>` | `change/hmda-eda-foundation-extension` |
| 긴급 결함 수정 | `fix/<short-topic>` | `fix/hmda-state-null-cast` |
| 외부 사실 검증만 필요한 임시 조사 | `research/<research-id>` | `research/hmda-source-contract` |
| 문서·설정처럼 OpenSpec이 불필요한 단순 변경 | `docs/<short-topic>` 또는 `chore/<short-topic>` | `docs/test-guidance` |

기본값은 `change/<change-id>`다. `research/*`는 조사 결과가 독립적으로 공유되거나 change 생성 전에 여러 선택지를 비교해야 할 때만 사용한다. 일반적인 RPI 작업에서 research branch를 별도로 만드는 것은 피한다.

## Phase And Branch Ownership

RPI phase는 branch가 아니라 **artifact와 책임의 경계**다.

| Phase | Branch rule | Canonical evidence |
| --- | --- | --- |
| Research | 같은 `change/*` branch에서 수행한다. 독립 조사가 필요할 때만 `research/*`를 임시 사용한다. | `openspec/research/{research-id}/research.md` |
| OpenSpec | 같은 branch에서 proposal, design, spec, tasks를 만든다. | `openspec/changes/{change-id}/` |
| Implement | 같은 branch에서 production code, tests, task state를 변경한다. | source, tests, `tasks.md`, validation output |
| Review | 같은 branch의 diff를 독립적으로 검토한다. | `openspec/reviews/{change-id}/...` |
| Archive | Review가 `approved`일 때 `main`에 병합한 뒤 OpenSpec archive를 수행한다. | archived OpenSpec specification |

Review가 `changes_requested`이면 새 branch를 만들지 말고 원래 `change/*` branch로 돌아간다. `blocked`이면 blocker를 해결할 owner phase로 route한다.

## Working Rules

### 1. Start From Updated `main`

작업 시작 전 `main`을 최신 remote와 맞춘다.

```bash
git switch main
git pull --ff-only origin main
git switch -c change/<change-id>
```

현재 local `main`은 `origin/main`보다 8 commits 앞서 있으므로, 다음 작업 전에 이 local commits를 push하거나 별도 판단을 거쳐 remote에 반영해야 한다. 이미 다른 사람이 remote에 올린 변경을 덮어쓰지 않도록 `push --force`는 사용하지 않는다.

### 2. One GPT Chat, One Write Workspace

서로 독립적인 작업을 동시에 수행하는 GPT chat은 서로 다른 worktree 또는 workspace directory를 사용한다.

```bash
git worktree add ../project-pivot-task-a -b change/task-a main
git worktree add ../project-pivot-task-b -b change/task-b main
```

같은 GPT chat 안의 agent들은 기본적으로 이 workspace를 공유한다. agent가 같은 파일을 동시에 수정해야 하는 경우에만 별도 slice worktree를 만들고, parent GPT chat이 결과를 통합한다.

### 3. One Change, One Integration Branch

하나의 branch에는 하나의 OpenSpec change와 그 change를 검증하는 test·documentation만 둔다. 서로 무관한 change를 같은 branch에서 함께 구현하지 않는다.

### 4. Agent Does Not Own Integration

agent는 기본적으로 branch 생성, push, merge를 결정하지 않는다. 전용 slice worktree가 명시적으로 배정된 경우에는 논리적 commit을 만들 수 있지만, 통합 branch의 rebase·merge·push는 parent GPT chat 또는 지정된 integrator가 소유한다.

### 5. Keep Commits Logical

권장 commit sequence는 다음과 같다.

```text
docs(openspec): define <change>
test(<domain>): add contract tests
feat(<domain>): implement <behavior>
docs(review): record <verdict>
```

문서와 code 이동처럼 함께 있어야만 의미가 있는 변경은 한 commit으로 묶고, 독립 검증 가능한 test·production·docs 변경은 분리한다. 이번처럼 staging을 나누는 방식은 유지한다.

### 6. Merge Only With Evidence

`main` 병합 전 최소 조건은 다음과 같다.

- active OpenSpec tasks와 실제 diff가 일치한다.
- focused validation이 실행되었다.
- 필요한 경우 전체 test, lint, type check, OpenSpec validation이 실행되었다.
- Review artifact가 `approved`다.
- remaining risk와 미실행 validation이 handoff에 기록되어 있다.

test pass만으로 merge를 승인하지 않는다. Review status와 OpenSpec task state를 함께 확인한다.

## Merge Policy

### 기본 병합

**PR 기반 fast-forward 또는 rebase merge**를 권장한다.

- logical commit history를 보존한다.
- branch가 오래 살아 divergence가 생기면 PR 전에 `main`을 rebase한다.
- merge commit을 무조건 만들지 않는다.
- squash merge는 작은 단일 문서 수정처럼 commit history 보존 가치가 낮은 경우에만 사용한다.

### 보호할 `main` 규칙

GitHub repository에서 다음 보호를 설정하는 것이 좋다.

- direct push 금지 또는 maintainer에게만 허용
- PR 승인 1회 이상
- required status check: focused test, full test 또는 변경 범위에 맞는 CI, lint/type check, OpenSpec validation
- branch가 최신 `main`을 포함해야 merge 허용
- force push와 branch deletion 제한

이 설정은 현재 local repository에서 확인하지 못했으므로, GitHub repository settings에서 별도로 확인해야 한다.

## Parallel Work

동시에 작업할 때는 먼저 GPT chat이 독립적인지 판단한다. 독립적인 GPT chat이면 workspace/worktree를 분리하고, 같은 GPT chat의 agent라면 기본 workspace를 공유한다.

```text
main
  ├── change/hmda-eda-foundation-extension
  └── change/test-observability
```

같은 change를 여러 GPT chat이 동시에 만져야 하면 다음처럼 slice branch/worktree를 만들 수 있다.

```text
change/<change-id>
  ├── change/<change-id>-tests
  └── change/<change-id>-implementation
```

단, slice branch는 기본 전략이 아니다. test chat과 production chat이 서로의 contract를 반복 수정하게 되면 branch를 나누는 이점보다 rebase와 integration 비용이 커진다. 일반적으로는 한 change branch 안에서 test-first 순서를 지키는 편이 낫다.

## Immediate Actions

1. 현재 `main`의 8개 local commits를 검토해 push할 것과 아직 local-only로 둘 것을 분류한다.
1. 다음 non-trivial 작업부터 `change/<openspec-change-id>` branch를 사용한다.
1. GitHub에서 `main` protection과 required checks를 설정한다.
1. PR template 또는 repository guide에 다음 gate를 고정한다: OpenSpec task state, validation command, Review verdict, remaining risk.
1. 오래된 branch는 PR·remote 상태를 확인한 뒤 merge, close, delete 중 하나로 정리한다. 현재 local evidence만으로 삭제하지 않는다.

## Recommendation Summary

**채택할 정책:** `main` 중심 trunk-based development, 독립 GPT chat당 workspace 하나, change당 통합 branch 하나, phase는 artifact로 구분, agent는 통합을 소유하지 않음, logical commit 보존, Review approved 후 PR merge.

**채택하지 않을 정책:** `develop` branch, 장기 release branch, phase별 branch, agent별 branch/worktree, 모든 변경의 squash merge.

## Evidence And Limits

- 확인한 snapshot: 2026-08-02, local HEAD `b757b1a`
- 확인한 source: local Git status, branch metadata, commit graph, Project Pivot RPI workflow, OpenSpec artifact layout
- 실행 확인: local branch inventory와 commit divergence 조회
- 확인하지 못한 항목: GitHub branch protection, open PR, CI required checks, remote branch freshness beyond fetched refs
