---
title: "HMDA Data Reliability Development Dashboard"
description: "현재 development snapshot에서 domain별 구현·검증 진행률, 남은 gap과 blocker를 한눈에 정리한 human-readable dashboard입니다."
categories:
  - data-engineering
  - reliability
tags:
  - ci
  - evaluation
  - openspec
  - testing
---

# HMDA Data Reliability Development Dashboard

> **Snapshot:** 2026-08-16 / `main@e9a8d2a`
> **Current Focus:** bounded Agentic review와 current-revision acceptance를 닫는다.

## Development Progress

| Domain | Implementation Status | Implementation Progress | Verification Status | Verification Progress |
| --- | :---: | --- | :---: | --- |
| HMDA Data | 🟡 In Progress | `████████░░ 17/19` | ⚪ Unverified | `░░░░░░░░░░ 0/3` |
| Data Platform | 🟢 Implemented | `██████████ 11/11` | ⚪ Unverified | `░░░░░░░░░░ 0/2` |
| Data Operations | 🟢 Implemented | `██████████ 9/9` | ⚪ Unverified | `░░░░░░░░░░ 0/2` |
| Reliability | 🟡 In Progress | `█████████░ 50/52` | ⚪ Unverified | `░░░░░░░░░░ 0/9` |
| Orchestration | 🟢 Implemented | `██████████ 7/7` | ⚪ Unverified | `░░░░░░░░░░ 0/1` |
| **Total** | **🟡 In Progress** | **`█████████░ 94/98`** | **⚪ Unverified** | **`░░░░░░░░░░ 0/17`** |

## Implementation Gaps

| Domain | # | Remaining Requirement |
| --- | :---: | --- |
| HMDA Data | 1 | `hmda-data-synthetic-defects` **Null spike case** — current source는 target null floor를 적용하지만 canonical Scenario가 요구하는 original-relative null-rate increase를 보장하지 않는다. |
| HMDA Data | 2 | `hmda-data-synthetic-defects` **Freshness delay case** — canonical Spec에는 존재하지만 current HMDA synthetic surface에서는 제거되어 있다. |
| Reliability | 1 | `reliability-profile-snapshots` **Freshness metric** — canonical Spec은 unavailable measurement에서 `observed_at` fallback을 요구하지만 current source는 `freshness_at=null`, `freshness_status=unavailable`을 반환한다. |
| Reliability | 2 | `reliability-incident-detection` **Freshness delay detection** — canonical Spec은 baseline-relative delay를 요구하지만 current source는 current observation age와 max-age threshold로 판정한다. |

## Verification Gaps

| Domain | # | Remaining Verification |
| --- | :---: | --- |
| HMDA Data | 1 | ⚪ `hmda-data-ingestion` matching-revision acceptance |
| HMDA Data | 2 | ⚪ `hmda-data-eda-descriptive-evidence` matching-revision acceptance |
| HMDA Data | 3 | ⚪ `hmda-data-synthetic-defects` matching-revision acceptance |
| Data Platform | 1 | ⚪ `data-platform-dbt-analytics` matching-revision acceptance |
| Data Platform | 2 | ⚪ `data-platform-duckdb-access` matching-revision acceptance |
| Data Operations | 1 | ⚪ `data-operations-stage-execution` matching-revision acceptance |
| Data Operations | 2 | ⚪ `data-operations-incident-lifecycle` matching-revision acceptance |
| Reliability | 1 | ⚪ `reliability-data-contracts` matching-revision acceptance |
| Reliability | 2 | ⚪ `reliability-evaluation-report` matching-revision acceptance |
| Reliability | 3 | ⚪ `reliability-evidence-table-metadata` matching-revision acceptance |
| Reliability | 4 | ⚪ `reliability-impact-analysis` matching-revision acceptance |
| Reliability | 5 | ⚪ `reliability-incident-detection` matching-revision acceptance |
| Reliability | 6 | ⚪ `reliability-profile-snapshots` matching-revision acceptance |
| Reliability | 7 | ⚪ `reliability-recovery-backfill` matching-revision acceptance |
| Reliability | 8 | ⚪ `reliability-remediation-draft` matching-revision acceptance |
| Reliability | 9 | ⚪ `reliability-schema-recovery` matching-revision acceptance |
| Orchestration | 1 | ⚪ `orchestration-pipeline` matching-revision acceptance |

## Risks / Blockers

| Area | Risk / Blocker | Impact |
| --- | --- | --- |
| Reliability / MVP | `docs/mvp.md`가 요구하는 bounded Agentic review, deterministic review validation과 live model proof가 current canonical Spec inventory와 runtime source에 아직 없다. | Deterministic capability 구현률과 별개로 HMDA Data Reliability MVP 완료를 선언할 수 없다. |

## References

- Current MVP scope: [`../mvp.md`](../mvp.md)
- Canonical capability contracts: [`../../openspec/specs/`](../../openspec/specs/)
- Implementation evidence: `src/hmda_reliability/`, `dbt/`
- Executable specification surfaces: `tests/`
- Counting rule: Implementation은 canonical Requirement 98개, Verification은 canonical capability별 matching-revision acceptance target 17개를 의미 단위로 집계한다.
- Current-revision validation: `main@e9a8d2a`에 연결된 GitHub Actions workflow run을 확인하지 못했으며 과거 revision 결과는 재사용하지 않았다.
- Dashboard policy: [`../AGENTS.md`](../AGENTS.md#dashboard-policy)
