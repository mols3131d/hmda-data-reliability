# HMDA EDA Baseline Overview

## Summary

이 변경은 HMDA 원천 CSV EDA가 reliability baseline의 근거로 사용할 수 있는 schema, volume, null, freshness evidence를 표시하도록 확장한다. CSV 파싱 오류 또는 입력 파일 부재에서는 불완전한 baseline을 만들지 않고 실행을 실패시킨다.

## Why Now

기존 EDA reader의 `ignore_errors=true`는 손상 행을 조용히 제외할 수 있다. 이 경우 `row_count`와 `null_rates`는 원천 전체가 아닌 파싱 성공 행을 기준으로 계산되어, 데이터 품질 변화와 파싱 손실을 구분할 수 없다.

## Scope

| Included | Excluded |
| --- | --- |
| Required schema와 inferred type 표시 | `ProfileSnapshot` 저장 |
| 전체 및 `activity_year`별 volume | Incident detection과 remediation |
| Required-column null baseline | Raw data 수정 또는 quarantine 처리 |
| `observed_at` 기반 freshness boundary | dbt model과 pipeline 변경 |
| Fail-fast CSV reader와 runtime validation | SLA 정의 |

## Contract

- 입력은 `HMDA_EDA_DATA_PATH` 또는 기본 경로 `data/raw/hmda/year_2025.csv`다.
- 입력 파일은 DuckDB reader 전에 존재를 확인한다.
- CSV reader는 `header=true`, `nullstr=['NA', '']`, `sample_size=200000`를 사용한다.
- `ignore_errors`를 사용하지 않는다.
- CSV parse error 또는 input path 오류가 발생하면 `row_count`, `null_rates`, `eda_evidence`를 생성하지 않는다.
- `observed_at`이 없거나 유효 timestamp가 없으면 source freshness는 `unmeasured`다.

## Execution Plan

1. Reader에서 input file 존재를 확인하고 fail-fast parsing으로 전환한다.
1. 동일 relation으로 schema, volume, null, freshness evidence를 계산한다.
1. 새 Marimo kernel에서 valid sample을 실행해 화면 출력을 확인한다.
1. malformed fixture에서 parse error와 baseline evidence 미생성을 확인한다.
1. 4.8 GB full source를 한 번 실행하고 duration 및 결과 또는 reader error를 기록한다.
1. EDA reference와 task checkbox를 검증 결과에 맞게 갱신한다.

## Completion Criteria

- 손상 CSV는 성공한 baseline을 표시하지 않는다.
- 정상 sample은 required schema, volume, null, evidence mapping, unmeasured freshness를 렌더링한다.
- full source 실행 결과 또는 parse error가 새 kernel 기준으로 기록된다.
- `ruff`, Markdown formatter, OpenSpec strict validation이 통과한다.

## Reading Order

1. [Proposal](proposal.md): 변경 목적과 영향
1. [Specification](specs/hmda-eda-baseline/spec.md): 검증 가능한 계약
1. [Design](design.md): reader와 validation 결정
1. [Tasks](tasks.md): 구현 및 검증 순서
