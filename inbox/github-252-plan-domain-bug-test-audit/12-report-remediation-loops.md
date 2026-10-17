---
type: report
title: Domain Audit Remediation Loops
description: PR 252 결함 수정 루프의 실행 근거, 검토 결과와 다음 전이를 기록합니다.
---

# Domain Audit Remediation Loops

## Current State

Phase: RPI Main Loop. Loops used: 3/30. Acceptance: open. Next: R-TD-02 actual SDK adapter test and negative control.

Starting revision과 scope는 [11](11-plan-remediation-execution.md), 실행할 항목은 [03](03-plan-audit-completion-checklist.md)을 따른다. 아래 실행은 실제 수행 후 결과와 검토 근거를 기록한다. 과거 [08](08-report-cloud-validation.md)의 수치를 이번 실행으로 표현하지 않는다.

## Loop 1 — HMDA Source Column Mapping

- Research: `_replace_partition_rows`는 staging의 column order대로 insert했고 input union의 BY NAME은 target order를 보호하지 않았다. 원천 값 보존과 transaction rollback의 기존 계약을 적용했다.
- Plan/Work: 기존 partition test에 CSV header 재정렬과 exact values·다른 연도 partition 전체 row 보존 oracle을 추가했다. Production 변경은 `INSERT ... BY NAME` 한 곳이다.
- RED: `tests/hmda_data/test_ingestion_partition.py::test_partition_reload_preserves_values_after_source_columns_are_reordered -q` → 1 failed, 값 `(95, 420000)`이 기대 `(350000, 120)` 대신 나타난 assertion 실패. 환경/collection 오류가 아니다.
- GREEN: 같은 module 14 passed; `tests/hmda_data -q` 77 passed. `.venv/bin/python -m pytest`로 실행했고 기본 memory/stress 제외 정책을 유지했다.
- Review: public load result의 값과 unrelated partition을 직접 검증한다. 기존 stale-state·rollback 회귀가 통과했다. 내부 SQL 문자열을 고정하지 않는다. 독립 최종 리뷰는 아직 남아 있다.
- Dispatch: I1 local implementation/validation 완료, 다음 R-REV-01. 이 상태를 최종 PR 완료로 표현하지 않는다.

## Loop 2 — Review Parser Failure Provenance

- Research: output byte limit 안의 deep JSON(20,001 bytes)와 큰 정수 JSON(5,006 bytes)이 `json.loads`의 RecursionError/ValueError로 evidence 저장을 우회한다. 기존 response-schema-invalid 경로와 저장 정책을 재사용한다.
- Work: public review service test 두 case에서 typed failure, provider 1회, invocation path와 load된 record metadata, raw output 미저장을 확인한다. Parser/model validation의 좁은 try에서 ValueError(JSON/Pydantic validation 포함), TypeError, RecursionError만 처리한다.
- RED: 새 parameterized test 2 failed, 실제 RecursionError와 integer conversion ValueError. GREEN: service module 18 passed, `tests/review_ai -q` 159 passed.
- Review: input rejection·provider unavailable·accepted review·provenance failure의 기존 회귀가 유지됐다. MemoryError 같은 process failure를 무차별 catch하지 않는다. Provider stub이므로 live model evidence가 아니다.
- Dispatch: I2 local implementation/validation 완료. 다음 schema executor/evaluator의 commit 이후 실패 상태와 안전한 replay.

## Loop 3 — Schema Recovery Cleanup Failure

- Research: executor의 with 종료에서 unlock 또는 DuckDB close가 실패하면 이미 commit된 결과까지 before-target failure로 분류했다. Evaluator는 recovery 예외를 무조건 `target_mutated=False`로 기록했다.
- Plan/Work: 완료한 typed result를 resource 종료까지 보존하고 해당 cleanup 예외에 after-target/replay stage, mutation state, actual state와 resume-verification을 연결한다. 아직 완료 결과가 없는 lock 획득·검증 실패는 기존 의미를 유지한다. Evaluator는 해당 예외의 table-replaced evidence를 읽는다.
- RED: executor의 before/after state × unlock/close 4 cases가 실제 DB after-state와 metadata 불일치로 실패. Actual executor를 거치는 evaluator unlock case도 RED였다. Executor 수정 뒤 evaluator의 target-mutated assertion이 추가로 RED여서 projection 누락까지 확인했다.
- GREEN: candidate/executor/schema-drift evaluator 3 modules, `-q -n 2` → 36 passed. Fault 제거 후 동일 승인 replay는 already-restored이고 executed actions는 profile 재실행뿐이다.
- Review: approval mismatch·diverged state·rollback 경계는 기존 회귀를 유지한다. Test는 OS lock/connection 종료 boundary만 제어하고 actual DB mutation과 identity를 사용한다. 완료 결과가 없는 오류를 commit됐다고 추정하지 않는다.
- Dispatch: I3 local implementation/validation 완료. 전체 runtime validation과 independent assessment는 아직 남아 있다.
