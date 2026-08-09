---
type: research
title: Project Pivot MVP Vertical Slice Implementation Readiness Analysis
description: MVP vertical slice 구현 준비도를 분석. Reliability vertical slice (volume_drop → detect → approval → recovery → evaluation)를 중심으로 OpenSpec Change 전환 준비 상태를 평가.
status: draft
tags:
  - foundation
  - mvp
  - reliability
  - vertical-slice
---

> [!NOTE]
> Foundation은 147/147 implemented, 111/111 verified 상태로 GO. 현재 병목은 MVP 구현 착수 여부. OpenSpec taxonomy 재구성과 prj-clarify-code 개선 완료. Marimo drift는 non-gating P3. dbt artifact retention와 Dagster dbt skip semantics는 P1 runtime risk. 다음 단계로 Reliability MVP vertical slice 착수 추천.

## Question

MVP vertical slice (특히 Reliability의 volume_drop → detect → approval → recovery → evaluation slice) 구현 준비도를 OpenSpec Change로 전환할 수 있는지 분석. Foundation 완료 여부, open PR 상태, 문서·코드 일관성, P1/P2/P3 위험, 삭제/축소 문서·artifact, OpenSpec 16 capability coverage를 포함.

### Scope

- Foundation, Architecture, dbt, Orchestration, Reliability, Marimo 관련 artifact
- OpenSpec taxonomy, prj-clarify-code, source instruction
- P1 dbt build artifact deletion, Dagster dbt skip semantics
- P2 recovery source_file scoped comparison, lifecycle verification
- P3 Marimo dependency·문서 drift

### Stop Condition

Foundation GO 확인, open PR 없음, MVP 목표 재정렬 완료.

## Findings

### F1. Foundation Readiness

- 147/147 implemented, 111/111 verified, GO 상태
- audited revision evidence 기반. focused suite 57 passed
- Architecture 방향 (Bronze → dbt Silver/Gold, Reliability lifecycle 분리) 일치

### F2. OpenSpec Taxonomy

- domain → subdomain → capability 기준 재구성 완료
- openspec/specs/에 hmda-data-ingestion, data-platform-*, orchestration-pipeline, reliability-* 구조 반영
- PR #34 완료

### F3. Code Clarification

- prj-clarify-code → pivot-clarify-code 개선 완료
- progressive disclosure 구조 적용
- PR #35 완료

### F4. Document Consistency

- DEVELOPMENT.md: Marimo/EDA 설명 포함
- pyproject.toml: marimo dev dependency + [tool.marimo.runtime] 남아 있음
- pytest 설정: 일치
- OpenSpec taxonomy: 일치

### F5. Risk Summary

| Risk | Severity | Description |
| ------ | ---------- | ------------- |
| dbt build artifact 삭제 | P1 | last-known-good evidence 소실 가능 |
| Dagster dbt skip/materialization semantics | P1 | pipeline 실행 경로 충돌 |
| recovery source_file scoped comparison | P2 | population equivalence 미보장 |
| lifecycle/recovery/evaluation verification | P2 | 최신 runtime 미검증 |
| Marimo dependency·문서 drift | P3 | non-gating |

### F6. Next Steps Readiness

- Open PR: 없음 (MVP 목표 재정렬 가능)
- 문서·artifact 정리 한계효용 감소
- Reliability MVP vertical slice 착수 가치 최고

## Options

| Criterion | Option 1: Immediate MVP 착수 | Option 2: Risk 먼저 해결 |
| ----------- | ------------------------------- | --------------------------- |
| Foundation | GO, ready | GO, ready |
| Open PR | 없음 | 없음 |
| Risk level | P1 2건 | P1 2건 + P2 2건 |
| Effort | direct slice 구현 | 작은 독립 변경 |
| Recommendation | **1순위** | 2순위 dbt artifact, 3순위 Orchestration |

## Validation

| Check | Evidence | Result |
| ------- | ---------- | -------- |
| Foundation GO | audited evidence | Pass |
| Open PR 상태 | GitHub 확인 | Pass |
| Marimo drift | pyproject.toml · DEVELOPMENT.md | Pass (non-gating) |
| P1 risk 확인 | 소스·테스트 심층 리뷰 필요 | Pending |

## Next Actions

1. Reliability vertical slice OpenSpec Change로 전환
1. dbt artifact retention 수정
1. Dagster dbt skip semantics 해결
1. Marimo 잔재 제거

이 문서는 `inbox/2026-08-09/12-00-research-mvp-readiness.md`로 저장됨.
