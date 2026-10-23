---
type: review
title: Reliability Evaluation Test Design Review
description: Volume·freshness·null·schema 평가 흐름과 실패 증거·성공률·보고서 oracle을 검토합니다.
---

# Reliability Evaluation Test Design Review

> [!NOTE]
> 실제 상태·결함 복원·실패 단계의 oracle은 강하다. Schema 복구 실패가 Action PASS로 집계되며, 여러 요구사항의 부분 충족 반례가 빠져 있다.

- **Target**: Reliability evaluation과 case/report projection.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: 평가 test 4개·freshness design 1개 전체를 두 관점 독립 검토. Shared conftest도 전체 확인했고 source·Spec은 targeted 대조했다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| E1 | Major | Schema recovery 실패가 Action PASS·성공률 100%로 집계된다 | 실패 case→property→집계→Markdown FAIL까지 연결 |
| E2 | Minor | “모두 충족”과 “일부만 충족”을 구별하는 다중 항목 oracle이 없다 | 2개 중 1개만 충족하는 고정 사례 추가 |

## Subview Assessment

| Area | Representative Scenario And Oracle | Real Boundary And Limit |
| --- | --- | --- |
| Aggregation/report | 고정 성공률 `2/3`, literal Markdown row·실제 파일 write, generic failure의 Action FAIL | renderer 자기 비교만 하지는 않음; 별도 JSON golden compatibility는 이 batch 증거 아님 |
| Volume drop | deterministic fixture, clean→defect→approval→recovery→replay, file scope·stale·dbt/promotion failure | CSV·DuckDB·detector·executor·파일 promotion 실제; 대표 dbt subprocess는 stub |
| Freshness delay | 고정 timestamp, candidate 재측정, temporal drift·expired replay, acceptance 후 observation 보존 | 실제 compound recovery; downstream callback은 합성 ID |
| Null spike | exact baseline/null `0.0`·`0.05`, ambiguity·residual candidate 거부, content·null-rate·replay·promotion | 실제 DB·파일; 일부 lifecycle/failure·downstream callback 통제 |
| Schema drift | physical VARCHAR drift, complete state·2024 sentinel, stale·unlock·rollback·dbt failure | 실제 최종 DB 관측; evaluator rollback mapping은 structured exception 주입, 실제 rollback은 executor test가 소유 |
| Approval/preflight | 기존·alias DB 거부, candidate 실패 전 approval 미호출, mutation/failure evidence | fixture의 `_approved`는 binding mechanics의 증거이며 실제 사람 승인 증거 아님 |
| Design | freshness scenario→test mapping·exclusion | [design](../../../../tests/reliability/test_freshness_delay_evaluation.design.md)과 현재 test 연결; observation equality만으로 모든 no-write를 증명하지 않음 |

주요 test 근거는 [report/volume](../../../../tests/reliability/test_evaluation_report.py)의 113·152·182·403·510·555·600·671·768·825행, [freshness](../../../../tests/reliability/test_freshness_delay_evaluation.py)의 31·179·214·287·345·499행, [null spike](../../../../tests/reliability/test_null_spike_evaluation.py)의 416·452·587·763·907·938·1201·1265·1653행, [schema drift](../../../../tests/reliability/test_schema_drift_evaluation.py)의 125·178·266·331·384·428·539행이다.

### E1 — Major: Failed Recovery Action Pass

#### Locations: E1

- [test_schema_drift_evaluation.py](../../../../tests/reliability/test_schema_drift_evaluation.py)
  - incomplete candidate와 target dbt failure가 stage·mutation·reconciliation만 검사한다.
- [schema_drift.py](../../../../src/hmda_reliability/reliability/evaluation/schema_drift.py)
  - `_failure_result`는 required/remediation actions를 빈 목록으로 둔다.
- [case_result.py](../../../../src/hmda_reliability/reliability/evaluation/case_result.py)
  - `action_passed`는 subset으로 판정한다.

#### Evidence: E1

