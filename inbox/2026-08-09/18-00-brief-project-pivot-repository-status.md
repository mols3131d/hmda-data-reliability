---
type: brief
title: Project Pivot Repository Status Brief
description: 2026-08-09 18:00 KST 기준 최신 main, 최근 PR과 Foundation readiness를 바탕으로 정리한 저장소 상태 브리프.
tags:
  - domain:project
  - capability:status-brief
---

# Project Pivot Repository Status Brief

## Summary

최신 `main`은 `16dfba7`이며 최근 작업은 runtime 기능 확장보다 OpenSpec taxonomy, source instruction, agent skill 등 계약과 개발 자산의 책임 경계를 정리하는 데 집중됐다. Foundation readiness는 audited runtime 기준 `GO`이고 `147/147` implementation, `111/111` verification checklist를 기록한다. 다만 current `main`에서 runtime validation을 재실행한 결과는 아니며, readiness에는 orchestration dbt skip semantics와 dbt last-known-good evidence retention이 non-gating blocked risk로 남아 있다.

## 1. Recent Work

### Facts

- 최신 `main`: `16dfba76727fe6fbf8a8e678971fe69ab65cdb92` — PR #32 `docs: source instruction 계층 분리` merge.
- 직전 주요 merge:
  - PR #35 — `pivot-clarify-code` skill 개선 및 progressive disclosure 정리.
  - PR #34 — canonical OpenSpec Spec을 domain/capability 중심으로 재구성하고 Foundation phase 판단을 readiness artifact로 분리.
  - PR #33 — inbox artifact promotion/lifecycle 규칙 정리.
- PR #30은 Foundation contract와 evidence provenance를 구현·테스트·canonical Spec과 재대조했다.

### Inference

최근 개발의 중심은 신규 runtime capability보다 Foundation 종료 전에 문서·계약·agent workflow의 ownership drift를 줄이는 작업이었다.

## 2. Development Status

### Facts

Foundation readiness snapshot(2026-08-08)은 다음을 기록한다.

- Decision: `GO (audited runtime)`
- Implementation coverage: `147/147`
- Verification checklist coverage: `111/111`
- Audited focused suite: `57 passed in 13.63s`
- Current PR validation: `Not run`
- Audited Foundation blocker: 없음

Readiness의 non-gating inventory에는 reliability lifecycle/recovery/evaluation, orchestration, synthetic defects 등 Foundation 밖 capability가 별도로 관리된다.

### Inference

Foundation gate 자체는 닫힌 것으로 취급할 근거가 충분하다. 현재 병목은 Foundation 문서 보강보다는 MVP에서 어떤 vertical slice를 먼저 실행 가능한 상태로 만들지 결정하는 데 가깝다.

## 3. Documentation and Code Consistency

### P2 — Runtime evidence freshness

Readiness가 명시하듯 `57 passed`는 audited revision `feea63f...`의 결과이며 current `main` 실행 결과가 아니다. 문서가 이를 정확히 구분하고 있어 계약 drift는 아니지만, MVP 진입 시 최신 runtime baseline이 필요하면 재검증이 필요하다.

### P2 — Known runtime gaps remain explicit

OpenSpec taxonomy 정리는 orchestration/dbt runtime risk를 해결한 것으로 취급하지 않는다. Readiness도 다음을 명시한다.

- Orchestration pipeline: standard pipeline의 dbt skip materialization semantics 충돌.
- dbt last-known-good evidence retention: build 전 기존 artifact 삭제.
- Recovery: `source_file` scoped comparison은 file-level population equivalence를 보장하지 않음.

문서와 PR 설명 사이에서 이 위험들의 상태 표현은 일관된다.

### P3 — Marimo drift

Readiness는 `DEVELOPMENT.md`와 `pyproject.toml`에 제거된 Marimo EDA runtime 설명·설정이 남아 있다고 기록한다. Foundation blocker는 아니지만 명시적인 documentation/configuration drift다.

## 4. Next Actions

1. **MVP vertical slice를 하나 선정해 OpenSpec Change로 착수한다.** Foundation gate가 닫혔으므로 추가적인 광범위 문서 정리보다 실제 end-to-end value 검증의 우선순위가 높다.
2. **MVP 실행 경로가 dbt/orchestration을 사용한다면 두 blocked risk를 먼저 닫는다.** last-known-good artifact retention과 dbt skip semantics는 evidence 신뢰성과 pipeline 실행 의미에 직접 영향을 준다.
3. **Marimo drift를 작은 cleanup으로 제거한다.** runtime 방향과 개발 문서/configuration을 맞추되 MVP 착수를 지연시키는 대규모 작업으로 확대하지 않는다.

## Verification Boundary

이 브리프는 GitHub의 최신 `main`, 최근 commit/PR metadata, Foundation readiness 및 inbox branch 지침을 정적으로 확인해 작성했다. pytest, dbt build, Dagster runtime, actual-source observation은 이번 브리프 작성 과정에서 실행하지 않았다.
