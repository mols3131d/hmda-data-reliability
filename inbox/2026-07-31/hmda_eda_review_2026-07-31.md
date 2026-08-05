---
title: "HMDA EDA Baseline Review"
date: 2026-07-31
---

# HMDA EDA Baseline Review

## Conclusion

HMDA EDA baseline은 공유 계산 entrypoint, read-only lifecycle, deterministic
fixture, process-level hard limit, 3회 memory workload 실행을 갖췄다. 완료
보고서도 fixture-level 3 GiB 통과를 full-source 보장으로 확대하지 않고,
full-source uncontrolled peak RSS 약 12.44 GiB를 별도로 명시한다.

다만 fixture manifest의 대표성 및 required-column invariant가 실제 gate에서
강제되지 않는다. 따라서 현 memory-budget 통과 결과는 현재 fixture bytes에
대한 실행 증거로는 유효하지만, spec이 요구한 representative fixture 계약의
준수 증거로는 불완전하다.

## Findings

| Priority | Finding | Impact | Recommended action |
| --- | --- | --- | --- |
| P1 | fixture manifest의 대표성 field와 required-column null invariant가 검증되지 않는다. | 축소·왜곡된 manifest도 유효한 memory gate 통과로 기록될 수 있다. | typed nested manifest contract와 complete invariant validation을 추가한다. |
| P2 | memory runner의 artifact parsing 예외 시 temp directory cleanup 및 최종 failure report가 보장되지 않는다. | 실패한 실행이 temp artifact를 남기고 조사 가능한 report 없이 중단될 수 있다. | run 단위 `try/finally`, 실패 결과 수집, locale 고정을 적용한다. |
| P3 | 저장된 memory report가 사용 fixture의 digest를 포함하지 않는다. | report만으로 fixture bytes와 manifest를 암호학적으로 연결해 재현·감사하기 어렵다. | manifest 및 fixture SHA-256, resolved path, schema fingerprint를 report에 기록한다. |

### P1: Fixture Contract Is Not Enforced

[HMDAEDAFixtureManifest](../../src/project_pivot/hmda_data/eda_fixture.py)는
`schema_columns`, `row_width_bytes`, `null_rates`, `activity_year_cardinality`,
`activity_year_skew`, `expected`를 기록하지만, fixture validation은 version과
첫 fixture file의 size/SHA-256만 확인한다.

또한 [validate_hmda_eda_evidence](../../src/project_pivot/hmda_data/eda_fixture.py)는
`expected["null_counts"]`에 존재하는 column만 비교한다. 현재 manifest에는
`loan_amount`, `income`만 존재하므로 나머지 required column 5개의 null
invariant는 memory gate 대상이 아니다.

이는 canonical spec의 “fixture 필수 특성 누락 시 유효한 memory-budget test로
통과하면 안 됨” 및 “required-column null invariant 검증” 요구와 맞지 않는다.

권고 조치:

1. `files`, `expected`, null baseline, activity-year distribution을 nested
   Pydantic model로 정의한다.
1. required 7개 column의 schema, null count 또는 null rate를 complete key set으로
   강제한다.
1. row width, cardinality, skew key 및 skew 합계의 정합성을 validation 단계에서
   검사한다.
1. 불완전하거나 상호 모순된 manifest가 preflight에서 실패하는 component test를
   추가한다.

### P2: Runner Failure Cleanup And Reporting

[memory runner](../../scripts/run_hmda_eda_memory.py)는 run directory를 만들지만,
GNU `time` artifact 또는 worker JSON parsing 과정에서 예외가 발생하면 cleanup과
최종 assessment/report write 전에 종료될 수 있다.

권고 조치:

1. `_run_once()`의 run directory 정리를 `try/finally`로 보장한다.
1. artifact parse 및 IO 예외를 run-level failed result로 변환한다.
1. 이후 run과 최종 assessment를 계속 수행해 failure evidence를 report에 남긴다.
1. GNU `time` 실행 환경에 `LC_ALL=C`를 명시해 출력 parser의 locale 의존성을
   제거한다.

### P3: Evidence Traceability

[memory report](../hmda_eda_memory_report.json)는 `fixture_version`을 기록하지만
실행에 사용된 manifest digest, fixture file digest, resolved fixture path를
포함하지 않는다. 같은 version label을 가진 다른 fixture 조합과 현재 report를
독립적으로 연결하기 어렵다.

권고 조치:

- report에 manifest SHA-256, fixture SHA-256, resolved fixture path, row count,
  schema fingerprint를 기록한다.
- completion report에서 해당 digest를 함께 참조한다.

## Confirmed Strengths

- [Shared EDA entrypoint](../../src/project_pivot/hmda_data/eda.py)는 notebook과
  automated test가 같은 evidence 계약을 사용하도록 한다.
- 입력 부재, CSV parse failure, aggregate query failure에서 partial evidence를
  반환하지 않고 DuckDB connection을 닫는다.
- process-level hard limit, swap 0, timeout, 전용 temp directory 및 세 번의
  representative run이 구현되어 있다.
- 기존 completion report는 full-source 관측값과 fixture-level 결과의 해석 경계를
  명시한다.

## Validation Boundary

정적 diagnostics에서는 EDA entrypoint, fixture, memory runner, notebook에서
오류가 발견되지 않았다. 이 리뷰에서는 test를 새로 실행하지 않았으므로, 기존
artifact에 기록된 `3/3 passed` 결과는 재실행으로 독립 확인하지 않았다.

full source는 약 13,543,606 rows 및 4.8 GiB이며, uncontrolled 실행 peak RSS는
약 12.44 GiB였다. 현재 5M-row, 약 728 MiB fixture의 3 GiB 통과는 full-source
memory-budget 보장을 뜻하지 않는다.
