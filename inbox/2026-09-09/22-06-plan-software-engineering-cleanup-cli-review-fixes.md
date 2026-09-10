---
type: plan
title: PR 231 cleanup CLI review fixes
description: PR 231 Inbox 리뷰의 F1~F3 안전성 finding을 수정하기 위한 구현 계획과 observable test contract입니다.
tags:
  - "domain:software-engineering"
  - "capability:repository-cleanup"
  - "safety"
---

# PR 231 cleanup CLI review fixes

## Decision

Inbox 리뷰의 F1~F3를 모두 수용한다. 기존 Draft PR #231의 변경 목적과 branch를 유지하고, cleanup 범위를 넓히지 않는 fail-closed 수정으로 처리한다.

## Safety contract

| Finding | Change | Observable contract |
| --- | --- | --- |
| F1 | `.local/worktrees`를 일반 repository cleanup discovery와 traversal에서 제외한다. | linked worktree의 파일은 cleanup candidate가 되지 않는다. |
| F2 | 기존 `/tmp` pattern은 discovery와 dry-run 보고에는 남기되, repository ownership marker가 없는 대상은 기본적으로 skip한다. Legacy residue는 `--allow-unowned-tmp`와 별도 confirmation을 모두 요구한다. | 다른 작업의 matching `/tmp` state는 기본 삭제되지 않으며, marker는 현재 repository root와 일치해야 한다. |
| F3 | confirmation 이후 destructive phase 직전에 Git tracked index를 다시 읽는다. | plan 생성 이후 tracked 상태가 바뀌면 candidate 삭제가 차단된다. |

## Test scenarios

- marker가 있는 project `/tmp` pattern은 candidate가 되고 marker가 없는 matching path는 skipped target이 된다.
- explicit `--allow-unowned-tmp` 없이는 legacy `/tmp` pattern을 삭제하지 않는다.
- `.local/worktrees` 아래 파일은 discovery 대상이 아니며 보존된다.
- confirmation 이후 fresh Git index가 candidate를 tracked path로 보고하면 파일/디렉토리를 삭제하지 않는다.
- 기존 protected path, symlink, dry-run과 explicit deletion contract는 유지된다.

## Validation gates

1. `uv run pytest tests/scripts/test_clean.py`
1. `uv run ruff check scripts/clean.py tests/scripts/test_clean.py`
1. changed Python format/type checks
1. 실제 `--dry-run` 및 marker 없는 system `/tmp` 대상의 fail-closed 동작 확인
1. diff review와 Draft PR 갱신

이 문서는 Inbox working artifact이며 `scripts/clean.py`와 `tests/scripts/test_clean.py`의 구현·test가 canonical executable contract다.
