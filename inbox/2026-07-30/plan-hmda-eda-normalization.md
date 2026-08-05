---
title: 'plan-hmda-eda-normalization'
date: '2026-07-30'
type: 'normalization-plan'
status: 'proposed'
scope: 'notebooks/eda_mo.py, docs/references/hmda_eda.md, openspec/changes/add-hmda-eda-baseline'
priority: 'p1'
---

## Observation

| Area | Current observation | Meaning |
| --- | --- | --- |
| Input path | Notebook fallback is `data/raw/hmda/year_2025.csv`; the file is present. | 이전의 `data/year_2025_sample.csv` file-not-found 오류 경로는 현재 코드에 없다. |
| Parse behavior | Shared DuckDB relation uses `ignore_errors=true`. | 파싱 실패 행이 volume과 null baseline에서 조용히 제외될 수 있다. |
| Runtime evidence | OpenSpec의 실행 검증 task는 완료지만, 현재 fallback으로 새 커널에서 full CSV를 성공 실행한 evidence는 없다. | 정상 완료를 아직 재확인할 수 없다. |
| Documentation | Reference는 이전 sample fallback과 모든 컬럼 null profile을 설명한다. | 현재 구현의 default path와 required-column null baseline에 맞지 않는다. |

## Goal

원천 CSV EDA가 하나의 명시된 입력을 fail-fast로 읽고, 새 실행에서 schema, volume, required-column null, freshness boundary를 모두 렌더링한 사실을 확인한다.

EDA는 source-file observation으로 제한한다. Bronze 적재, dbt, `ProfileSnapshot` 저장, incident 판정과 recovery는 이 계획의 범위가 아니다.

## Plan

### 1. Input and Reader Contract

1. `notebooks/eda_mo.py`의 default path를 `data/raw/hmda/year_2025.csv`로 유지하고, 화면에 실제 resolved input path를 표시한다.
1. 입력 파일 부재는 reader 실행 전에 명확히 실패하게 한다.
1. `csv_options`와 SQL reader에서 `ignore_errors`를 함께 제거한다. 파싱 오류가 있으면 `eda_evidence`, row count, null rate를 생성하지 않는다.
1. `header`, `nullstr=['NA', '']`, `sample_size=200000`는 유지한다.

### 2. Fresh Runtime Evidence

1. 정상 CSV용 소형 fixture로 새 Marimo kernel 실행을 먼저 확인한다. required schema, row count, null baseline, `observed_at` 부재 상태를 확인한다.
1. 필드 수가 불일치하는 행을 포함한 임시 CSV를 별도 실행한다. DuckDB parse error가 발생하고 baseline 화면 또는 `eda_evidence`가 생성되지 않는지 확인한다.
1. `data/raw/hmda/year_2025.csv`는 full-file scope임을 명시한 뒤 새 kernel에서 실행한다. schema, 전체 row count, `activity_year` counts, required-column null baseline, freshness boundary의 렌더링을 기록한다.
1. full-file 실행 중 parse error가 발생하면 정상화 완료로 처리하지 않는다. 오류 위치와 입력 상태만 기록하고, 원천 정정 또는 quarantine 경로는 별도 변경으로 결정한다.

### 3. Contract and Documentation Alignment

1. `docs/references/hmda_eda.md`의 fallback 경로를 현재 default path로 수정한다.
1. null baseline 설명을 전체 컬럼이 아닌 present required columns로 한정하고, `schema.required_columns` evidence를 반영한다.
1. OpenSpec `design.md`의 `ignore_errors` 유지 결정을 fail-fast 계약으로 바꾼다.
1. OpenSpec `tasks.md`의 기존 실행 검증 완료 표시는 새 실행 증거가 생길 때까지 미완료 상태로 되돌리고, malformed CSV failure 검증을 추가한다.

## Verification Gates

| Gate | Check | Expected observation |
| --- | --- | --- |
| Static | `uv run --group dev marimo check notebooks/eda_mo.py` | Marimo dependency graph가 통과한다. |
| Reader contract | malformed-row fixture 실행 | parse error가 노출되고 metric evidence가 생성되지 않는다. |
| Baseline render | valid small fixture 실행 | schema, volume, required null, freshness boundary가 새 kernel에서 렌더링된다. |
| Full scope | default `year_2025.csv` 실행 | full-file 입력으로 같은 섹션이 렌더링되고 reader 오류가 없다. |
| Consistency | `uv run ruff check notebooks/eda_mo.py` 및 `uv run rumdl fmt docs/references/hmda_eda.md openspec/changes/add-hmda-eda-baseline` | 코드·문서 형식이 통과한다. |

## Completion Criteria

- default input path로 file-not-found 오류 없이 새 Marimo kernel 실행이 시작된다.
- malformed CSV는 성공 baseline을 만들지 않는다.
- 정상 fixture와 full source CSV에서 현재 실행 결과를 확인할 수 있다.
- 노트북, reference, OpenSpec task 상태가 동일한 reader contract와 검증 상태를 설명한다.

## Risks

| Risk | Handling |
| --- | --- |
| Full CSV는 약 5 GB라 실행 시간이 길다. | fixture 검증을 먼저 통과시키고 full scan은 명시된 최종 gate로 한 번만 수행한다. |
| Fail-fast 전환 뒤 실제 source parse error가 발견될 수 있다. | 데이터 품질 이슈로 기록한다. EDA가 soft-fail로 baseline을 계속 만들게 하지 않는다. |
| 이전 notebook output이 화면에 남을 수 있다. | 검증마다 새 kernel과 입력 경로를 기록해 stale output을 evidence에서 제외한다. |
