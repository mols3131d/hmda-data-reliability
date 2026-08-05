---
title: 'improvement-hmda-eda-parse-integrity'
date: '2026-07-30'
type: 'improvement-plan'
status: 'proposed'
source_review: 'hmda-eda-baseline-review'
priority: 'p1'
---

## Summary

`notebooks/eda_mo.py`의 baseline CSV reader를 fail-fast로 전환한다. 파싱 오류가 있는 입력은 volume, null rate, schema hash를 계산하거나 baseline evidence로 표시하지 않는다.

대상 결함: [hmda-eda-ignored-parse-errors](hmda-eda-baseline-review/hmda-eda-ignored-parse-errors.md).

## Goal

- EDA baseline의 `row_count`와 `null_rates`가 원천에서 조용히 제외된 행을 포함하지 않도록 보장한다.
- 입력 파싱 오류를 분석 결과가 아닌 실행 오류로 드러낸다.

## Scope

| 포함 | 제외 |
| --- | --- |
| `notebooks/eda_mo.py`의 `read_csv_auto` 옵션 | production ingestion reader 변경 |
| 입력 범위 안내 문구 | `ProfileSnapshot`, incident lifecycle, detection 변경 |
| 정상·손상 CSV 실행 검증 | 물리 줄 수 기반 손실 집계 |

## Decision

`ignore_errors=true`를 제거한다. DuckDB reader가 파싱 오류를 반환하면 노트북 실행을 중단한다.

물리 행 수와 reader row count를 비교해 경고하는 방식은 채택하지 않는다. CSV는 인용된 줄바꿈 등으로 물리 줄 수와 레코드 수가 다를 수 있어, 별도 CSV 해석기를 추가하지 않고는 정확한 손실 수를 보장할 수 없다.

## Work Items

1. [notebooks/eda_mo.py](../../../../project-pivot/notebooks/eda_mo.py)의 `csv_options`에서 `ignore_errors`를 제거한다.
1. 동일 reader SQL에서 `ignore_errors=true`를 제거한다. 옵션 값과 실제 reader 옵션이 다시 분리되지 않게 함께 확인한다.
1. 입력 범위 화면에서 soft-fail 설명을 삭제하고, CSV 파싱 오류가 발생하면 baseline을 생성하지 않는다는 문구로 교체한다.
1. OpenSpec `design.md`의 shared relation 결정에서 `ignore_errors` 보존 문구를 제거하고 fail-fast 계약을 기록한다.
1. OpenSpec `tasks.md`에 malformed CSV가 EDA 실행을 실패시키는 검증 항목을 추가한다.

## Verification

| Check | Expected result |
| --- | --- |
| `uv run --group dev marimo check notebooks/eda_mo.py` | Marimo dependency graph 검사 통과 |
| `HMDA_EDA_DATA_PATH=data/year_2025_sample.csv` HTML export | schema, volume, null, freshness 섹션 렌더링 성공 |
| 필드 수가 다른 행을 포함한 임시 CSV export | DuckDB CSV parse error로 실패, `eda_evidence` 미생성 |
| `uv run ruff check notebooks/eda_mo.py` | lint 통과 |
| `uv run rumdl fmt openspec/changes/add-hmda-eda-baseline` | 변경된 OpenSpec Markdown 포맷 통과 |

## Acceptance Criteria

- malformed CSV는 정상 `row_count`나 `null_rates`를 표시하지 않는다.
- 정상 sample CSV는 기존 baseline 표와 `eda_evidence`를 계속 생성한다.
- 노트북 안내 문구와 실제 DuckDB reader 옵션이 모두 fail-fast 계약을 표현한다.
- 변경은 EDA notebook과 해당 OpenSpec 문서에만 한정한다.

## Risks

- 이전에 허용되던 원천의 파싱 이상은 노트북 실행을 막는다. 이는 baseline evidence의 신뢰성을 우선하는 의도된 동작이다.
- 전체 원천 CSV의 실제 오류 여부는 구현 후 명시적으로 실행해 확인한다. 오류가 발견되면 데이터 정정 또는 별도 quarantine 경로를 새 변경으로 결정한다.
