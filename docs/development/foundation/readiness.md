# Foundation Readiness Dashboard

> **Snapshot:** 2026-08-08  
> **Decision:** 🟢 GO (audited runtime)  
> **Audited test revision:** `feea63fe5945c353f2f9b70b57a29cbe7294dafa`  
> **Actual-source execution revision:** `17522ddc42748fe22e779f50b8e328ebaf2d4abb`  
> **Evidence commit:** `feea63fe5945c353f2f9b70b57a29cbe7294dafa`  
> **Current PR validation:** ⚪ Not run

`readiness.md`와 `readiness.yml`은 Foundation phase의 현재 완료 판단과 evidence inventory를 기록한다. 시스템 동작 계약은 current canonical capability Spec이 소유한다. Foundation focused suite는 audited test revision에서 57개 test가 통과했다. Actual-source evidence는 별도 execution revision에서 생성되었고, evidence commit까지 EDA runtime·source·generator 변경이 없어 현재 audited evidence에 적용 가능하다.

## Foundation Gate

| Capability | Implementation Status | Implementation Coverage | Verification Status | Verification Checklist Coverage |
| --- | :---: | --- | :---: | --- |
| HMDA Source Ingestion | 🟢 Implemented | `7/7` | 🟢 Verified | `7/7` |
| Bronze Raw Table | 🟢 Implemented | `7/7` | 🟢 Verified | `7/7` |
| Partition Ingestion Idempotency | 🟢 Implemented | `5/5` | 🟢 Verified | `5/5` |
| Silver Source Contract | 🟢 Implemented | `18/18` | 🟢 Verified | `18/18` |
| Silver Staging Layer | 🟢 Implemented | `18/18` | 🟢 Verified | `18/18` |
| Gold Mart Grain Alignment | 🟢 Implemented | `18/18` | 🟢 Verified | `18/18` |
| Gold Analysis Metrics | 🟢 Implemented | `18/18` | 🟢 Verified | `18/18` |
| EDA Schema and Volume Observation | 🟢 Implemented | `11/11` | 🟢 Verified | `11/11` |
| EDA Quality Baseline | 🟢 Implemented | `12/12` | 🟢 Verified | `1/1` |
| EDA Domain Observation | 🟢 Implemented | `26/26` | 🟢 Verified | `1/1` |
| Reliability Data Contracts | 🟢 Implemented | `7/7` | 🟢 Verified | `7/7` |
| **Total** | **🟢 GO** | **`147/147`** | **🟢 Verified** | **`111/111`** |

Implementation coverage는 `147/147`이며, Verification checklist coverage는 `111/111`이다. 표의 `Verified`는 audited evidence 상태이며 current PR head의 재실행 결과를 의미하지 않는다.

## Blockers

Audited Foundation runtime 기준 blocker 없음 (B1, B2, B4 해결 완료).

## Audited Verification

Foundation focused suite:

- Revision: `feea63fe5945c353f2f9b70b57a29cbe7294dafa`
- Result: **57 passed in 13.63s**

Actual-source observation:

- Execution revision: `17522ddc42748fe22e779f50b8e328ebaf2d4abb`
- Evidence commit: `feea63fe5945c353f2f9b70b57a29cbe7294dafa`
- Source fingerprint: canonical evidence의 SHA-256 사용
- Applicability: execution revision과 evidence commit 사이 변경은 generated EDA evidence artifact뿐이며 EDA calculation, source, evidence generator semantics는 변경되지 않았다.

재현 command:

```bash
mkdir -p artifacts && uv run pytest tests/hmda_data tests/data_platform tests/dbt tests/reliability/contracts
uv run python scripts/run_actual_source.py
```

이 PR에서는 canonical Spec taxonomy와 참조만 정리하며 runtime validation을 다시 실행하지 않았다. 따라서 위 결과를 current PR head execution으로 표현하지 않는다.

## Non-Gating Inventory