Caller [C1 probe](../validation.md#c1-failed-recovery-action-metric)에서 target dbt validation만 실패시키자 `recovery_dbt_failure`, `after_target_mutation`, `target_mutated=True`가 남았지만 `action_passed=True`였다. Clean·drift·failure report의 Action 성공률은 `1.0`, 실패 행의 Action은 `PASS`다. Generic failure adapter는 미충족 `complete_recovery`를 요구하며 [825행 테스트](../../../../tests/reliability/test_evaluation_report.py)가 FAIL을 확인하지만 별도 schema adapter에는 적용되지 않는다.

#### Impact: E1

실패 단계는 볼 수 있어도 요약 성공률과 Action 열을 따르면 실패한 복구를 성공으로 해석한다. Report 집계의 subset 수학 자체보다 schema failure case의 입력 구성과 통합 oracle이 문제다.

#### Action: E1

Schema failure의 미충족 action을 명시하고 기존 실패 시나리오에서 `action_passed=False`, 집계 count/rate와 Markdown `FAIL`을 함께 검사한다. 실제 AI 품질 판정을 추가하는 작업은 아니다.

### E2 — Minor: All Versus Any Oracle

#### Locations: E2

- [test_evaluation_report.py](../../../../tests/reliability/test_evaluation_report.py)
  - 113행의 직접 집계·렌더링 사례는 nonempty expected/required 목록이 singleton이다.
- [evaluation Spec](../../../../openspec/specs/reliability-evaluation-report/spec.md)
  - `Synthetic case aggregation`: 모든 expected incident·required action의 포함.

#### Evidence: E2

현재 `issubset` 구현은 정상이다. 다만 빈 목록 처리는 유지하면서 nonempty 목록을 any-intersection으로 바꾸면 singleton oracle은 그대로 통과할 수 있다. Expected `[volume_drop, null_spike]` 중 `[volume_drop]`만 탐지하거나 required `[x, y]` 중 `[x]`만 수행한 사례가 필요하다. Schema evaluator의 required 2개 case도 action 결과를 직접 검사하지 않는다. 전체 관련 property/report 참조를 targeted 대조했으며 mutant 실행은 하지 않았다.

#### Action: E2

두 개 중 하나만 충족하는 작은 고정 case로 property·집계 count·Markdown FAIL을 검사한다. 모든 조합을 늘리는 요구가 아니다.

## Cross-Domain Reconciliation

[Operations D1](../data-operations/README.md#d1--major-results-only-projection-drift)의 result-only hash 민감도를 이 batch는 보완하지 않는다. Volume·null promotion 사례는 두 artifact를 함께 바꾸고 freshness/schema callback은 합성 ID를 사용한다.

[Recovery R1](recovery.md#r1--major-staging-cleanup-after-commit)의 cleanup 오류가 metadata 없이 전달되면 volume/null/freshness에서는 mutation 전 실패로 잘못 투영될 수 있고, schema의 raw `OSError`는 structured case 생성 밖으로 나간다. 이는 source 경로를 대조한 영향 분석이며 evaluator에서 별도로 재현한 결과는 아니다. 같은 root cause로 연결하며 추가 결함 수로 세지 않는다.

Volume의 raw `RuntimeError` 전파는 기존 test가 명시적으로 기대한다. Null-spike의 `ValueError` 규칙을 다른 evaluator에 그대로 적용하는 후보는 기각했다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 full-body·design 검토 | Batch C 두 관점, 5파일과 shared conftest |
| ✅ Pass | 현재 정상 suite | [전체 실행 근거](../validation.md#test-execution) |
| ❌ Fail | Schema failure의 Action/report 집계 | C1 caller probe, Action PASS·성공률 100% |
| ⚪ Not Verified | all-vs-any mutant | 정적 oracle gap, 실행하지 않음 |
| ⚪ Not Verified | 실제 사람·live AI 평가 | 이 테스트의 승인·callback fixture와 다른 영역 |
