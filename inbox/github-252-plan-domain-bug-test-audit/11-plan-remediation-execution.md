---
type: plan
title: Domain Audit Remediation Execution
description: PR 252의 확인된 결함 수정, 회귀 검증과 세션 간 재개를 위한 실행 계획입니다.
tags:
  - reliability
  - testing
---

# Domain Audit Remediation Execution

## Goal And Scope

사용자는 2026-10-17 PR #252 branch에서 실제 작업을 진행하고 Inbox artifact를 남기며 루프를 수행하도록 요청했다. 감사 이력은 [08](08-report-cloud-validation.md)과 [09](09-review-cloud-audit.md), 완료 공백은 [10](10-review-pr252-completion-readiness.md)을 따른다. 기존 감사 완료와 제품 수정 완료를 구분한다.

- Owning ref: `agent/docs/plan-domain-bug-test-audit`.
- Starting head: `5e313244f05d5bcd2967f55cc6904039eafba6af`; audit source baseline: `8bc62fa6ec995f2e57456d55712b36ff11b1f1d9`.
- 이번 작업은 확인된 다섯 finding과 Airflow 검증에 한정한다. 사용자 지정 branch에서 finding별 독립 commit으로 진행한다. 새 기능, AI 위임 권한, unrelated cleanup과 의존성 변경은 포함하지 않는다.
- 기존 active OpenSpec change 두 개는 evaluation refactor와 optional projection을 소유한다. 해당 목적을 다시 구현하지 않으며 기존 canonical contract의 결함을 좁게 수정한다. 새 계약 결정이 필요한 detector는 결정 전 수정하지 않는다.
- 외부 provider/Langfuse live 호출은 포함하지 않는다. 기존 local evidence와 optional live proof를 혼동하지 않는다.

## Prepare

Readiness: READY WITH LIMITS. 기존 Python 3.13 venv에 DuckDB 1.5.5, pytest 9.1.1이 준비돼 있다. Interpreter가 기본 sandbox 밖에 있어 실행 시 승인된 환경 접근을 사용한다. Airflow의 정상 runner 여부는 아직 검증하지 않았다.

Run: standard intensity, max_loops=30, loops_used=0. Main Loop는 Research → Plan → Work → Review이며 substantive review 종료 때만 counter를 증가시킨다. 최종 구현 완료는 별도 review-lead의 independent assessment와 validation을 필요로 한다.

## Work And Acceptance

| Order | Finding / owner | Planned change | Acceptance oracle |
| --- | --- | --- | --- |
| 1 | R-HMDA-01 / HMDA ingestion | Partition insert를 column name에 연결 | 재정렬 CSV의 exact values 보존, 다른 partition 불변, 실패 시 rollback |
| 2 | R-REV-01 / Review AI | JSON parser의 제한 초과 예외를 기존 typed validation failure로 변환 | deep JSON/huge integer에서 provider 1회, validation_failed와 persisted invocation; 성공 경로 유지 |
| 3 | R-SCH-01 / Reliability, Data Platform | Commit 이후 lock release failure의 mutation evidence를 보존 | executor와 evaluator의 committed state, verification pending, 동일 승인 replay의 no second mutation |
| 4 | R-TD-02 / Runtime AI tests | 실제 SDK adapter를 fake client와 연결해 검증 | kwargs/응답/오류 계약; 잘못된 model mapping을 주입한 negative control이 실패 |
| 5 | R-DET-01 / Reliability detection | 0의 계약 결정 후 최소 수정 | 선택된 계약에 따른 unchanged/positive degradation/threshold equality 검증; R-DET-02는 별도 Note 유지 |
| 6 | Orchestration | 정상 proc/filesystem 환경에서 DAGRun 5개 재실행 | ordering, failure blocking, promotion/asset evidence; 실패하면 environment와 production 분류 |

Detector `0` 허용 + 양의 악화만 탐지와 `0` 거부 중 사용자 선택을 비동기로 요청했다. 답변은 결정 근거로 기록하며 기다리는 동안 다른 finding을 진행한다.

각 단위는 기존 test area에 독립 oracle을 추가해 RED를 확인하고 production의 최소 변경 후 GREEN을 확인한다. 최소 focused test 다음 관련 suite를 실행한다. 최종에는 full non-resource suite, Ruff/format, type/Tach와 실제 변경에 해당하는 repository checks를 수행한다. 환경 실패는 제품 성공으로 바꾸지 않는다.

## Completion And Resume

다섯 finding별 구현·회귀 검증과 최종 통합/독립 리뷰가 완료되거나, 사용자에게 미해결 decision/evidence를 명확히 전달해야 한다. 단순 owner 기록으로 구현 완료를 선언하지 않는다. 기존 approval/Ready/merge 권한은 사람에게 남긴다.

현재 열린 작업은 [03](03-plan-audit-completion-checklist.md), loop 근거는 [12](12-report-remediation-loops.md), 정확한 재개 지점은 [07](07-report-domain-audit-session-handoff.md)이 소유한다. Material state 변화마다 이 문서를 재생성하지 않고 해당 owner를 갱신한다. Artifacts와 코드는 논리적 checkpoint commit으로 보존하며 원격 전달은 같은 PR branch에서 수행한다.
