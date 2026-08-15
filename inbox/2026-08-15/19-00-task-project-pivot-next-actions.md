---
type: task
title: Project Pivot 다음 작업 정리
description: 2026-08-14~15 Inbox Brief Summary를 실행 가능한 우선순위와 완료 조건으로 정리한다.
status: open
source: https://app.notion.com/p/3bd13d7e58b98196b078f7828423e4da
---

> [!NOTE]
> 현재 가장 작은 고가치 작업은 완료된 `null_spike` Reliability Change의 archive readiness를 확인하고 lifecycle을 마감하는 것이다. 기존 validation 수치는 historical snapshot이므로 current `HEAD` 실행 결과로 표현하지 않는다.

## Now

### 1. `null_spike` archive readiness 확인 및 archive

- [x] 마지막 구현 revision과 final validation evidence의 대상 revision이 일치하는지 확인한다.
- [x] `tasks 24/24 완료`와 Self-Review 완료 상태를 OpenSpec Change 기록에서 다시 확인한다.
- [x] `reliability-null-spike-recovery-vertical-slice`에 남은 미완료 task, unresolved finding, 후속 필수 문서가 없는지 확인한다.
- [x] readiness가 충족되면 OpenSpec Change를 archive한다.
- [x] archive 후 active Change 목록에서 해당 Change가 사라지고 archive 결과가 보존되는지 확인한다.

**완료 조건:** archive 전후 상태와 근거가 확인되고, 완료된 Change가 active 상태로 남지 않는다.

**Archive evidence:** `4fb6299`가 마지막 null-spike 구현/test merge revision이며, source/test 변경 없이 descendant인 current `HEAD` `8a3c2c7`에서 focused test `34 passed`, default pytest `212 passed`, `ty check`와 relevant Ruff/format/rumdl을 재실행했다. 전체 repository Ruff/format/rumdl에는 이번 Change와 무관한 기존 baseline issue가 남아 있어 pass로 기록하지 않았다. `openspec validate --all --strict`는 archive 전 `17/17`, archive 후 `16/16` 통과했다. Archive 결과는 `openspec/changes/archive/2026-08-15-reliability-null-spike-recovery-vertical-slice/`에 보존됐고 active Change 목록은 비었다.

## Next

### 2. Foundation Non-Gating Inventory 선택적 재검증

- [x] 현재 상태와 혼동 가능성이 큰 오래된 risk 항목만 선별한다.
- [x] 전체 Foundation 재감사 대신 선별 항목의 현재 `main` 상태와 기존 evidence를 대조한다.
- [x] 과거 snapshot과 current validation 결과를 문서에서 명확히 구분한다.

**완료 조건:** 재검증 대상과 제외 대상의 기준이 기록되고 stale risk 또는 현재성 오해가 정리된다. Runtime 구현 근거는 `main@8a3c2c785a86d80019010eb6747c8b9520aba7fe`에 고정했다. `3 passed, 23 deselected`는 PR 작성 중 기록된 focused result지만 원래 pytest command가 보존되지 않아 reproducible current-HEAD execution evidence로 승격하지 않는다. 재현 가능한 test target은 Foundation readiness에 기록했다.

### 3. 다음 Reliability milestone 하나 선정

- [x] `volume_drop`과 `null_spike`에서 재사용 가능한 approval, recovery, evaluation evidence contract를 목록화한다.
- [x] 새 workflow/meta-work를 늘리기 전에 가장 작은 다음 Reliability capability를 선택한다.
- [x] 선택한 milestone의 scope, owning package, validation boundary를 기록한다.

**완료 조건:** 다음 milestone이 하나로 좁혀지고, 구현 전에 scope와 검증 경계가 설명된다. [Next Reliability Milestone](../../docs/development/reliability-next-milestone.md)에 `schema_drift` recovery vertical slice를 차기 capability로 확정하고 재사용 contract, scope, owning package, validation boundary를 기록했다.

## Later

### 4. Marimo 정책과 문서 정렬

- [x] Marimo가 현재 active tool인지 제거 대상인지 실제 사용 상태를 확인한다.
- [x] 결정에 따라 `DEVELOPMENT.md`와 Foundation readiness 관련 기록의 설명을 정렬한다.
- [x] historical drift를 current policy로 오해할 수 있는 표현을 제거한다.

**완료 조건:** Marimo ownership과 정책 상태가 관련 문서에서 일관되게 표현된다. Marimo는 active runtime/tool이 아니며, `pyproject.toml`의 dependency와 runtime 설정도 제거했다.

## Validation Boundary

이번 정리는 2026-08-14~15 repository brief와 Notion 통합 요약을 실행 항목으로 재구성한 것이다. 원본 정리 문서 작성 과정에서는 pytest, Ruff, `ty`, OpenSpec CLI를 새로 실행하지 않았다. 따라서 기존 `24/24` 수치는 저장된 evidence의 snapshot으로만 취급하며, current `HEAD` 검증 결과로 재사용하지 않는다. Archive readiness 후속 작업의 current `HEAD` 검증 결과는 위 `Archive evidence`에 별도로 기록한다.

## Source

- [Project Pivot Inbox Brief Summary (2026-08-14~15)](https://app.notion.com/p/3bd13d7e58b98196b078f7828423e4da)
- [2026-08-14 10:04 brief](https://github.com/mols3131d/project-pivot/blob/inbox/inbox/2026-08-14/10-04-brief-project-pivot-repository-status.md)
- [2026-08-14 17:59 brief](https://github.com/mols3131d/project-pivot/blob/inbox/inbox/2026-08-14/17-59-brief-project-pivot-repository-status.md)
- [2026-08-15 09:59 brief](https://github.com/mols3131d/project-pivot/blob/inbox/inbox/2026-08-15/09-59-brief-project-pivot-repository-status.md)
- [2026-08-15 17:59 brief](https://github.com/mols3131d/project-pivot/blob/inbox/inbox/2026-08-15/17-59-brief-project-pivot-repository-status.md)
