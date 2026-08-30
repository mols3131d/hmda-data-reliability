---
type: report
title: Code Comprehension Refactoring RPI Report
description: mols-code-comprehension-refactor 후보 1~4와 선행 pilot의 Research, Plan, Implementation, Review 결과와 검증 근거를 정리한다.
status: completed
categories:
  - software-engineering
tags:
  - code-comprehension
  - refactor
  - rpi
  - validation
---

# Code Comprehension Refactoring RPI Report

> [!NOTE]
> `mols-code-comprehension-refactor` 기준으로 선행 pilot과 조사 우선순위 1~4의 동작 보존 리팩터링을 적용했다. 전체 테스트는 `461 passed, 1 skipped`, Ruff lint/format과 diff 무결성 검사는 통과했고, 독립 `review-lead` 평가는 `clear`였다. 다만 `review_ai/service.py`에는 새 `_ReviewSession._build_record()`로 대체된 기존 module-level `_build_record()`가 남아 있어 커밋 전 제거가 권장된다.

## Scope

### In Scope

| 구분 | 대상 |
| --- | --- |
| 선행 pilot | [`data_operations/runner.py`](../../src/hmda_reliability/data_operations/runner.py) artifact promotion 상태 추적 |
| Candidate 1 | [`review_ai/service.py`](../../src/hmda_reliability/review_ai/service.py) invocation evidence 조립 흐름 |
| Candidate 2 | [`hmda_data/eda/analysis.py`](../../src/hmda_reliability/hmda_data/eda/analysis.py) volume/null metric row 해석 |
| Candidate 3 | [`hmda_data/synthetic/cases.py`](../../src/hmda_reliability/hmda_data/synthetic/cases.py) null-spike threshold SQL 표현 |
| Candidate 4 | [`reliability/recovery/executor.py`](../../src/hmda_reliability/reliability/recovery/executor.py) content/freshness reconciliation 분기 |

### Out of Scope

- 공개 API, 반환 모델, 예외 계약 또는 persistence schema 변경
- 결함 수정, 성능 최적화 또는 architecture redesign
- LangGraph를 사용하는 remediation workflow 교체
- 테스트 assertion 완화 또는 새로운 dependency 도입

## RPI Summary

| Target | Research Finding | Implementation | Preservation Evidence | Status |
| --- | --- | --- | --- | --- |
| `data_operations/runner.py` | staged, backup, committed 경로가 세 개의 병렬 collection에 분산돼 rollback 상태를 재구성해야 했다 | `_ArtifactPromotion` frozen dataclass로 source, destination, staged, backup 경로를 결합했다 | dbt runner 26 tests, focused rollback tests, Ruff | 완료 |
| `review_ai/service.py` | provider/parse/validation 분기마다 동일한 invocation context를 긴 argument 목록으로 반복 조립했다 | `_ReviewSession`에 불변 context와 record/persist 흐름을 캡슐화했다 | review_ai 87 tests, service 10 tests, Ruff | 완료, cleanup 1건 |
| `hmda_data/eda/analysis.py` | `GROUPING SETS` 결과의 null count를 tuple slice와 offset 산술로 해석했다 | profile column별 명시적 indexed mapping과 정수 변환으로 결과 해석을 직접 표현했다 | EDA 28 tests, Ruff | 완료 |
| `hmda_data/synthetic/cases.py` | strict null-rate 증가 수식이 큰 SQL `CASE` 안에 중첩돼 의도와 parameter 순서를 해독해야 했다 | `null_threshold_expr`로 threshold 수식을 분리하고 CTE/parameter 순서는 유지했다 | synthetic 11 tests, Ruff | 완료 |
| `reliability/recovery/executor.py` | `execute()`가 content와 freshness reconciliation 세부 분기를 직접 소유했다 | `_reconcile_state()`로 binding 종류별 reconciliation을 캡슐화했다 | approval backfill 22 tests, Ruff | 완료 |

## Detailed Results

### Artifact Promotion State

[`data_operations/runner.py`](../../src/hmda_reliability/data_operations/runner.py)는 candidate artifact 하나에 속한 경로를 `_ArtifactPromotion`으로 묶었다.

- `source`: 검증된 run artifact
- `destination`: current projection 경로
- `staged_path`: current 변경 전에 준비하는 `.next` 경로
- `backup_path`: partial commit 실패 시 복구하는 `.previous` 경로

`staged_promotions`, `backed_up_promotions`, `committed_promotions`는 경로 종류가 아니라 **완료된 상태 단계**를 나타낸다. 두 번째 artifact 교체 실패 시 committed destination 제거 후 backup을 역순 복원하는 기존 순서와, commit 완료 뒤 backup cleanup 실패를 무시하는 기존 결과를 유지했다.

### Review Invocation Evidence Assembly

[`review_ai/service.py`](../../src/hmda_reliability/review_ai/service.py)는 단일 review 실행에서 변하지 않는 값을 `_ReviewSession`으로 묶었다.

- invocation identity와 recording time
- runtime/review settings
- validated review input과 rendered prompt
- invocation evidence writer

