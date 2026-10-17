---
type: report
title: Domain Audit Remediation Loops
description: PR 252 결함 수정 루프의 실행 근거, 검토 결과와 다음 전이를 기록합니다.
---

# Domain Audit Remediation Loops

## Current State

Phase: RPI Main Loop. Loops used: 2/30. Acceptance: open. Next: R-SCH-01 post-commit failure evidence regression.

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
