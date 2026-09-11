---
type: report
title: "PR 229 Issues And Blockers"
description: "PR #229의 검증 이슈를 계약별 근거에 대조하고 완료 blocker, 잔여 제한과 전달 상태를 구분한다."
tags: [orchestration, airflow, runtime-proof, evidence-gap, pr-229]
---

# PR 229 Issues And Blockers

## Summary

**2026-09-10 옵션 A 검증 결과, PR #229에 남은 기술적 완료 blocker는 확인되지 않았다.** 실제 Airflow 3.3.0 `dags test` 두 시나리오와 직접 관련된 자동화 테스트 74개를 결합해 canonical spec의 10개 Requirement(총 28개 Scenario 포함)를 requirement-level로 대조했다. 확인된 production DAG 결함, 실패한 관련 테스트 또는 필수 verification gap은 없다.

이 결론은 모든 Scenario를 scheduler daemon에서 종단 간 재실행했다는 뜻이 아니다. 두 실제 실행은 `triggered_by=TEST`이며 모든 중간 상태 전이를 연속 sampling하지 않았다. 그러나 canonical spec과 확정된 MVP는 scheduler-service 실행, 자동·주기 생성 또는 모든 Scenario의 종단 간 실측을 요구하지 않는다. 이 항목은 잔여 제한이지 blocker가 아니다.

## Resolution

| ID | Previous State | Current Assessment | Resolution Evidence |
| --- | --- | --- | --- |
| B1 | Scheduler-managed 수동 실행 증거 미확보 | **Not a blocker** | Canonical spec은 workflow behavior와 `schedule=None`을 요구하며 scheduler-service 실행을 acceptance로 지정하지 않음. 자동·주기 실행도 확정된 MVP 범위 밖 |
| B2 | 계약별 검증 근거 대조 미완료 | **Resolved** | 10개 Requirement(총 28개 Scenario 포함)를 관련 자동화 테스트와 실제 실행 범위에 대조하고 2026-09-10 관련 테스트 74개 통과 |
| I1 | 모든 TaskInstance 중간 전이를 미수집 | **Accepted limit** | Spec이 요구하는 실행 순서와 terminal failure propagation은 task start/end·state 및 자동화 테스트로 검증. 관찰하지 않은 중간 상태를 입증했다고 주장하지 않음 |
| I2 | 원본 실행 증거가 로컬 경로에만 존재 | **Residual delivery risk** | 원격 판단에 필요한 run ID, task state, Asset event, projection ID와 보호 파일 지문은 [04 실측 보고서](04-report-orchestration-actual-airflow-dagrun-proof-result.md)에 보존. 전체 로그·추출 JSON은 로컬에 유지 |
| I3 | 이전 독립 검토의 `clear` 범위가 제한적 | **Superseded evidence** | 해당 `clear`는 당시 문서 정합성에 한정. 현재 결론은 2026-09-10의 계약 대조, 테스트 실행과 후속 독립 검토를 기준으로 판단 |
| I4 | 로컬 문서와 원격 PR 전달 상태 불일치 | **Resolved** | 04~08과 tasks를 PR branch에 전달하고 PR description을 실제 validation 범위에 맞춤. 이후 live 상태는 Git/GitHub가 소유 |

완료 blocker는 목표 충족에 필요한 근거가 없는 상태를 뜻하며, 진행 blocker는 접근 불가·권한 부족·상충하는 요구사항 때문에 작업 자체를 수행할 수 없는 상태를 뜻한다. B1·B2는 에이전트가 처리할 수 없는 진행 장애가 아니었다. B2는 실제로 에이전트가 대조·검증해 해소했고, B1은 계약 확인 결과 필수 목표가 아닌 추가 신뢰 수준으로 재분류했다.

## Requirement Evidence

Canonical spec은 10개 Requirement 아래 총 28개 Scenario를 정의한다. 아래 표는 이를 Requirement 단위로 대조한 결과이며 Scenario별 1:1 traceability matrix를 별도로 보존했다는 의미는 아니다.

| Requirement | Automated Evidence | Runtime Evidence | Result |
| --- | --- | --- | --- |
| Data-plane workflow graph | `test_airflow_dag.py` | 단일 `hmda_data_plane` 실행 | Pass |
| Ordered stage execution | `test_airflow_execution.py`, `test_dbt_runner.py` | 정상 순서와 gate failure propagation | Pass |
| Execution and data update evidence | `test_airflow_execution.py` | Raw·analytics Asset event와 실패 시 analytics event 부재 | Pass |
| Domain delegation | `test_airflow_dag.py`, `test_airflow_execution.py`, `test_quality_gate.py` | 실제 task가 Data Operations boundary 실행 | Pass |
| Data quality gate execution | Data Operations·Reliability quality gate tests, `test_dbt_runner.py` | 16.1% clean 통과와 `null_spike` 차단 | Pass |
| Runtime configuration boundary | `test_config.py`, `test_airflow_execution.py` | 두 run의 explicit JSON override 적용 | Pass |
| Single pipeline orchestration owner | `test_airflow_dag.py` | Airflow DAG 실행 surface | Pass |
| Control-plane exclusion | `test_airflow_dag.py` | `schedule=None`, retry 0인 단발 실행 | Pass |
| Disabled analytics skip semantics | `test_airflow_execution.py` | 별도 runtime 실측 없음 | Pass at lowest useful test level |
| Task data boundary | `test_airflow_dag.py`, `test_airflow_execution.py` | Domain payload 대신 Asset evidence 사용 | Pass |

직접 관련된 현재 검증 명령은 다음과 같으며 74개 테스트가 모두 통과했다.

```bash
uv run pytest \
	tests/orchestration/test_airflow_dag.py \
	tests/orchestration/test_airflow_execution.py \
	tests/orchestration/test_config.py \
	tests/data_operations/test_quality_gate.py \
	tests/reliability/test_quality_gate.py \
	tests/data_operations/test_dbt_runner.py
```

## Not Blockers

- **Scheduler-service proof:** 두 run이 scheduler daemon proof가 아니라는 사실은 유지한다. 현재 계약에는 필수 acceptance로 존재하지 않는다.
- **자동·주기 실행 미구현:** 확정된 MVP 범위 밖이며 `schedule=None`을 유지한다.
- **모든 실패 경로의 Airflow 실측 부재:** 해당 동작은 가장 낮은 유효 경계의 자동화 테스트로 검증됐다. 별도 runtime 실측은 새 위험이나 요구가 생길 때 추가한다.
- **Dirty DAGRun의 failed / CLI exit 1:** 품질 차단 Scenario의 기대 결과다.
- **샘플 19행:** 선행 20행 설명을 실측값으로 정정한 사항이다.
- **Worktree 제거:** 요청된 격리·정리 조건을 충족한 결과다.
- **메인 DB·manifest 오염:** 실행 전후 SHA-256·크기·mtime_ns 불변을 확인했다.

## Delivery State

기술적 검증과 문서 전달은 완료됐다. PR의 Draft, CI, review와 mergeability는 GitHub live state가 소유하므로 Ready 전환이나 merge 직전에 다시 확인한다.

향후 scheduler-service 운영이나 영구 runtime harness가 요구되면 현재 PR의 숨은 blocker로 소급하지 않고 별도 requirement와 변경으로 평가한다.
