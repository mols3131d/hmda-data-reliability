---
title: "HMDA EDA Coding Agent Task"
description: "HMDA EDA fixture contract와 process-level memory runner의 검증 공백을 수정하기 위한 coding agent 작업 지시서"
date: 2026-07-31
---

# HMDA EDA Coding Agent Task

## Mission

HMDA EDA memory-budget validation의 false pass 가능성과 실패 시 evidence 유실
문제를 수정한다.

이번 작업은 다음 세 가지를 달성해야 한다.

1. Fixture manifest의 필수 대표성 및 correctness contract를 실제 validation에서
   강제한다.
1. Memory runner가 실패 경로에서도 temp resource를 정리하고 최종 failure
   report를 남기도록 한다.
1. 저장된 memory report를 실제 fixture bytes와 재현 가능하게 연결한다.

> [!WARNING]
> 5M-row representative fixture가 3 GiB process budget 안에서 통과했다는 사실을
> full source 약 4.8 GiB의 memory safety 보장으로 확대하지 않는다. 이번 작업은
> fixture contract와 memory evidence 품질을 개선하는 작업이며, full-source
> memory budget을 새로 보장하는 작업이 아니다.

## Target Files

### Must inspect

- [src/project_pivot/hmda_data/eda_fixture.py](../../../src/project_pivot/hmda_data/eda_fixture.py)
- [tests/hmda_data/test_eda_fixture.py](../../../tests/hmda_data/test_eda_fixture.py)
- [scripts/run_hmda_eda_memory.py](../../../scripts/run_hmda_eda_memory.py)
- [src/project_pivot/hmda_data/eda_memory.py](../../../src/project_pivot/hmda_data/eda_memory.py)
- [tests/hmda_data/test_eda_memory.py](../../../tests/hmda_data/test_eda_memory.py)
- [openspec/specs/hmda-eda-baseline/spec.md](../../../openspec/specs/hmda-eda-baseline/spec.md)

### Reference only

- [src/project_pivot/hmda_data/eda.py](../../../src/project_pivot/hmda_data/eda.py)
- [notebooks/eda_mo.py](../../../notebooks/eda_mo.py)
- [notes/artifacts/hmda_eda_fixture_manifest.json](../hmda_eda_fixture_manifest.json)
- [notes/artifacts/hmda_eda_memory_report.json](../hmda_eda_memory_report.json)
- [notes/artifacts/2026-07-31/hmda_eda_baseline_completion_report.md](hmda_eda_baseline_completion_report.md)

## Scope

### 1. Strengthen fixture manifest contract

Update `src/project_pivot/hmda_data/eda_fixture.py`.

Required behavior:

- Replace unbounded `dict[str, Any]` fields with typed nested Pydantic models where
  practical.
- Enforce the required fixture fields from the canonical spec:
  - fixture version
  - seed
  - complete schema column list
  - positive row count
  - positive row width
  - null rates
  - activity-year cardinality
  - activity-year skew
  - file count and file records
  - expected row count
  - expected required-column null counts
  - expected activity-year counts
  - expected freshness state
- Enforce complete required-column coverage for all seven EDA columns:
  `activity_year`, `state_code`, `county_code`, `loan_purpose`, `action_taken`,
  `loan_amount`, `income`.
- Reject manifests when:
  - required keys are missing
  - extra or unknown keys make the contract ambiguous
  - `file_count` differs from the file record count
  - declared file size or SHA-256 differs from the actual file
  - expected row count differs from manifest row count
  - expected null-count keys are incomplete
  - expected activity-year counts do not agree with cardinality or skew keys
  - activity-year skew is not within valid bounds or does not sum to approximately 1
- Preserve deterministic fixture generation and existing public function names unless
  a signature change is strictly necessary.

### 2. Strengthen evidence validation

Update `validate_hmda_eda_evidence` and related tests.

Required behavior:

- Validate required schema status for all seven required EDA columns.
- Validate evidence row count against manifest expected row count.
- Validate null counts for all seven required EDA columns, including zero-null fields.
- Validate null rates when the manifest declares them.
- Validate activity-year counts, cardinality, and freshness state.
- Keep validation read-only with respect to source data.
- Raise the existing domain validation error type for invalid fixture or evidence
  contracts.

### 3. Make memory runner failure-safe

Update `scripts/run_hmda_eda_memory.py` and, where needed,
`src/project_pivot/hmda_data/eda_memory.py`.

Required behavior:

