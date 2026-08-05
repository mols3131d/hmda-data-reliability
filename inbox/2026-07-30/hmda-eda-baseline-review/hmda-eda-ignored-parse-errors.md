---
title: 'hmda-eda-ignored-parse-errors'
description: 'ignore_errors가 파싱 실패 행을 baseline에서 조용히 제외한다.'
type: 'code-review-detail'
priority: 'p1'
---

- Location: [notebooks/eda_mo.py:81-83](../../../../../project-pivot/notebooks/eda_mo.py#L81-L83), [notebooks/eda_mo.py:94-97](../../../../../project-pivot/notebooks/eda_mo.py#L94-L97), [notebooks/eda_mo.py:153-181](../../../../../project-pivot/notebooks/eda_mo.py#L153-L181)

## Summary

`ignore_errors=true`가 손상 행을 제외한 결과로 row count와 null rate baseline을 계산하지만, 제외 건수 또는 baseline이 파싱 성공 행 기준이라는 사실을 출력하지 않는다.

## Observation

**[hmda-eda] 조용한 행 제외**: 입력 범위는 `ignore_errors=true`로 분석을 계속한다고만 표시한다. 이후 volume과 null metric은 해당 reader의 `count(*)`로 계산된다.

- 손상 행은 relation에 포함되지 않으므로 `row_count`, `activity_year_counts`, `null_rates`의 분모에서 모두 사라진다.
- 재현: 3개 데이터 행 중 1개가 필드 수 불일치인 CSV를 같은 DuckDB reader로 읽으면 `count(*)`는 2가 된다.

## Impact

**[hmda-eda] 신뢰할 수 없는 baseline**: 원천 파일의 행 수 감소나 null rate 변화를 데이터 변화로 해석할 수 있지만, 실제 원인은 새 파싱 오류일 수 있다.

- EDA evidence가 이후 reliability 기준선 근거로 사용되면 손실된 행을 탐지할 수 없다.
- CSV가 손상된 경우에도 schema 및 volume 화면이 정상처럼 보인다.

## Recommendation

**[hmda-eda] 파싱 손실을 가시화**: baseline reader에서 `ignore_errors`를 제거해 파싱 실패를 즉시 표시하거나, 유지해야 하면 물리 입력 행 수와 reader row count의 차이 및 경고를 함께 출력한다.

- 현재 출력의 `row_count`가 파싱 성공 행 수임을 명시한다.
- 새 regression test는 malformed row가 있을 때 오류 또는 손실 경고가 발생하는지 검증한다.

## Verification

**[hmda-eda] 재현 완료**: DuckDB `read_csv_auto(..., ignore_errors=true)`에 정상 행 2개와 필드 수 불일치 행 1개를 입력했다.

- physical data rows: 3
- reader `count(*)`: 2, dropped rows: 1
