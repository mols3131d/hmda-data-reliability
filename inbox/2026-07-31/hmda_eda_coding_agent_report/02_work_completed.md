---
title: "이번 작업에서 수행한 내용"
description: "HMDA EDA fixture contract, evidence validation, memory runner, provenance와 tests 변경을 기록한다."
date: 2026-07-31
---

# 이번 작업에서 수행한 내용

## Fixture manifest contract

[src/project_pivot/hmda_data/eda_fixture.py](../../../../src/project_pivot/hmda_data/eda_fixture.py)를
수정했다.

- `HMDAEDAFixtureFile`, `HMDAEDAActivityYearCount`,
  `HMDAEDAFreshnessExpectation`, `HMDAEDAFixtureExpected` nested Pydantic model을 추가했다.
- 모든 nested model과 manifest에 `extra="forbid"`, `frozen=True`를 적용했다.
- fixture version, seed, complete schema, positive row count/row width, null rates,
  activity-year cardinality/skew, file count/file records, expected invariants를 검증한다.
- 7개 required EDA column의 schema/null coverage를 강제한다.
- expected row count, null count, activity-year count와 skew의 상호 일치를 검증한다.
- file path traversal, 파일 존재, file size, SHA-256을 검증한다.
- manifest parse/validation 실패를 `HMDADataValidationError`로 변환한다.
- deterministic fixture generation과 기존 public function 이름은 유지했다.

## Evidence validation

`validate_hmda_eda_evidence`를 확장했다.

- 7개 required schema column의 존재와 `valid` status를 확인한다.
- evidence row count를 manifest expected row count와 비교한다.
- null count와 null rate를 7개 column 모두에 대해 검증한다.
- null이 0인 column도 key가 반드시 존재해야 한다.
- activity-year count, cardinality, freshness status/timestamp를 검증한다.
- malformed evidence structure도 기존 domain validation error로 변환한다.

## Memory runner

[scripts/run_hmda_eda_memory.py](../../../../scripts/run_hmda_eda_memory.py)와
[src/project_pivot/hmda_data/eda_memory.py](../../../../src/project_pivot/hmda_data/eda_memory.py)를
수정했다.

- run directory cleanup을 `try/finally`로 보장한다.
- GNU `time` report와 worker JSON의 malformed/missing 상태를 failed run으로 기록한다.
- filesystem 오류와 preflight failure를 final report 생성 경로에 포함한다.
- 원래 원인을 `failure_reason`에 보존한다.
- GNU `time` parsing에 `LC_ALL=C`를 적용했다.
- process/resource/output validation을 함께 평가해 OOM·timeout을 pass로 처리하지 않는다.
- temporary output 후 `replace`하는 atomic write를 사용한다.

## Provenance

Memory result/report에 다음 정보를 추가했다.

- fixture version과 resolved fixture directory
- manifest SHA-256
- 선언된 모든 fixture file의 path, size, SHA-256
- schema fingerprint
- row count와 expected invariant summary
- process limit, swap limit, DuckDB memory/thread, timeout, temp-disk 조건
- run별 exit status, resource status, output validation, peak RSS, elapsed time,
  temp disk usage, failure reason
- 필요한 Python/DuckDB version만 기록하고 불필요한 local platform detail은 제거했다.

## Tests

[tests/hmda_data/test_eda_fixture.py](../../../../tests/hmda_data/test_eda_fixture.py)에
missing/unknown field, file count, incomplete null map, negative rate, row count,
activity-year cardinality/skew, changed file, deterministic fixture와 evidence
validation test를 추가했다.

[tests/hmda_data/test_eda_memory.py](../../../../tests/hmda_data/test_eda_memory.py)에
malformed GNU `time`, malformed/missing worker JSON, success/failure cleanup,
provenance report, preflight failure report test를 추가했다.
