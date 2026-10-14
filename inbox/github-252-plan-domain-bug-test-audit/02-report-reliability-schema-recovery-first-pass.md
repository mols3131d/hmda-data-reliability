---
type: report
title: Reliability Schema Recovery Audit First Pass
description: 최신 main의 스키마 복구 승인·후보 검증·상태 조정 및 테스트 검출력을 정적으로 감사한 첫 결과입니다.
tags:
  - reliability
  - testing
  - review
---

# Reliability Schema Recovery Audit First Pass

## Assessment

**첫 번째 제한 범위 정적 감사 완료. 확정된 production defect는 없다.** Schema recovery의 승인 일치성, staged candidate, target-state reconciliation, transactional rollback과 주요 regression test를 교차 확인했다. 테스트 설계에서 근거가 약한 assertion 한 건을 확인했지만 다른 integration test의 실제 approval 경계 검증도 발견되어, 회복 안전성이 깨졌다는 결론은 내리지 않는다.

| Field | Value |
| --- | --- |
| Audit Baseline | `8bc62fa6ec995f2e57456d55712b36ff11b1f1d9` (`main`, 2026-10-14) |
| Owning PR | #252, `agent/docs/plan-domain-bug-test-audit` |
| Reviewed Scope | Reliability 중 schema recovery의 승인·후보 staging·복구·replay 경계, partition backfill approval 경계 일부 |
| Method | OpenSpec ↔ source ↔ tests 정적 대조, 주변 호출자 확인, 셀프 리뷰 재검토 |
| Execution | **Not Verified** — pytest, 재현, fault injection, local DuckDB runtime 및 독립 리뷰 미실행 |
| Completion | 전체 Reliability 또는 일곱 도메인의 감사 완료를 의미하지 않음 |

## Evidence

계약은 [Schema Recovery Spec](../../openspec/specs/reliability-schema-recovery/spec.md)과 [Backfill Spec](../../openspec/specs/reliability-recovery-backfill/spec.md) 기준이다. 전체 source/tests에서 아래 경계만 집중 검토했다.

| Boundary | Implementation | Matching Tests | Observed Static Evidence |
| --- | --- | --- | --- |
| Exact approval과 scope | `recovery/schema_request.py`, `contracts/schema_recovery.py`, `recovery/schema_executor.py` | `contracts/test_schema_recovery.py`, `test_schema_recovery_executor.py` | approved status·proposal/action 일치 확인 후 candidate 접근 |
| Candidate preflight/staging | `recovery/schema_candidate.py` | `test_schema_recovery_candidate.py`, `test_schema_drift_evaluation.py` | complete table identity와 candidate dbt 결과 확인, staged Parquet state 재측정 |
| Target mutation/replay | `recovery/schema_executor.py`, `recovery/schema_result.py` | `test_schema_recovery_executor.py` | mutation lock 안에서 before/after 상태 분기, 트랜잭션 내부 replacement·profile validation·rollback |
| End-to-end caller | `evaluation/schema_drift.py` | `test_schema_drift_evaluation.py` | candidate preflight가 approve callback보다 앞서 있고 invalid candidate는 callback 미호출·target state 보존으로 검증 |
| Partition backfill cross-check | `recovery/executor.py`, `recovery/request.py` | `test_approval_backfill_validation.py` | proposal binding, staged source 검증, before/after reconciliation 및 오류 경로 확인; **전수 감사 아님** |

표의 구현 경로는 `src/hmda_reliability/reliability/`, 테스트 경로는 `tests/reliability/` 기준이다. 다른 Reliability 파일과 다른 도메인은 이번 라운드에서 검토하지 않았다.

## Finding

### R-TD-01 · Low · Candidate unit/component test의 approval 차단 주장 과도

- **Location:** `tests/reliability/test_schema_recovery_candidate.py`의 `test_candidate_state_failure_blocks_approval_and_target_access`, `test_candidate_dbt_failure_blocks_approval_and_target_access`.
- **Observed:** `approval_calls.append(...)`가 `pytest.raises` 내부의 `preflight(...)` 다음에만 위치하므로, 예외 발생 시 자동으로 실행되지 않는다. 테스트에서 검사하는 `target_path`도 실제 production target operation에 전달되지 않는다. 따라서 두 assertion은 approval callback 차단이나 target mutation을 직접 검증하지 않는다.
- **Counterevidence:** `tests/reliability/test_schema_drift_evaluation.py::test_schema_drift_evaluation_rejects_incomplete_candidate_before_approval`는 실제 evaluation caller에 `approve` callback을 연결하고, 미호출과 target state 보존을 검증한다. 따라서 approval 차단에 대한 전체 테스트 공백이나 production 취약점으로 확대하지 않는다.
- **Disposition:** 테스트 의미론 개선 후보. 위 두 테스트는 preflight rejection으로 정확히 명명하고 무의미한 sentinel을 제거하는 편이 명확하다. 수정이 필요하다면 감사 기록과 분리된 최소 테스트 PR에서 다룬다. 이번 문서 PR에는 test/source를 변경하지 않는다.

## Self Review Loop

1. **Loop 1 — Contract/coverage review:** schema recovery의 approval → candidate → target mutation 경계를 code와 spec에 연결했다. 한정된 component test의 빈 assertion을 발견했으나 처음 추정한 “approval guard 전체 미검증” 주장은 근거가 부족했다.
2. **Loop 2 — Disconfirmation/reconciliation:** 실제 caller `evaluation/schema_drift.py`와 corresponding integration test를 추가 확인해 approval callback 차단이 별도 검증됨을 확인했다. R-TD-01을 *Low test-design clarity*로 축소하고 production defect 주장을 기각했다. Immutable staged artifact라는 명칭만으로 file-system 불변성을 증명했다고 주장하지도 않았다.

이 기록은 **동일 작업 컨텍스트의 셀프 리뷰**이지, 독립 reviewer의 dual-perspective assessment가 아니다.

## Next Actions

1. 동일 baseline에서 `uv run pytest tests/reliability/test_schema_recovery_candidate.py tests/reliability/test_schema_recovery_executor.py tests/reliability/test_schema_drift_evaluation.py`를 실행하고 pass/fail/skip과 환경을 기록한다. 이번 세션에서는 실행하지 않았다.
2. Partition backfill의 complete boundary와 나머지 Reliability source/test를 목록화하고, 각 파일에 examined/excluded 근거를 남긴다.
3. R-TD-01은 중복된 실제 guard test를 확인한 뒤 수정 효용을 판단한다. 결함으로 확정하지 않고 테스트 수 증가만을 목표로 하지 않는다.

검토 기준이 이후 변경되면 해당 revision을 명시해 재검토한다.
