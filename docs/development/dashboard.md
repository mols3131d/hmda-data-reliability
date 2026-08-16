# Project Pivot Development Dashboard

> [!CAUTION]
> **Human convenience snapshot only.** 이 문서는 canonical source, agent context 또는 validation evidence가 아니다.

> **Snapshot:** 2026-08-16 / evidence base `main@e9a8d2a`
> **Current Focus:** bounded Agentic review와 current-revision acceptance를 닫는다.

Implementation progress는 `openspec/specs/**`의 17개 current capability에서 식별한 **98개 canonical Requirement**를 의미 단위로 집계한다. Verification progress는 각 canonical capability마다 **matching-revision acceptance target 1개**, 총 17개를 집계한다. Test 파일 존재나 과거 revision의 성공 결과는 current-revision verification으로 세지 않는다.

## Development Progress

| Domain | Implementation Status | Implementation Progress | Verification Status | Verification Progress |
| --- | :---: | --- | :---: | --- |
| HMDA Data | 🟡 In Progress | `████████░░ 17/19` | ⚪ Unverified | `░░░░░░░░░░ 0/3` |
| Data Platform | 🟢 Implemented | `██████████ 11/11` | ⚪ Unverified | `░░░░░░░░░░ 0/2` |
| Data Operations | 🟢 Implemented | `██████████ 9/9` | ⚪ Unverified | `░░░░░░░░░░ 0/2` |
| Reliability | 🟡 In Progress | `█████████░ 50/52` | ⚪ Unverified | `░░░░░░░░░░ 0/9` |
| Orchestration | 🟢 Implemented | `██████████ 7/7` | ⚪ Unverified | `░░░░░░░░░░ 0/1` |
| **Total** | **🟡 In Progress** | **`█████████░ 94/98`** | **⚪ Unverified** | **`░░░░░░░░░░ 0/17`** |

`Implemented`는 current source에서 해당 canonical Requirement의 구현 evidence를 확인했다는 뜻이다. Source가 더 새로운 behavior를 구현했더라도 canonical Spec과 의미가 다르면 완료로 세지 않는다. `Verification`은 별도이며, snapshot revision에서 실제 acceptance evidence가 확인되지 않으면 `Unverified`로 남긴다.

## Implementation Gaps

| Domain | # | Remaining Requirement |
| --- | :---: | --- |
| HMDA Data | 1 | `hmda-data-synthetic-defects` **Null spike case** — canonical Scenario는 결과 `income` null 비율이 원본보다 증가할 것을 요구하지만 current source는 sampled rows에 target null floor를 적용하며 original-relative increase를 직접 보장하거나 검증하지 않는다. |
| HMDA Data | 2 | `hmda-data-synthetic-defects` **Freshness delay case** — canonical Spec은 지연 observation timestamp를 포함하는 synthetic case를 요구하지만 current HMDA synthetic surface에서는 이 case가 제거되어 있다. |
| Reliability | 1 | `reliability-profile-snapshots` **Freshness metric** — canonical Spec은 측정값이 없을 때 `observed_at`을 `freshness_at`으로 fallback하도록 요구하지만 current source는 `freshness_at=null`, `freshness_status=unavailable`을 반환한다. |
| Reliability | 2 | `reliability-incident-detection` **Freshness delay detection** — canonical Spec은 baseline 대비 freshness delay를 요구하지만 current source는 `current.observed_at - current.freshness_at`의 current-age SLA로 판정한다. |

마지막 세 freshness gap은 active `reliability-freshness-delay-semantics` Change가 의도한 delta와 방향이 일치한다. 그러나 `openspec/changes/**`는 non-canonical work artifact이므로, durable contract가 `openspec/specs/**`에 동기화되기 전에는 current canonical Requirement가 충족됐다고 계산하지 않는다.

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

Snapshot revision `main@e9a8d2a`에 연결된 GitHub Actions workflow run은 확인되지 않았다. 따라서 과거 revision의 CI/test 결과를 재사용하지 않고 17개 target을 모두 미검증으로 유지한다.

## Risks / Blockers

| Area | Risk / Blocker | Development Impact |
| --- | --- | --- |
| Reliability / MVP | `docs/mvp.md`가 요구하는 bounded Agentic review, deterministic review validation과 live model proof가 current canonical Spec inventory와 runtime source에 아직 없다. | Canonical deterministic Reliability의 구현률과 별개로 **Project Pivot MVP 완료를 선언할 수 없다.** |

## References

- Current MVP scope: [`../mvp.md`](../mvp.md)
- Canonical capability contracts: [`../../openspec/specs/`](../../openspec/specs/)
- HMDA implementation: `src/project_pivot/hmda_data/`
- Data Platform implementation: `src/project_pivot/data_platform/`, `dbt/`
- Data Operations implementation: `src/project_pivot/data_operations/`
- Reliability implementation: `src/project_pivot/reliability/`
- Orchestration implementation: `src/project_pivot/orchestration/`
- Executable specification surfaces: `tests/hmda_data/`, `tests/data_platform/`, `tests/dbt/`, `tests/data_operations/`, `tests/reliability/`, `tests/orchestration/`

Dashboard의 읽기·갱신 규칙은 [`../AGENTS.md`](../AGENTS.md#dashboard-policy)를 따른다.
