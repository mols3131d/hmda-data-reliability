---
type: review
category: review
title: HMDA EDA Reconcile Core Contract Lead Review
description: 6-core EDA 런타임 계약 정렬, Agent 친화적 탐색 API 및 정적 차트 내보내기, 단일 원천 포터블 에비던스 동기화에 대한 종합 검토
status: completed
tags:
  - domain:hmda-data
  - subdomain:eda
  - capability:hmda-eda-baseline
  - contract-reconciliation
---

> [!NOTE]
> Verdict: Pass (승인). 6-core 계약 축소, complete-key grain 집계, Marimo 대체(YAML/정적 HTML 차트), 단일 원천 기반 JSON/Markdown 에비던스 동기화 및 머신 독립성 정규화가 모든 Quality 및 Adversarial 관점에서 수용 가능한 수준으로 입증되었습니다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| `hmda-eda` / `reconcile-core-contract` | Commit `ad10e97a` (`feat/hmda-eda-baseline-reduce-core-scope`) | `src/project_pivot/hmda_data/eda/`, `scripts/run_actual_source.py`, `tests/hmda_data/eda/`, `docs/references/`, `openspec/` | Pass |

## Quality Assessment

1. **6-Core Contract 수축**:
   - `REQUIRED_EDA_COLUMNS`가 6개 컬럼(`activity_year`, `state_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`)으로 제한되었습니다.
   - `county_code` 및 불필요한 anomaly, freshness, `schema_hash` 조회가 제거되어 EDA 계산 경계가 명확해졌습니다.
1. **Complete-Key Grain 집계 정밀화**:
   - `_calculate_grain_alignment`에서 SQL `FILTER (WHERE activity_year IS NOT NULL AND state_code IS NOT NULL AND loan_purpose IS NOT NULL)`를 사용해 complete-key 행만 `distinct_group_count`로 계산하고, null key 행(170,769건)과 분리하여 `coverage_rate`를 계산합니다.
1. **전체 소요 시간(Duration) 측정 범위 수정**:
   - `duration_seconds` 측정을 Volume, Distribution, Numeric Summary, Grain 집계가 모두 완료된 최종 시점까지로 연장하여 실제 EDA 비용을 정확히 관측합니다.
1. **단일 원천 기반 에비던스 동기화**:
   - `scripts/run_actual_source.py`의 `write_evidence` 함수가 단일 `evidence` 개체로부터 `hmda_eda_reference.json`과 `hmda_eda.md`를 함께 작성하도록 보장하여 Markdown과 JSON 간의 수치 불일치를 근본적으로 예방합니다.
1. **Agent-Friendly 탐색 모듈 도입**:
   - 반응형 UI 노트북(`eda_mo.py`)을 완전 제거하고 에이전트/CLI 탐색을 위한 YAML 직렬화(`export_eda_evidence_yaml`) 및 정적 Altair 차트 파일 내보내기(`render_eda_static_charts`)를 구현했습니다.

## Adversarial Assessment

1. **로컬 머신 경로 유출 방지 (Path Portability)**:
   - `write_evidence` 생성 과정에서 절대 경로(`/home/mols...`, `.tmp`)가 제거되고 상대 경로 ID(`data/raw/hmda/year_2025.csv`)만 보존됩니다.
   - `test_eda_evidence.py`를 통해 머신 특정 경로가 에비던스 파일에 남지 않는지 명시적으로 단언(assert)합니다.
1. **Uncommitted 변경사항 추적성**:
   - `_repository_revision` 함수가 `git diff --quiet` 결과를 검사하여 커밋되지 않은 수정사항이 존재할 경우 `-dirty` 접미사를 추가합니다. 이를 통해 깨진/미커밋 상태의 코드가 깨끗한 커밋 증거로 위장하는 위험을 차단합니다.
1. **커넥션 및 리소스 정리 (Connection Leak Safeguard)**:
   - `analyze_hmda_csv` 함수 내부에서 `try ... finally: connection.close()` 구문으로 처리되어 쿼리 또는 파싱 실패 시에도 DuckDB 커넥션이 누출되지 않습니다.
1. **카디널리티 바운드 방어**:
   - `max_activity_years` 매개변수로 그룹화 결과 행 수를 제한하여 비정상 CSV 입력 시 발생할 수 있는 메모리 폭증 위험을 방지합니다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| EDA Focused Component Tests | `uv run pytest tests/hmda_data/eda/` (17/17 passed) | Pass |
| Python Linting & Formatting | `uv run ruff check` & `uv run ruff format` (No issues) | Pass |
| Markdown Formatting | `uv run rumdl check` (No issues) | Pass |
| Actual-source Evidence Generation | `uv run python scripts/run_actual_source.py` (Consistent JSON & MD) | Pass |

## Remaining Risks

- **Headless Browser 의존성에 따른 PNG 이미지 변환 제한**: `render_eda_static_charts`는 기본적으로 standalone HTML 차트를 생성합니다. PNG 이미지 직접 내보내기는 헤드리스 환경(`vl-convert` 등) 의존성이 필요하므로 정적 HTML 생성을 보장 수단으로 사용합니다. 이는 OpenSpec Design D4 및 Risks에 기록된 의도된 설계 선택(Trade-off)입니다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Pass | 6-core 사양 축소, 단일 원천 에비던스 동기화, 포터블 경로 정규화 및 테스트 검증이 모두 완성되었습니다. | `main` 브랜치 병합 준비 완료 |
