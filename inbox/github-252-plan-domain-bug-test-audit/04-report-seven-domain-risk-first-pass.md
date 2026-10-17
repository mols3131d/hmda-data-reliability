---
type: report
title: Seven Domain Risk Boundary First Pass
description: PR 252의 일곱 도메인에서 위험도 높은 실행 경로를 조사하고 셀프 리뷰한 범위 제한 결과입니다.
tags:
  - reliability
  - testing
  - review
---

# Seven Domain Risk Boundary First Pass

**Verdict: 전 도메인 최초 위험 경로 샘플 검토, 그러나 어느 도메인도 전수 감사 완료가 아님.** Current `main` full SHA: `8bc62fa6ec995f2e57456d55712b36ff11b1f1d9`. 기존 [schema recovery first pass](02-report-reliability-schema-recovery-first-pass.md)의 R-TD-01 외 확정된 production defect는 없다. 본 기록은 direct source/test inspection 근거이며 pytest나 재현을 수행했다는 뜻이 아니다.

## Loop Results

### L2 — Reliability: first pass only

- **Research/Target:** schema recovery: `recovery/schema_executor.py`, `recovery/schema_candidate.py`, `evaluation/schema_drift.py`; `test_schema_recovery_executor.py`, `test_schema_recovery_candidate.py`, `test_schema_drift_evaluation.py`.
- **Work/Observed:** schema recovery의 approval → preflight → lock → rollback/replay 경계를 구조적으로 대조함. R-TD-01은 component test의 no-op sentinel 문제로 한정; 다른 integration test의 approval callback guard 확인.
- **Review/Unverified:** 나머지 detection, profile, backfill, impact, evaluation 등 전수 리뷰와 실행 미완료.
- **Disposition:** 샘플 검토 후 과도한 결함 주장 없이 `in_progress`. 전체 파일별 contract·oracle·mock·failure coverage, 재현과 validation은 다음 작업에 남김.

### L3 — Data Operations: first pass only

