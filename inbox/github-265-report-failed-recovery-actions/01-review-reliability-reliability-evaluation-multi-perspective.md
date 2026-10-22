---
type: review
title: PR #265 Recovery Action Evaluation Multi-Perspective Review
description: PR #265의 실패한 schema recovery action 집계와 렌더링 계약을 다관점으로 검토합니다.
tags:
  - domain:reliability
  - capability:reliability-evaluation
---

# PR #265 Recovery Action Evaluation Multi-Perspective Review

> [!IMPORTANT]
> **Blocked** — 코드·계약 대조에서 필수 수정 finding은 확인되지 않았습니다. 실패 사례에 비어 있지 않은 필수 action을 부여해 False PASS를 막고 정상 clean 사례는 유지합니다. 다만 이번 세션에서 독립 subagent review를 재실행할 수 없어 독립 리뷰 게이트는 미충족입니다.

- **Target** — [PR #265](https://github.com/mols3131d/hmda-data-reliability/pull/265)
- **Revision** — base `34519fec148dd2ab38ddf0cc0157c3d3ed9f7247` / reviewed head `4969725ba2c8782f69a24c2eda1fa3f8c35254ab`
- **Scope** — Schema-drift failure case action mapping, `EvaluationCaseResult`의 subset 판정, aggregate/Markdown 결과, 회귀 테스트와 CI.

## Findings

현재 승인된 변경 범위에서 확인된 `current_required` finding 없음. 코드 관점 assessment: `clear`; 최종 독립-review gate: `blocked` (separate specialist coverage 미검증). 잠재 위험은 아래 Candidate Decisions와 Risks and Limits에서 분리합니다.

## Perspectives

| Perspective | Reviewer / Method | Focus | Assessment and Evidence |
| --- | --- | --- | --- |
| Correctness | 동일 세션, 정본→코드 추적 | 실패 action의 판정 경계 | [schema_drift.py](../../src/hmda_reliability/reliability/evaluation/schema_drift.py)의 `_failure_result`가 `required_actions=["complete_recovery"]`를 부여하며 실패 case의 `remediation_actions=[]`와 subset 결과가 거짓이 됨 |
| Adversarial | 동일 세션, 반례 검토 | clean·success 회귀 및 오류 stage 보존 | [case_result.py](../../src/hmda_reliability/reliability/evaluation/case_result.py)의 기존 subset 계산을 그대로 사용; 새 assertion이 clean 성공과 dbt failure evidence를 구분 |
| Evidence/Reporting | 동일 세션, 테스트·CI 검토 | case→aggregate→Markdown | [회귀 테스트](../../tests/reliability/test_schema_drift_evaluation.py)가 2/3·66.67% 및 Markdown Action FAIL을 확인; CI Lite 성공 |

## Candidate Decisions

| ID | Perspectives | Candidate | Decision | Rationale | Finding |
| --- | --- | --- | --- | --- | --- |
| C1 | Correctness, Adversarial | 실패 복구에서 required-actions가 비어 Action PASS가 됨 | Drop | 이번 diff가 `_failure_result`에 `complete_recovery`를 요구하고 실패 경로에 성공 action이 추가되지 않으므로 기존 false-green 경로가 닫힘 | — |
| C2 | Adversarial | 일반 subset 판정 자체를 바꿔야 함 | Drop | 오류 원인은 실패 case의 입력 mapping이며 일반 판정 변경은 정상 clean의 empty-set 의미를 훼손하고 in-scope correction이 아님 | — |
| C3 | Evidence/Reporting | case만 실패하고 집계·Markdown은 여전히 100%일 수 있음 | Drop | 수정된 통합 assertion이 `action_passed_cases == 2`, 성공률 `2/3`, 렌더링 Action `FAIL`을 함께 검사 | — |

같은 세션에서 **1차 계약·구현 확인 → 2차 반례·회귀·운영 경계 재검토 → 후보 재판정** 순으로 수행했습니다. 서로 다른 관점은 서로 독립된 subagent 실행을 의미하지 않습니다. `Drop`은 반례 무효화, 기존 safeguard 확인 또는 본 PR의 승인 범위 밖임을 뜻합니다. `Open`은 해결로 간주하지 않습니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Source + canonical contract 정적 검토 | [`_failure_result`](../../src/hmda_reliability/reliability/evaluation/schema_drift.py)와 [evaluation report spec](../../openspec/specs/reliability-evaluation-report/spec.md) |
| ✅ Pass | 회귀 oracle 검토 | [`test_schema_drift_evaluation.py`](../../tests/reliability/test_schema_drift_evaluation.py)에서 DBT failure의 result→report→Markdown, clean success와 원래 error evidence assertion 확인 |
| ✅ Pass | 원본 HEAD CI Lite | [Run 39142659312](https://github.com/mols3131d/hmda-data-reliability/actions/runs/39142659312) `check=success` (원본 HEAD) |
| ⚪ Not Verified | 테스트 직접 재실행 | 이번 세션에서 pytest/ruff/ty/tach를 로컬 실행하지 않았음 |
| ⚪ Not Verified | 독립 reviewer 재수행 | PR 설명의 DualVantage 수행 주장은 있으나 이번 세션은 동일 컨텍스트 다관점 분석이며 별도 worker 기록을 검증하지 못함 |

## Risks and Limits

- 이 문서는 원본 HEAD의 정적 코드·테스트 및 CI 증거에 대한 리뷰입니다. 독립 worker가 수행한 결과를 이 리뷰의 독립 coverage로 대체할 수 없습니다.
- 원본 코드와 다른 HEAD가 되면 변경된 부분에 대한 CI·리뷰 증거를 새 revision으로 재확인해야 합니다.
- **Next:** 별도 독립 검토 증거 확인 → 인간 리뷰; 수정 요청이 없다면 추가 production-code 변경을 요구하지 않습니다.

이 보고서는 비정본 리뷰 산출물입니다. 본문에 기록된 원본 HEAD 이후 보고서 커밋이나 후속 PR 병합으로 검증 state가 바뀌면 review readiness와 CI를 새 revision 기준으로 다시 판단해야 합니다.