다음 capability와 development concern은 현재 구현되어 있거나 위험이 확인됐지만 Foundation 총계에는 포함하지 않는다.

| Capability | Audit Status |
| --- | --- |
| Reliability freshness semantics | Risk — Foundation data contract는 `freshness_at` 존재만 요구하고 `reliability-profile-snapshots`는 미측정 시 `observed_at` fallback을 명시한다. 미측정 상태의 별도 표현은 후속 contract 개선 후보다. |
| Profile / incident / impact / remediation lifecycle | Implemented, current execution unverified |
| Reliability recovery backfill | Implemented, current execution unverified — partition content identity와 recovery 경로가 `source_file` scope를 포함하며 source-file filtering과 file-scoped recovery test가 존재한다. Content identity가 correctness oracle이며 row-count는 auxiliary evidence로만 사용한다. |
| Reliability evaluation report | Implemented, current execution unverified |
| Orchestration pipeline | Blocked — standard pipeline에서 dbt skip materialization semantics 충돌 |
| dbt last-known-good evidence retention | Implemented, current execution unverified — 고유한 run-scoped target에서 candidate artifact를 만들고 current pair를 보존하며, promotion 실패 시 pair rollback test가 존재한다. |
| HMDA synthetic defects | Implemented, current execution unverified |
| Test quality observability | Implemented, current execution unverified — development/test tooling concern이며 canonical runtime Spec은 아니다. |

## Additional Drift

- `DEVELOPMENT.md`와 `pyproject.toml`에는 제거된 Marimo EDA runtime 관련 설명·설정이 남아 있다.

## Selective Revalidation

현재 구현과 기존 test 근거를 기준으로 다음 두 Non-Gating Inventory 항목의 stale risk 설명을 갱신했다.

- `reliability-recovery-backfill`: `source_file`이 partition content identity와 recovery 경로에 포함되고, source-file filtering 및 file-scoped recovery test가 존재한다. Canonical recovery Spec에 따라 row-count comparison은 file-level population equivalence의 oracle로 사용하지 않는다.
- `dbt Last-Known-Good Evidence Retention`: `run_dbt_build`가 고유한 run-scoped target을 사용하고 current artifact pair를 보존하며, promotion rollback test가 존재한다.

Evidence provenance:

- Implementation revision: `8a3c2c785a86d80019010eb6747c8b9520aba7fe` (PR base; 이 PR은 runtime code/test를 변경하지 않는다.)
- Recorded focused result: **3 passed, 23 deselected**
- Original pytest command: **not recorded**
- Reproduction targets:
  - `tests/reliability/test_evaluation_report.py::test_volume_drop_vertical_slice_preserves_source_file_scope`
  - `tests/data_operations/test_dbt_runner.py::test_candidate_dbt_build_does_not_promote_artifacts`
  - `tests/data_operations/test_dbt_runner.py::test_artifact_promotion_restores_pair_when_second_replace_fails`

재현 command:

```bash
uv run pytest \
  tests/reliability/test_evaluation_report.py::test_volume_drop_vertical_slice_preserves_source_file_scope \
  tests/data_operations/test_dbt_runner.py::test_candidate_dbt_build_does_not_promote_artifacts \
  tests/data_operations/test_dbt_runner.py::test_artifact_promotion_restores_pair_when_second_replace_fails
```

위 command는 review follow-up에서 새로 실행한 결과가 아니다. 원래 focused execution command가 보존되지 않았으므로 `3 passed, 23 deselected` 기록을 reproducible current-HEAD execution evidence로 승격하지 않는다. Foundation 전체 재감사와 current `main` 전체 validation도 이 작업 범위에 포함하지 않는다.

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
- OpenSpec: `hmda-data-ingestion`, `data-platform-duckdb-access`, `data-platform-dbt-analytics`, `hmda-data-eda-descriptive-evidence`, `reliability-data-contracts`
