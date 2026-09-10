---
type: review
title: PR 231 Safe Cleanup CLI Review
description: PR #231의 repository cleanup CLI와 회귀 테스트를 삭제 안전성 contract 중심으로 검토한다.
tags:
  - "domain:software-engineering"
  - "capability:repository-cleanup"
  - "git"
  - "safety"
---

# PR 231 Safe Cleanup CLI Review

> [!IMPORTANT]
> **Revise** — cleanup CLI의 기본 fail-closed 방향과 테스트 배치는 적절하지만, 실제 삭제 경계에 acceptance 전 수정이 필요한 안전성 문제가 남아 있다. 특히 `.local/worktrees`와 broad `/tmp` pattern은 의도한 소유 경계를 넘어 데이터를 삭제할 수 있으므로 F1과 F2를 먼저 해소해야 한다.

- **Target** — [PR #231](https://github.com/mols3131d/hmda-data-reliability/pull/231)
- **Revision** — `1bb7a82dfd6548066dcac51a3b69aa34406b49cb..44dcd27ca5b89b85e176da8bc4abe99e8604f93c`
- **Scope** — `scripts/clean.py`, `tests/scripts/test_clean.py`, cleanup 대상 선택·Git tracked 보호·symlink 보호·confirmation 경계와 현재 CI evidence

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 **Major** | `.local/worktrees` 전체가 일반 repository cleanup target이라 linked worktree의 tracked·local state를 root index 보호 없이 재귀 삭제할 수 있다. | `.local/worktrees`를 일반 target에서 제거하거나 Git worktree metadata를 기준으로 등록 worktree를 보존하는 별도 cleanup 경계를 둔다. |
| F2 | 🟠 **Major** | `/tmp` direct child를 이름 pattern만으로 신뢰해 현재 repository와 무관한 matching temporary state도 삭제 대상이 된다. | broad shared pattern을 제거하거나 repository ownership을 검증할 수 있는 marker·namespace 아래로 cleanup 범위를 제한한다. |
| F3 | 🟡 **Minor** | 삭제 직전 safety check가 CLI 시작 시 읽은 동일한 tracked-index snapshot을 재사용해 confirmation 이후 Git state 변경을 보지 못한다. | destructive phase 직전에 tracked index를 다시 읽고 fresh state로 candidate를 재검증하는 regression test를 추가한다. |

## Details

### F1 · Linked worktree를 root tracked index로 보호할 수 없음

🟠 **Major**

#### Locations

- [`scripts/clean.py`](../../scripts/clean.py)
  - `REPO_DIRECTORY_TARGETS`
  - `_load_tracked_index`
  - `_contains_tracked_path`
  - `_delete_candidate`
- [`tests/scripts/test_clean.py`](../../tests/scripts/test_clean.py)
  - `test_repo_discovery_preserves_protected_paths`

#### Evidence

`REPO_DIRECTORY_TARGETS`는 `.local/worktrees` 자체를 고정 삭제 대상으로 포함한다. Repository safety check는 현재 `repo_root`에서 한 번 실행한 `git ls-files --cached` 결과를 `TrackedIndex`로 만들고, candidate 아래에 그 index의 tracked path가 있는지만 검사한다.

Linked worktree는 자신의 worktree/index state를 가지므로 root repository index만으로 `.local/worktrees/<worktree>/...` 내부의 tracked path와 local modification을 보호할 수 없다. 그럼에도 현재 테스트는 `.local/worktrees/worktree/file.txt`를 정상 cleanup candidate에 포함해 이 경계를 허용된 동작으로 고정한다.

#### Impact

`.local/worktrees` 아래에 실제 linked worktree가 존재할 때 `shutil.rmtree()`가 해당 worktree의 tracked files, uncommitted modification과 untracked state를 함께 제거할 수 있다. 삭제 후 Git worktree metadata와 filesystem 상태가 불일치할 가능성도 생긴다.

#### Action

가장 단순한 안전 경계는 `.local/worktrees`를 일반 recursive cleanup target에서 제외하는 것이다. Cleanup이 반드시 필요하다면 `git worktree list --porcelain` 등 Git이 소유하는 metadata로 등록 worktree를 식별하고, active worktree를 보존하는 별도 Git-aware 정책으로 분리한다.

### F2 · `/tmp` pattern이 project ownership을 증명하지 않음

🟠 **Major**

#### Locations

- [`scripts/clean.py`](../../scripts/clean.py)
  - `TMP_PATTERNS`
  - `discover_tmp_targets`
  - `_safety_reason`
- [`tests/scripts/test_clean.py`](../../tests/scripts/test_clean.py)
  - `test_tmp_patterns_match_only_allow_listed_direct_children`

#### Evidence

`discover_tmp_targets`는 temporary root의 direct child 이름이 `test.duckdb*`, `airflow_recon_*`, `pytest-of-*`, `pr*-review*` 중 하나와 일치하는지만 확인한다. Candidate가 현재 repository에서 생성됐는지, repository-specific marker가 있는지, 다른 실행이 사용 중인지 확인하지 않는다.

현재 테스트도 임의의 `pytest-of-user`와 다른 matching 이름을 생성해 모두 정상 삭제 candidate로 기대한다. 따라서 이름만 같은 다른 작업의 temporary state도 동일한 코드 경로로 삭제 대상이 된다.

#### Impact

같은 machine의 다른 repository 또는 동시 실행이 동일한 naming pattern을 사용하면 `--tmp-only --yes` 또는 `--all --yes`가 현재 작업과 무관한 temporary state를 재귀 삭제할 수 있다. 이는 PR 설명의 "project-related `/tmp` artifacts" 경계보다 넓다.

#### Action

Repository가 소유권을 증명할 수 없는 broad root pattern은 삭제 대상에서 제거한다. `/tmp` cleanup이 필요하면 repository-specific namespace 또는 marker를 생성·검증해 그 아래만 제거하도록 범위를 좁힌다.

### F3 · Pre-delete revalidation이 stale Git snapshot을 재사용함

🟡 **Minor**

#### Locations

- [`scripts/clean.py`](../../scripts/clean.py)
  - `main`
  - `_delete_candidate`
  - `_safety_reason`
- [`tests/scripts/test_clean.py`](../../tests/scripts/test_clean.py)
  - tracked-file protection 및 confirmation 관련 tests

#### Evidence

`main`은 cleanup plan을 만들기 전에 tracked index를 한 번 읽고 같은 `TrackedIndex` 객체를 각 `_delete_candidate` 호출에 전달한다. `_delete_candidate`가 safety check를 다시 호출하더라도 Git index 자체를 reload하지 않으므로 plan 출력이나 interactive confirmation 이후의 tracked-state 변경은 반영되지 않는다.

#### Impact

Plan 생성 후 삭제 전에 candidate 내부 파일이 새로 tracked 상태가 되면 pre-delete check가 그 변경을 보지 못하고 기존 candidate를 삭제할 수 있다. 일반적인 단일 사용자 실행에서는 window가 짧지만, destructive utility가 주장하는 tracked-file protection contract에는 명확한 TOCTOU gap이다.

#### Action

Confirmation이 끝난 뒤 destructive phase 진입 직전에 tracked index를 다시 읽고 각 candidate를 fresh state로 재검증한다. Plan 이후 tracked state가 변경된 scenario가 삭제를 차단하는 regression test를 추가한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Exact PR revision inspection | Base `1bb7a82d...`, head `44dcd27c...`; changed files는 `scripts/clean.py`, `tests/scripts/test_clean.py` 2개로 확인했다. |
| ✅ Pass | GitHub `CI Lite` | Workflow run `34344731262`가 성공했다. Python lint·format·type validation이 통과했고 selected test step은 `261 passed`로 완료됐다. |
| ⚪ Not Verified | PR body의 local validation claims | `8 passed`, pre-push `575 passed, 1 skipped`, explicit cleanup 실행은 PR body에 기록되어 있으나 이번 review에서 독립 실행 log를 확인하지 않았다. |
| ⚪ Not Verified | Destructive local reproduction | 데이터 삭제를 동반하는 별도 재현은 실행하지 않았다. Finding은 exact source와 test의 reachable code path를 기준으로 검증했다. |

## Risks and Limits

- 현재 runtime에서는 repository가 권장하는 `review-lead` 기반 독립 dual-perspective orchestration을 사용할 수 없어 동일 context의 직접 review로 수행했다. 이를 독립 review와 동등하게 간주하지 않는다.
- F1~F3의 safety boundary가 수정되면 기존 assessment는 stale해질 수 있으므로 새 head revision을 다시 검토해야 한다.
