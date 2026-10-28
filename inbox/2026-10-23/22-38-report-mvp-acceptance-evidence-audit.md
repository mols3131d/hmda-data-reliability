---
type: report
title: "MVP Acceptance Evidence Audit"
description: "2026-10-23 기준 checkout SHA에서 MVP 수용 기준 10개의 구현·검증·human evidence를 판정합니다."
tags:
  - mvp
  - acceptance
  - evidence
---

# MVP Acceptance Evidence Audit

> [!IMPORTANT]
> **현재 checkout SHA에서 MVP 완료는 입증되지 않았다.** 10개 기준 중 5개는 충족, 1개는 미충족, 3개는 차단, 1개는 미확인이다. 차단·미확인 항목은 코드가 실패했다는 뜻이 아니라 현재 SHA에 필요한 live 또는 사람의 증거가 없다는 뜻이다.

## Audit Target

- **Date:** 2026-10-23 (Asia/Seoul)
- **Branch:** `agent/test/cover-sdk-retry-classification`
- **HEAD:** `b6b47606bdabf69221eff94c8f9c69dc03b6cc57`
- **Ref check:** local `origin/agent/test/cover-sdk-retry-classification`도 같은 SHA를 가리킨다.
- **Working tree:** tracked diff 없음. 기존 untracked `.private/`는 읽거나 변경하지 않았다.
- **Acceptance owner:** [MVP acceptance](../../docs/mvp.md#L101-L119). 구현 증거는 현행 source/test 실행과 local artifact에서 확인했고, 과거 Inbox·무시된 artifact는 현재 SHA의 proof로 승격하지 않았다.

MVP 문서는 현재 acceptance만 소유하며 구현 상태를 소유하지 않는다. 여기서는 기준을 바꾸지 않고, 기준별 현행 증거와 공백을 보고한다. 상태는 `충족`=현행 SHA에서 기준에 직접 대응하는 실행 증거 확인, `미충족`=관찰한 증거가 요구된 proof 종류에 못 미침, `차단`=live provider 또는 사람의 별도 행동이 필요, `미확인`=현행 SHA에 연결된 증거를 찾지 못해 상태를 확정할 수 없음으로 사용한다.

## Acceptance Verdicts

| # | Acceptance proof | Status | Evidence and reason |
| ---: | --- | --- | --- |
| 1 | Data Lake: HMDA source → Bronze → dbt analytical layer | **충족** | 현행 SHA에서 ingestion, real dbt, system E2E 및 실제 Airflow DAGRun 검증을 포함한 선택 테스트 91건이 통과했다. [system E2E](../../tests/data_operations/test_system_recovery_e2e.py#L264)와 [성공 DAGRun](../../tests/orchestration/test_airflow_dagrun.py#L320)은 source load, staging/mart row oracle과 dbt artifact를 확인한다. 이 증거는 테스트가 생성한 HMDA 형식 fixture에 대한 것이다. 실제 전체 local source를 현행 SHA에서 다시 처리한 결과까지 주장하지 않는다. |
| 2 | Reliability: synthetic incident 탐지·설명, 승인 뒤 recovery, 재검증 | **충족** | 같은 91건 실행에 [system recovery E2E](../../tests/data_operations/test_system_recovery_e2e.py#L264)와 [real dbt evaluator E2E](../../tests/data_operations/test_system_recovery_e2e.py#L424)가 포함됐다. null spike gate, read-only lifecycle, candidate dbt 검증, proposal-bound typed approval, recovery, post-recovery gate와 replay를 다룬다. approval은 테스트 fixture이므로 실제 사람의 승인 행위까지 증명하지 않는다. |
| 3 | Agentic contract: structured review, evidence binding, validation, evaluation | **충족** | 현행 SHA의 Review AI/Runtime AI 선택 테스트 199건이 통과했다. [service tests](../../tests/review_ai/test_service.py), [validator tests](../../tests/review_ai/test_validator.py), [evidence store tests](../../tests/review_ai/test_evidence_store.py), [utility evaluation tests](../../tests/review_ai/evaluation/test_utility_evaluation.py#L193)가 output/evidence 연결, contradiction·injection 처리, typed failure, immutable provenance, rubric/comparison contract를 검증한다. offline suite는 live provider 품질을 대신하지 않는다. |
| 4 | Live Agentic: 동일 revision의 accepted model invocation과 provenance | **차단** | [live runner](../../scripts/run_agentic_review_live.py)의 provider opt-in 실행은 이번 감사에서 하지 않았다. 로컬 invocation 기록 3개는 모두 다른 revision(`c7ceeddf`, `632790e0`, `2c3b61cd`)이며 `validation_failed`다. HEAD `b6b47606`에서 accepted invocation artifact는 확인되지 않았다. 현재 출력은 live acceptance proof가 아니다. |
| 5 | Safety: AI가 guardrail·proposal-bound approval을 우회해 mutation하지 않음 | **충족** | 현행 SHA의 통합·Review AI 선택 테스트가 통과했다. [approval safety tests](../../tests/data_operations/test_system_recovery_e2e.py#L484)는 거부·identity/action mismatch에서 target identity 보존을 확인하고, [Review AI dependency boundary tests](../../tests/review_ai/test_dependency_boundaries.py)와 validator tests는 advisory/output 경계를 확인한다. |
| 6 | Reproducibility: 정상·incident·recovery·failure/retry와 live 결과를 같은 SHA에 보존 | **차단** | deterministic 부분은 현행 SHA의 91/199 선택 테스트에서 통과했고 system E2E가 recovery/replay를 재실행했다. 그러나 acceptance에 포함된 live invocation 결과는 현행 SHA에 없다. 과거의 failed invocation artifact는 exact-head live 재현 증거가 아니다. |
| 7 | Review context: incident 주변 bounded evidence, provenance, missing/unconfirmed 구분 | **충족** | 현행 SHA의 [context tests](../../tests/review_ai/test_context.py#L66)는 `test_context_selects_related_evidence_and_preserves_provenance`, `test_context_distinguishes_missing_evidence_from_unconfirmed_context`, `test_context_is_bounded_and_replayable`를 검증한다. 선택 근거, 출처와 digest를 확인한다. |
| 8 | Agentic utility: deterministic 재진술을 넘는 실제 review 기여 | **미충족** | 현재 확인된 utility bundle `.local/artifacts/agentic-review/utility/proofs/review-ai-utility-proof-v1.json`은 revision `b9143eba`의 fixture 비교다. `output_fixture_id`와 고정된 baseline/candidate 출력·점수는 fixture contract proof이지 현행 SHA의 실제 model review가 아니다. 현행 SHA에서 사람이 다음 판단에 쓸 추가 기여를 낸 accepted output을 확인하지 못했다. |
| 9 | Quality evaluation: versioned human rubric을 실제 사례에 적용하고 재실행 | **차단** | 현행 SHA의 [utility evaluation tests](../../tests/review_ai/evaluation/test_utility_evaluation.py#L193)는 `rubric_v1` 다섯 criterion과 output digest 계약을 검증한다. 하지만 그 점수는 테스트 fixture이며, 실제 사람이 accepted output을 평가한 현행 SHA 기록은 없다. [평가 가이드](../../docs/development/review-ai-evaluation.md#L61)는 score 판단이 사람의 책임이며 offline test가 human utility assessment를 대신하지 않는다고 명시한다. 실제 사례 채점과 근거 기록이 필요하다. |
| 10 | Change comparison: 같은 case/rubric의 baseline·candidate를 비교하고 채택 근거 보존 | **미확인** | 현행 SHA의 [comparison implementation](../../src/hmda_reliability/review_ai/evaluation/value.py#L217)과 [comparison tests](../../tests/review_ai/evaluation/test_utility_evaluation.py#L317)는 동일 case, revision, role, deterministic facts 및 output digest를 검증한다. 확인된 로컬 비교 bundle은 revision `b9143eba`의 fixture 결과이고 HEAD와 다르다. 현행 SHA에 연결된 실제 사람의 comparison/decision 기록은 찾지 못했다. Langfuse/원격 annotation은 이번 세션에 조회 가능한 도구가 없어 확인하지 않았다. |

## Current-SHA Validation

2026-10-23에 VS Code Test Controller로 현재 checkout에서 실행했다. 기록은 선택 범위에 한정하며 전체 suite나 CI 성공으로 일반화하지 않는다.

| Run | Selected scope | Result |
| --- | --- | --- |
| Data pipeline / recovery | HMDA ingestion·partition, dbt runner, system recovery E2E, Airflow DAGRun, approval backfill validation 6개 파일 | **91 passed / 0 failed** |
| Review / runtime AI | `tests/review_ai` 및 `tests/runtime_ai`의 계약·context·service·validator·store·live harness·utility evaluation·provider/settings 14개 파일 | **199 passed / 0 failed** |

## Evidence Freshness And Limits

- 현행 checkout은 `b6b47606bdabf69221eff94c8f9c69dc03b6cc57`다. 두 test run 모두 이 checkout에서 수행했다.
- 같은 local artifact 디렉터리의 live invocation은 2026-09-21 및 2026-10-02 기록이다. 모두 현행 SHA가 아니며 확인된 상태는 `validation_failed`; 10월 2일 두 기록의 failure code는 `response_schema_invalid`다.
- local utility bundle도 `.gitignore` 대상이며 project revision `b9143ebab1735e77594d2b00bcb5f52d8d453eb3`에 묶여 있다. 현행 proof나 versioned repository evidence로 취급하지 않았다.
- [HMDA EDA observation](../../docs/references/hmda_eda.md)은 revision `17522ddc`의 2026-08-08 source observation이다. actual-source EDA 기록이며 현행 SHA의 Bronze→dbt E2E를 증명하지 않는다.
- 선택 테스트는 통과했지만 full suite와 현재-head CI 결과는 이 감사에서 수집하지 않았다. 실제 provider 실행, 사람의 rubric 채점·comparison, 원격 Langfuse annotation도 수행·조회하지 않았다.

## Remaining Evidence To Close MVP Acceptance

1. 현행 SHA를 고정한 accepted live invocation을 실행하고 sanitized invocation evidence를 보존한다.
1. 그 accepted output을 사람이 `rubric_v1` 다섯 항목으로 채점하고 rationale을 기록한다.
1. 동일한 representative case/rubric에서 baseline과 candidate를 비교하고 사람의 decision 및 근거를 현행 SHA에 연결한다.
1. 같은 current revision에 해당하는 live record와 deterministic rerun을 함께 보존해 reproducibility proof를 닫는다.
1. 실제 full local HMDA source 처리까지 MVP의 Data Lake 기준에 요구된다면, 테스트 fixture 증거와 분리해 해당 실행 및 source identity를 추가 확인한다.
