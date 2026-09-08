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

## Acceptance

- configured target Skill directory는 보존한다.
- config/lock에 없는 stale target Skill directory는 `generate` 전후 모두 제거한다.
- target root 밖의 directory와 비-Skill projection은 삭제하지 않는다.
- Rulesync generate 실패 시에도 의도하지 않은 삭제가 발생하지 않는다.
- 기존 `preview`, `check`, `doctor`, `validate`와 Claude bridge 동작을 불필요하게 변경하지 않는다.
