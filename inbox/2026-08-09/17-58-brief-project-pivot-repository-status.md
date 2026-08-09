---
type: brief
title: Project Pivot Repository Brief — 2026-08-09 17:58
description: 최신 main, 최근 PR/commit, Foundation readiness와 runtime 위험을 교차 검토한 정기 repository brief.
tags:
  - project-pivot
  - repository-status
  - foundation
  - mvp
---

# Project Pivot Repository Brief

## Summary

최신 `main`은 `16dfba76727fe6fbf8a8e678971fe69ab65cdb92`이며, 직전 브리핑 이후 새 `main` commit과 open PR은 확인되지 않았다. Foundation은 canonical readiness에서 `GO`이지만 해당 판정은 audited runtime evidence에 기반하며 current `main` 재실행 결과가 아니다.

현재 저장소의 핵심 병목은 Foundation 추가 정리가 아니라 **Reliability MVP vertical slice를 active OpenSpec Change로 전환하는 것**이다. 이미 `volume_drop` 단일 recovery vertical slice의 research 결론이 존재하지만 `openspec/changes/`에는 active Change가 없다.

구현상 우선 위험은 `run_dbt_build()`가 실행 전에 기존 `manifest.json`과 `run_results.json`을 삭제하는 점과, Dagster에서 dbt 실행을 skip해도 `MaterializeResult`를 반환해 asset materialization semantics와 충돌하는 점이다. Marimo는 제거된 runtime이라는 readiness 설명과 달리 `DEVELOPMENT.md`와 `pyproject.toml`에 계속 남아 있어 문서·설정 drift가 확인된다.

## 1. 최근 수행된 작업 브리프

### Verified facts

- 최신 `main`: `16dfba7` — PR #32 `docs: source instruction 계층 분리` merge.
- 직전 주요 merge:
  - PR #35 — `pivot-clarify-code` skill 개선.
  - PR #34 — OpenSpec canonical Spec taxonomy를 domain/capability 중심으로 재구성.
- 현재 open PR: 0.
- `openspec/changes/`에는 `archive/`와 운영 문서만 있고 active Change directory가 없다.
- 직전 브리핑 이후 새 `main` commit은 확인되지 않았다.

### Meaning

최근 개발 흐름은 source implementation 확장보다 **계약, taxonomy, instruction ownership, agent workflow의 구조 정리**에 집중되어 있다. 이 정리는 Foundation 이후 MVP에 진입하기 위한 해석 비용을 낮췄지만, 현재는 추가 meta-documentation보다 실제 MVP Change 생성의 가치가 더 높다.

## 2. 레포지토리 개발 현황 브리프

### Foundation

`docs/development/foundation/readiness.md`의 2026-08-08 snapshot:

- Decision: `GO (audited runtime)`
- Implementation coverage: `147/147`
- Verification checklist coverage: `111/111`
- Audited focused suite: `57 passed in 13.63s`
- Current PR validation: `Not run`

따라서 Foundation 완료 판단은 유효한 repository evidence이지만 **현재 main HEAD를 새로 실행해 검증했다는 의미는 아니다.**

### MVP

`inbox/archive/2026-08-08/reliability-mvp-volume-drop-vertical-slice.md`는 첫 MVP를 다음 흐름으로 결정한다.

`volume_drop → detection → impact → candidate validation → human approval → recovery → post-recovery verification`

Research는 completed 상태이며 safety contract까지 정리되어 있다. 반면 active OpenSpec Change는 없다.

**Inference:** 현재 MVP의 실질 상태는 “방향 결정 완료 / Planning 미착수”에 가깝다. 구현 병목보다 plan-to-implementation handoff가 현재 가장 직접적인 병목이다.

## 3. 문서 및 코드 일관성 리뷰 브리프

### 🟠 P2 — Marimo runtime drift

`docs/development/foundation/readiness.md`는 Marimo EDA runtime 관련 설명·설정을 제거 대상 drift로 명시한다. 그러나 현재:

- `DEVELOPMENT.md`: Analysis 및 Notebook 도구로 `Marimo` 명시.
- `pyproject.toml`: dev dependency `marimo>=0.23.16` 유지.
- `pyproject.toml`: `[tool.marimo.runtime]` 유지.

이는 readiness와 실제 개발 환경 문서/설정 사이의 명시적 불일치다.

### 🟠 P2 — Foundation validation provenance는 일관되지만 current HEAD 검증은 아님

Readiness는 audited test revision, actual-source execution revision, evidence commit을 분리해서 기록하고 현재 PR validation이 실행되지 않았음을 명시한다. 이 부분은 과거의 “최신 HEAD가 검증됐다”는 오해 가능성을 줄였고 문서 내부 provenance는 일관적이다.

### 🟢 OpenSpec taxonomy와 phase ownership

Foundation phase 판단은 readiness artifact가 소유하고 runtime behavior는 canonical capability Spec이 소유한다. `openspec/changes/`에는 active Change가 없고 canonical Spec 정리 이후 archive만 유지된다. 최근 taxonomy 작업과 현재 directory 상태가 정렬되어 있다.

## 4. 위험 및 경고 관련 브리프

### 🔴 P1 — dbt last-known-good artifact 손실 가능성

`src/project_pivot/data_operations/runner.py`의 `run_dbt_build()`는 dbt 실행 전에 `_remove_dbt_artifacts()`를 호출하고 기존 `manifest.json` 및 `run_results.json`을 삭제한다.