Provider unavailable, response size 초과, schema parse 실패, deterministic validation 결과는 이제 `record_and_persist()`에 분기별 값만 전달한다. Status, failure code, latency, attempt count, usage와 trace identity의 기존 매핑은 관련 테스트에서 유지됐다.

> [!WARNING]
> 기존 module-level `_build_record()`가 현재 파일에 남아 있지만 새 실행 경로에서는 호출되지 않는다. 동작 회귀는 아니지만 중복된 representation을 남기므로 커밋 전 삭제하고 동일한 review_ai 검증을 다시 실행하는 것이 좋다.

### EDA Metric Row Interpretation

[`hmda_data/eda/analysis.py`](../../src/hmda_reliability/hmda_data/eda/analysis.py)는 단일 DuckDB query와 `GROUPING SETS`를 유지했다. 변경은 결과 해석에만 한정했다.

- total row 위치를 결정하는 `metric_offset` 의미는 유지했다.
- null count tuple slice를 `enumerate(profile_columns)` 기반 명시적 column mapping으로 바꿨다.
- DuckDB 반환 값을 `int`로 정규화해 반환 타입 의도를 직접 나타냈다.
- `activity_year_rows` 반환 shape와 downstream offset 사용은 변경하지 않았다.

### Null-Spike Threshold Expression

[`hmda_data/synthetic/cases.py`](../../src/hmda_reliability/hmda_data/synthetic/cases.py)는 strict null-rate 증가를 결정하는 SQL 식을 `null_threshold_expr`로 분리했다.

수식은 다음 두 조건의 큰 값을 사용하되, 연도별 non-null count를 넘지 않는다.

1. 요청된 `null_fraction`에 따른 최소 null 개수
1. output null ratio가 전체 source null ratio를 엄격히 초과하는 최소 정수 개수

SQL placeholder 순서와 `params` 순서는 그대로 유지했다. Parquet schema, sample cardinality, strict increase invariant와 failure condition은 관련 synthetic tests로 확인했다.

### Recovery Reconciliation Branch

[`reliability/recovery/executor.py`](../../src/hmda_reliability/reliability/recovery/executor.py)는 content identity와 freshness binding 분기를 `_reconcile_state()`로 이동했다.

`execute()`는 다음 흐름을 더 직접적으로 드러낸다.

1. approval/proposal 검증
1. approved candidate staging
1. current identity 확인
1. binding 종류에 따른 reconciliation
1. 필요한 경우 compare-and-replace mutation
1. profile snapshot 재검증

Freshness timestamp 조회는 freshness binding이 있을 때만 수행하며, `_replace_approved_partition()`에 전달되는 binding과 exception timing은 유지했다.

## Validation Evidence

| Validation | Result |
| --- | --- |
| `uv run pytest tests/data_operations/test_dbt_runner.py -q` | 26 passed |
| `uv run pytest tests/review_ai -q` | 87 passed |
| `uv run pytest tests/hmda_data/eda -q` | 28 passed |
| `uv run pytest tests/hmda_data/test_synthetic.py -q` | 11 passed |
| `uv run pytest tests/reliability/test_approval_backfill_validation.py -q` | 22 passed |
| `uv run pytest -q` | 461 passed, 1 skipped |
| `uv run ruff check src tests` | passed |
| `uv run ruff format --check src tests` | 172 files already formatted |
| `git diff --check` | passed |
| Independent `review-lead` | `clear` |

독립 검토는 공개 signature, 반환 model, typed failure mapping, file rollback, DuckDB query shape, synthetic SQL parameter ordering과 recovery transaction 경계를 확인했다.

## Review Observations

### Non-Blocking Cleanup

1. [`review_ai/service.py`](../../src/hmda_reliability/review_ai/service.py)의 기존 module-level `_build_record()`를 제거한다.
1. [`reliability/recovery/executor.py`](../../src/hmda_reliability/reliability/recovery/executor.py)의 `_reconcile_state()` 반환 type과 downstream `executed_actions` representation의 type annotation 일관성을 재확인한다.

### Future Hardening

다음 항목은 이번 comprehension refactor가 만든 regression은 아니며, 별도 correctness/hardening 작업으로 분리해야 한다.

- artifact stage copy가 partial `.next` 파일을 남기며 실패하는 경우
- rollback cleanup 또는 backup restore 자체가 실패하는 경우
- recovery failure evidence의 추가 characterization이 필요한 경우

## Current State

- Source 변경 5개와 candidate research artifact 1개가 아직 미커밋 상태다.
- 현재 diff 규모는 source 기준 `195 insertions`, `127 deletions`다.
- 이 보고서는 non-canonical working artifact이며 source/test contract를 대체하지 않는다.

## Next Actions

1. 남은 module-level `_build_record()`를 제거한다.
1. focused `tests/review_ai/test_service.py`와 전체 `tests/review_ai`를 재실행한다.
1. 전체 Ruff 및 `uv run pytest -q`를 다시 실행한다.
1. 새 independent review를 받아 최종 변경 상태를 확인한다.
1. source refactor와 조사/보고서 artifact를 논리적 commit 단위로 정리한다.
