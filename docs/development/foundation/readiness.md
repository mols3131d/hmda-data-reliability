# Foundation Readiness Dashboard

> **Snapshot:** 2026-08-07  
> **Decision:** 🔴 Blocked  
> **Audited revision:** `b34a78582cbce5193568caa54744db630468fe94`

`foundation-baseline` OpenSpec을 기준으로 Foundation 완료에 필요한 capability만 합산한다. 아래 수치는 구현·test oracle **coverage**이며, 최신 HEAD의 실행 통과율이 아니다. Audit 시점에는 현재 revision의 GitHub Actions 실행 evidence를 확인하지 못했다.

## Foundation Gate

| Capability | Implementation Status | Implementation Coverage | Verification Status | Verification Oracle Coverage |
| --- | :---: | --- | :---: | --- |
| HMDA Source Ingestion | 🟢 Implemented | `7/7` | ⚪ Unverified | `7/7` |
| Bronze Raw Table | 🟢 Implemented | `7/7` | ⚪ Unverified | `7/7` |
| Partition Ingestion Idempotency | 🟢 Implemented | `5/5` | ⚪ Unverified | `5/5` |
| Silver Source Contract | 🟢 Implemented | `18/18` | ⚪ Unverified | `18/18` |
| Silver Staging Layer | 🟢 Implemented | `18/18` | 🟡 Partial | `17/18` |
| Gold Mart Grain Alignment | 🟢 Implemented | `18/18` | ⚪ Unverified | `18/18` |
| Gold Analysis Metrics | 🟢 Implemented | `18/18` | ⚪ Unverified | `18/18` |
| EDA Schema and Volume Observation | 🟢 Implemented | `11/11` | ⚪ Unverified | `11/11` |
| EDA Quality Baseline | 🟢 Implemented | `12/12` | 🔴 Blocked | `0/1` |
| EDA Domain Observation | 🟢 Implemented | `26/26` | 🔴 Blocked | `0/1` |
| Reliability Contracts | 🔴 Blocked | `7/7` | 🔴 Blocked | `7/7` |
| **Total** | **🔴 Blocked** | **`147/147`** | **🔴 Blocked** | **`108/111`** |

Implementation coverage는 `147/147`이다. Foundation 종료 여부는 coverage가 아니라 아래 blocker와 current runtime verification으로 결정한다.

## Blockers

| ID | Area | Finding | Close When |
| --- | --- | --- | --- |
| B1 | HMDA EDA | actual-source evidence가 dirty revision에서 생성되어 clean-HEAD provenance contract와 충돌한다. | clean HEAD에서 evidence를 재생성하고 provenance·artifact invariant를 검증한다. |
| B2 | Silver | canonical domain contract는 staging의 raw row, Null과 `try_cast` semantics 보존을 요구하지만 integration test가 staging 결과를 직접 검증하지 않는다. | staging 자체의 preservation semantics를 test로 고정한다. |
| B3 | Reliability Contracts | Foundation `ProfileSnapshot` contract가 `freshness_at`을 required datetime으로만 표현해 freshness 미측정 상태를 구분하지 못한다. 후속 profile runtime은 이를 `observed_at` fallback으로 메운다. | 미측정 상태의 canonical 표현을 정하고 contract·builder·detector를 정렬한다. |
| B4 | Foundation Governance | EDA change lifecycle/task metadata가 현재 tree와 어긋나고 root README의 Foundation readiness navigation도 사라졌다. | active change와 metadata를 정리하고 README navigation을 복구한다. |

## Current Verification

현재 HEAD에서 Foundation 관련 pytest/dbt/actual-source 실행 evidence는 **Unverified**다. Test가 존재하거나 과거 실행이 성공했다는 사실만으로 현재 verification을 `Passing`으로 올리지 않는다.

주요 재검증 command:

```bash
mkdir -p artifacts && uv run pytest tests/hmda_data
mkdir -p artifacts && uv run pytest tests/data_platform tests/dbt
mkdir -p artifacts && uv run pytest tests/reliability/contracts
uv run python scripts/run_actual_source.py
```

## Non-Gating Inventory

다음 capability는 현재 구현되어 있거나 위험이 확인됐지만 `foundation-baseline`에 따라 Foundation 총계에는 포함하지 않는다.

| Capability | Audit Status |
| --- | --- |
| Profile / incident / impact / remediation lifecycle | Implemented, current execution unverified |
| Approval backfill validation | Implemented, current execution unverified |
| Evaluation report | Implemented, current execution unverified |
| Dagster orchestration | Blocked — standard pipeline에서 dbt skip materialization semantics 충돌 |
| dbt last-known-good evidence retention | Blocked — build 전 기존 artifact 삭제 |
| Synthetic reliability cases | Implemented, current execution unverified |
| Test quality observability | Implemented, current execution unverified |

## Additional Drift

- Gold metric의 `action_taken` 모집단과 `approval_rate` 분모는 canonical Data Platform domain 문서에 정의되어 있고 현재 SQL/test와 일치한다. 다만 `dbt-analytics-foundation` OpenSpec에는 세부 semantics가 없어 traceability가 약하다.
- `DEVELOPMENT.md`와 `pyproject.toml`에는 제거된 Marimo EDA runtime 관련 설명·설정이 남아 있다.
- Foundation draft README에는 이미 결정된 Gold grain과 제거된 notebook smoke가 미결정 항목으로 남아 있다.
- `approval-backfill-validation`, `evaluation-report` canonical spec의 `Purpose`가 아직 `TBD`다.

## References

- [Foundation](README.md)
- [Bronze](data-pipeline-bronze.md)
- [Silver](data-pipeline-silver.md)
- [Gold](data-pipeline-gold.md)
- [EDA](eda.md)
- [Observability](observability.md)
- [Reliability](reliability.md)
- [Orchestration](orchestration.md)
- [Data Platform Domain](../../domains/data-platform.md)
- [Reliability Domain](../../domains/reliability.md)
- [ARCHITECTURE](../../ARCHITECTURE.md)
- OpenSpec: `foundation-baseline`, `hmda-data-foundation`, `partition-ingestion`, `hmda-eda-baseline`, `dbt-analytics-foundation`, `reliability-contracts`