- **Research/Target:** [runner](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/data_operations/runner.py#L118-L260), [quality gate](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/data_operations/quality_gate.py#L23-L96), [tests](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/tests/data_operations/test_dbt_runner.py#L294-L378).
- **Work/Observed:** dbt process가 shared DB mutation lock 안에서 gate 뒤에 시작되고, promotion 전 projection bytes 재검증 및 rollback tests가 있음.
- **Review/Unverified:** Full source/tests 미검토. Candidate artifact는 digest check와 copy 사이 직접 변경 race를 원칙적으로 차단하지 않는다고 source 주석이 인정함; spec contract 요구와 실제 reachability 검토 필요.
- **Disposition:** 샘플 검토 후 과도한 결함 주장 없이 `in_progress`. 전체 파일별 contract·oracle·mock·failure coverage, 재현과 validation은 다음 작업에 남김.

### L4 — HMDA Data: first pass only

- **Research/Target:** [partition](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/hmda_data/ingestion/partition.py#L51-L135), [transaction](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/hmda_data/ingestion/partition.py#L321-L381), [tests](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/tests/hmda_data/test_ingestion_partition.py#L106-L251).
- **Work/Observed:** staged source 검증 후 transaction 내부 expected content/temporal identity 비교, stale mismatch에서 rollback. 동시 writer·idempotence test 위치 확인.
- **Review/Unverified:** 전수 source/test 및 synthetic boundary 미완료; 실행·기대 DB mutation 결과 검증하지 않음.
- **Disposition:** 샘플 검토 후 과도한 결함 주장 없이 `in_progress`. 전체 파일별 contract·oracle·mock·failure coverage, 재현과 validation은 다음 작업에 남김.

### L5 — Data Platform / dbt: first pass only

- **Research/Target:** [lock](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/data_platform/duckdb.py#L28-L78), [projection](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/data_platform/artifacts.py#L24-L90), [tests](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/tests/data_platform/test_duckdb.py#L38-L158).
- **Work/Observed:** canonical DB path lock, length-prefixed artifact pair digest, alias serialization test 경계 확인.
- **Review/Unverified:** SQL helpers, dbt materialization, 전체 test와 runtime concurrency 미검토.
- **Disposition:** 샘플 검토 후 과도한 결함 주장 없이 `in_progress`. 전체 파일별 contract·oracle·mock·failure coverage, 재현과 validation은 다음 작업에 남김.

### L6 — Review AI: first pass only

- **Research/Target:** [validator](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/review_ai/validator.py#L23-L81), [service](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/review_ai/service.py#L120-L217), [tests](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/tests/review_ai/test_validator.py#L50-L140).
- **Work/Observed:** unknown evidence/incident mismatch/fact contradiction에 deterministic reject; service는 bounded context evidence IDs로 제한. utility evidence fabricated case 및 provenance failure tests 존재.
- **Review/Unverified:** utility/projection/live harness 전체 검토 및 provider live evidence 미완료.
- **Disposition:** 샘플 검토 후 과도한 결함 주장 없이 `in_progress`. 전체 파일별 contract·oracle·mock·failure coverage, 재현과 validation은 다음 작업에 남김.

### L7 — Runtime AI: first pass only

- **Research/Target:** [provider](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/runtime_ai/provider.py#L129-L198), [transport](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/runtime_ai/provider.py#L205-L263), [tests](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/tests/runtime_ai/test_provider.py#L93-L196).
- **Work/Observed:** bounded retry, per-response UTF-8 byte cap, SDK hidden retry zero, retryable/nonretryable tests 확인.
- **Review/Unverified:** SDK real timeout, network/service failure 실측 및 전체 settings/contracts review 미완료.
- **Disposition:** 샘플 검토 후 과도한 결함 주장 없이 `in_progress`. 전체 파일별 contract·oracle·mock·failure coverage, 재현과 validation은 다음 작업에 남김.

### L8 — Orchestration: first pass only

- **Research/Target:** [DAG](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/orchestration/dags/hmda_data_plane.py#L90-L166), [spec](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/openspec/specs/orchestration-pipeline/spec.md#L19-L45), [tests](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/tests/orchestration/test_airflow_execution.py#L178-L280).
- **Work/Observed:** raw → gate → analytics task dependencies, build 전 gate 재검증 및 promotion 실패 시 성공 evidence 미기록 확인; invalid runtime override는 real `tests/orchestration/test_config.py`가 별도 검증.
- **Review/Unverified:** Airflow 실제 DAG run, retry/skip matrix와 전체 테스트 미검토.
- **Disposition:** 샘플 검토 후 과도한 결함 주장 없이 `in_progress`. 전체 파일별 contract·oracle·mock·failure coverage, 재현과 validation은 다음 작업에 남김.

## Cross-Domain Self Review And Improvement

1. **Claim challenge:** L3 promotion의 digest 검사와 복사 사이 TOCTOU 가능성은 코드에 이미 명시되어 있다. 후보가 외부에 의해 실제로 변경되는 경로·contract 위반·실패 증거가 없으므로 **confirmed bug로 선언하지 않는다**.
2. **Counterevidence:** L8의 `test_invalid_runtime_request_fails_before_domain_execution`는 config 함수를 monkeypatch해 fail-fast만 본다. 그러나 `tests/orchestration/test_config.py::test_runtime_adapter_rejects_invalid_explicit_year`가 실제 validation을 별도로 호출하므로 “invalid year is untested”라고 주장하지 않는다.
3. **Source vs test:** 표제나 test 이름만을 oracle로 간주하지 않는다. 예: L2 R-TD-01은 test 내부 no-op sentinel과 실제 evaluation caller 검증을 대조해서 Low로 축소했다.
4. **Limits:** 한 소스 파일 또는 test 일부를 읽은 것은 전체 파일 및 domain audit 완료가 아니다. 같은 컨텍스트의 self-review는 독립 review로 기록하지 않는다.

## Execution Blocker

이 ChatGPT runtime에서는 private GitHub repo clone 시 `Could not resolve host: github.com`이 발생했고, local Python에 `duckdb`가 없다. 따라서 `uv run pytest`, fixture/setup, real fault-injection 및 mutation-run checks는 **Not Verified**. 문서 변경에 대한 CI Lite 통과를 domain pytest로 대체하지 않는다.

## Completion Handoff

[Checklist](03-plan-audit-completion-checklist.md)의 L2–L8은 *첫 패스 진행*이며 체크박스 미완료를 유지한다. 이후 모든 102 source / 67 test Python 파일에 examined/excluded 근거를 대조하고, test 실행·candidate repro·독립 리뷰를 거쳐야 PR 완료 판단이 가능하다. 제한 없는 audit coverage를 주장하거나 #252를 병합해서는 안 된다.
