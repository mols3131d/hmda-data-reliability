# HMDA EDA Reference

> **Source:** `data/raw/hmda/year_2025.csv`
> **Date Observed:** 2026-08-06
> **Duration:** 0.66 seconds (DuckDB 2 threads, 2GB memory)

이 문서는 HMDA 2025 data에 대한 1회성 read-only observation 결과를 기록한다.

## 1. Volume and Activity Year

- **Total Rows:** 13,543,606
- **Activity Years:**
  - 2025: 13,543,606 rows

## 2. Null Rates

| Column | Null Count | Null Rate |
| --- | --- | --- |
| `activity_year` | 0 | 0.00% |
| `state_code` | 170,769 | 1.26% |
| `county_code` | 301,923 | 2.23% |
| `loan_purpose` | 0 | 0.00% |
| `action_taken` | 0 | 0.00% |
| `loan_amount` | 0 | 0.00% |
| `income` | 647,212 | 4.78% |

## 3. Schema Constraints

- **Type Check:** `activity_year`, `loan_purpose`, `action_taken` (Integer families), `loan_amount`, `income` (Numeric families), `state_code`, `county_code` (VARCHAR).
- **Missing Required Columns:** None.

## 4. Grain Alignment (MVP)

- **Grain Columns:** `activity_year`, `state_code`, `loan_purpose`
- **Distinct Groups:** 335
- **Rows with Null Keys:** 170,769
- **Coverage Rate:** 98.74%

## Boundaries and Limitations

1. **Read-only**: 이 데이터는 관찰만 하며 수정이나 clipping, 자동 정제를 수행하지 않는다.
1. **Freshness & Profile Mapping**: 이 기능들은 EDA 파이프라인에서 제거되어 기록하지 않는다.
1. **Validation Command**:
   - `uv run pytest tests/hmda_data/eda/`
   - `uv run marimo export html notebooks/eda_mo.py`
