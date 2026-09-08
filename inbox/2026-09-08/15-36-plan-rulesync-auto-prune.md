---
type: plan
title: "Rulesync target skill projection auto-prune"
description: "rulesync.py generate 전후 stale target Skill directory를 안전하게 정리하는 구현 계획"
tags:
  - rulesync
  - agent-assets
  - prune
---

# Rulesync Target Skill Projection Auto-Prune

## Goal

`rulesync.py`가 `rulesync.jsonc`와 `rulesync.lock`에 선언되지 않은 target Skill directory를 `generate` 전후에 감지하고 자동 정리한다.

## Boundaries

- In scope: `scripts/rulesync.py`, 그 동작을 검증하는 `tests/scripts`와 이 plan/checkpoint artifact
- Out of scope: Rulesync source/lock 직접 수정, generated projection 수동 편집, unrelated asset cleanup
- PR은 Draft 상태로 유지하며 human review·approval·merge는 수행하지 않는다.

## Loop Plan

1. Research — config/lock schema, target path와 기존 `generate`/`validate` flow를 확인한다.
1. Plan — 삭제 허용 boundary, before/after detection, failure semantics와 regression matrix를 확정한다.
1. Work — observable contract를 먼저 test로 고정하고 최소 구현을 추가한다.
1. Review — focused test, related suite, lint/format와 diff safety를 검증한다.

## Initial State

- Branch: `agents/rulesync-auto-prune-script-addition`
- Base: `origin/main` at `6340fe4fc7f671f7d6ae3a67dbe921a956de1111`
- PR-first: 이 artifact를 initial commit으로 게시한 뒤 Draft PR을 생성한다.

## Research

- `scripts/rulesync.py`는 Rulesync `generate`를 직접 호출하며, `install/update`도 내부에서 같은 generate 경로를 재사용한다.
- repository generated Skill roots는 `.agents/skills`, `.claude/skills`, `.github/skills`다. 각 root의 직접 자식 중 `SKILL.md`를 가진 실제 directory만 prune 후보로 본다.
- 보존 이름은 canonical local `.rulesync/skills/<name>/SKILL.md`(외부 curated subtree 제외), `rulesync.jsonc` source skill names와 `rulesync.lock` source skill keys의 union으로 계산한다.
- name 비교는 target filesystem 차이를 고려해 case-insensitive로 한다. symlink와 `SKILL.md`가 없는 directory는 보존한다.
- `preview`와 `check`는 inspection-oriented public action이므로 prune하지 않는다. generate가 실패하면 after-prune도 실행하지 않는다.
- Current Rulesync documentation도 `generate --delete`를 설명하지만, 이 작업은 version-sensitive CLI flag에 의존하지 않고 repository가 소유한 narrow target-root boundary를 유지한다.

## Plan

- `generate` 호출 전 stale 후보를 관찰하고 호출 후 다시 관찰한다.
- generate 성공 시 두 관찰 결과의 union만 삭제한다. generate failure, unreadable config/lock/source 또는 symlink boundary에서는 삭제하지 않는다.
- optional `skills-lock.json`의 valid external Skill names는 expected set에 포함하고, 그 lock이 invalid하거나 unsafe하면 삭제하지 않는다.
- projection root와 canonical source의 symlink/junction ancestor는 안전한 repository boundary로 인정하지 않는다.
- 기존 `_sync_sources`, Claude bridge와 `_validate` return-code ordering은 유지한다.

## Test Matrix

- stale Skill directory는 세 generated roots에서 제거된다.
- local/config/lock에 선언된 Skill은 보존된다.
- non-Skill directory와 symlink는 보존된다.
- generate failure에서는 stale directory가 보존되고 failure code가 전달된다.
- generate 전후 detection과 `install/update → generate` forwarding 순서를 검증한다.
- projection root ancestor symlink, canonical source symlink/non-directory/child symlink와 Skills CLI lock ownership을 검증한다.

## Loop Progress

| Loop | Transition | Result |
| ---: | --- | --- |
| 1 | Review → artifact | 세 material safety/ownership findings를 `review` artifact에 기록 |
| 2 | Apply → focused Review | boundary/source/Skills CLI 보강과 회귀 테스트 적용; focused tests 17 passed |
| 3 | Validate → safety refinement | `tests/scripts` 66 passed, artifact validator 통과; `lstat()` 기반 fail-closed refinement 추가 |
| 4 | Apply → final Review | non-directory source regression 추가; 정적 검사와 전체 scripts suite 재통과 |

## Current Handoff

- Implementation: local working tree에 safety/ownership remediation과 regression tests가 반영됐다.
- Validation: `tests/scripts` 66 passed, 1 Windows-only test skipped; changed files의 Ruff/format/ty/diff check 통과.
- Artifact: `17-48-review-rulesync-auto-prune.md`에 최종 verdict와 remaining risks 기록.
- Delivery: commit `60ea6bd`를 branch와 PR #223에 publish했고, PR 제목/본문을 implementation·validation 상태로 갱신했다. PR은 Draft로 유지한다.

## Acceptance

- configured target Skill directory는 보존한다.
- config/lock에 없는 stale target Skill directory는 `generate` 전후 모두 제거한다.
- target root 밖의 directory와 비-Skill projection은 삭제하지 않는다.
- Rulesync generate 실패 시에도 의도하지 않은 삭제가 발생하지 않는다.
- 기존 `preview`, `check`, `doctor`, `validate`와 Claude bridge 동작을 불필요하게 변경하지 않는다.