따라서 dbt process 실패, timeout, artifact 미생성 시 직전 정상 실행의 evidence도 함께 사라질 수 있다. 이는 MVP research가 요구한 replay, reconciliation, candidate validation의 evidence safety와 직접 충돌한다.

### 🔴 P1 — Dagster dbt skip materialization semantics

`src/project_pivot/orchestration/defs/assets.py`에서 `run_dbt_build=false`이면 dbt를 실행하지 않지만 `MaterializeResult`를 반환하고 metadata에 `skipped=true`, `succeeded=false`를 기록한다.

**Inference:** 실제 Silver/Gold data가 갱신되지 않았는데 asset이 materialized된 것으로 해석될 수 있어 orchestration 상태와 실제 data plane 상태가 어긋날 위험이 있다. Readiness도 이 항목을 `Blocked`로 기록한다.

### 🟠 P2 — Reliability 확장 capability의 current execution 공백

Profile / incident / impact / remediation, recovery, evaluation, synthetic defects는 구현됐지만 readiness 기준 current execution은 unverified다. Foundation blocker는 아니지만 MVP에서는 해당 흐름 자체가 제품 가치 검증 대상이므로 새로운 end-to-end evidence가 필요하다.

### 🟠 P2 — Inbox branch 운영 부채

전용 `inbox` branch는 최신 `main`과 diverged 상태이며 비교 시 `main` 쪽 고유 commit이 151개, `inbox` 쪽 고유 commit이 9개다. 또한 routine date directory가 이미 lifecycle 기준인 8개를 초과해 9개 존재했다.

이번 brief는 최신 `main`의 `inbox/AGENTS.md`와 `docs/development/vcs-git/branch.md`를 기준으로 작성했다. 다만 `inbox` branch의 운영 자산 동기화와 archive rotation은 별도 정리 작업이 필요하다.

## 5. 그 외 분석 브리프

### 개선 신호

- Root README navigation은 Architecture / Development / Foundation Readiness로 최소화되어 entrypoint가 명확하다.
- Architecture는 data plane과 reliability control/recovery boundary를 명확히 분리한다.
- OpenSpec taxonomy는 phase artifact와 capability Spec의 ownership을 분리했다.
- Foundation readiness가 실행 revision과 evidence revision을 구분해 검증 provenance를 과장하지 않는다.

### 비효율 신호

최근 변경의 상당 부분이 문서·taxonomy·skill·instruction refinement에 집중되었다. 구조 정리는 충분한 수준에 도달했으며, 현재 상태에서 같은 층위의 추가 review/refactor를 반복하면 MVP 진행보다 meta-work 비중이 커질 가능성이 있다.

## 6. 다음 할 일 제안 브리프

### P1. Reliability MVP OpenSpec Change 생성

- **이유:** MVP research 결론은 완료됐지만 active Change가 없다.
- **기대 효과:** `volume_drop` vertical slice를 specification, design, tasks, tests로 실행 가능한 단위로 전환한다.
- **주의:** Research의 safety decision을 그대로 구현 상세로 고정하지 말고 exact model, hashing, writer gate, artifact workspace는 Design에서 결정한다.

### P2. dbt artifact retention을 MVP 선행 contract로 해결

- **이유:** 현재 runner의 pre-delete 동작은 MVP candidate/recovery evidence 정확성을 훼손할 수 있다.
- **기대 효과:** failed build에서도 last-known-good evidence를 보존하고 run-scoped failure evidence를 남길 수 있다.
- **주의:** 단순 삭제 제거보다 성공 후 promotion semantics까지 정의해야 한다.

### P3. Dagster skip semantics를 MVP 실행 경로에 들어가기 전에 정리

- **이유:** skip인데 materialization event가 남는 현재 구조는 orchestration truth와 실제 data 상태를 다르게 만들 수 있다.
- **기대 효과:** pipeline 상태의 해석 가능성과 downstream dependency 정확성이 높아진다.
- **주의:** Dagster control-plane 자체를 MVP scope로 확대하지 말고 현재 asset contract만 바로잡는다.

### P4. Marimo drift는 작은 cleanup으로 닫기

- **이유:** readiness가 이미 drift로 명시했고 수정 범위가 작다.
- **기대 효과:** 개발 환경 문서와 dependency/config가 현재 EDA runtime 방향과 일치한다.
- **주의:** MVP보다 우선하지 않는다.

## Evidence

- `README.md`
- `AGENTS.md`
- `DEVELOPMENT.md`
- `docs/ARCHITECTURE.md`
- `docs/development/README.md`
- `docs/development/foundation/readiness.md`
- `docs/development/vcs-git/branch.md`
- `docs/development/vcs-git/commit.md`
- `pyproject.toml`
- `src/project_pivot/data_operations/runner.py`
- `src/project_pivot/orchestration/defs/assets.py`
- `inbox/archive/2026-08-08/reliability-mvp-volume-drop-vertical-slice.md`
- latest reviewed `main`: `16dfba76727fe6fbf8a8e678971fe69ab65cdb92`

## Validation Limits

- Repository runtime, pytest, dbt build, Dagster execution은 이번 분석에서 실행하지 않았다.
- GitHub repository content, commit/PR state와 기존 audited evidence를 정적으로 교차 검토했다.