- Guarantee per-run temporary directory cleanup with `try/finally`.
- Convert timing report parse errors, worker output JSON errors, missing output files,
  and filesystem errors into a run-level failed result where practical.
- Continue to final assessment/report generation when a run fails because of malformed
  auxiliary output. Do not hide the original failure reason.
- Set a stable locale for GNU `time` parsing, such as `LC_ALL=C`.
- Preserve systemd hard-limit, swap, timeout, DuckDB memory, thread, and temp-disk
  evidence.
- Keep existing rule: incomplete output or failed invariant means memory-budget failure.
- Do not classify an OOM or timeout as a passing run merely because a process exited.

### 4. Add evidence provenance

Update the memory result/report contract.

The final report must include enough information to identify the exact input used:

- fixture version
- resolved fixture directory
- manifest SHA-256
- fixture file SHA-256 for every declared file
- fixture file size for every declared file
- schema fingerprint or equivalent manifest schema digest
- row count and expected invariant summary
- process and DuckDB resource conditions
- per-run exit status, resource status, output validation, peak RSS, elapsed time,
  temp disk usage, and failure reason when present

Do not expose secrets or unrelated local environment details.

## Tests to Add or Update

Update [tests/hmda_data/test_eda_fixture.py](../../../tests/hmda_data/test_eda_fixture.py)
with focused tests for:

- missing required manifest field is rejected
- incomplete required-column null-count map is rejected
- inconsistent row count is rejected
- inconsistent activity-year cardinality/skew is rejected
- invalid skew sum or negative rate is rejected
- changed fixture file is rejected
- valid deterministic fixture remains accepted

Update or add focused tests for memory runner behavior:

- malformed GNU `time` report becomes a failed run result
- malformed or missing worker JSON becomes a failed run result
- temp run directory is removed after both success and failure
- final report includes failure evidence when a run fails
- fixture and manifest digests are included in the report
- existing three-run assessment semantics remain unchanged

Prefer small unit/component tests over launching the full 5M-row memory workload in
ordinary pytest. Keep the `memory` marker isolated from the default test suite.

## Acceptance Criteria

The task is complete only when all conditions below are true.

- [ ] Manifest validation rejects missing or inconsistent required fields.
- [ ] All seven required EDA columns participate in null-count validation.
- [ ] Activity-year cardinality and skew are validated, not merely recorded.
- [ ] Source file size and SHA-256 validation remain enforced.
- [ ] Memory runner cleans every run directory on success and handled failure paths.
- [ ] Malformed auxiliary output cannot silently produce a passing memory result.
- [ ] Final report contains fixture and manifest provenance digests.
- [ ] Existing public EDA behavior remains compatible unless a contract correction
      requires otherwise.
- [ ] Focused tests pass.
- [ ] Ruff check and type check pass for changed Python files.
- [ ] Markdown formatting passes for this document if it is modified.
- [ ] The final response names changed files, tests run, and any unverified boundary.

## Validation Commands

Run the narrowest checks first:

```bash
uv run pytest -n 0 \
  tests/hmda_data/test_eda_fixture.py \
  tests/hmda_data/test_eda_memory.py
```

Then run the broader HMDA EDA correctness slice:

```bash
uv run pytest -n 0 \
  tests/hmda_data/test_eda.py \
  tests/hmda_data/test_eda_fixture.py \
  tests/hmda_data/test_eda_memory.py
```

Run static checks for changed Python files:

```bash
uv run ruff check \
  src/project_pivot/hmda_data/eda_fixture.py \
  src/project_pivot/hmda_data/eda_memory.py \
  scripts/run_hmda_eda_memory.py \
  tests/hmda_data/test_eda_fixture.py \
  tests/hmda_data/test_eda_memory.py
```

If the repository has a configured type checker, run it for the changed Python
surface. Do not claim the 5M-row process-level memory gate was rerun unless it was
actually executed under the documented hard-limit runner.

Format this document with:

```bash
uv run rumdl fmt notes/artifacts/2026-07-31/hmda_eda_coding_agent_task.md
```

## Out of Scope

Do not:

- modify the raw HMDA source data
- change the Marimo UI layout unless a contract change requires it
- claim full-source memory safety
- add a new profiling framework
- change reliability lifecycle behavior
- change OpenSpec canonical requirements without an explicit contract decision
- commit changes or create a branch unless separately requested

## Final Response Format

Report the result briefly in Korean:

1. changed files
1. behavior fixed
1. tests and checks run
1. remaining limitations

Include any failed command and its relevant cause. Do not report a check as passed if
it was not executed.
