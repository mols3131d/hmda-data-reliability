## 1. Reader integrity

- [x] 1.1 `notebooks/eda_mo.py`에서 입력 파일 존재를 DuckDB reader 전에 확인하고, 실제 resolved input path를 표시한다.
- [x] 1.2 `csv_options`와 shared `read_csv_auto` relation에서 `ignore_errors`를 제거하고 `header=true`, `nullstr=['NA', '']`, `sample_size=200000` 계약을 유지한다.
- [ ] 1.3 CSV parse error 또는 입력 파일 부재 시 `row_count`, `null_rates`, `eda_evidence`가 생성되지 않는지 확인한다.

## 2. Baseline output

- [x] 2.1 required column 존재·추론 타입 비교표와 누락·타입 불일치 callout을 fail-fast reader 결과로 생성한다.
- [x] 2.2 전체 및 `activity_year`별 row count와 required column별 null count·null rate를 같은 aggregate query에서 계산한다.
- [x] 2.3 JSON-serializable `eda_evidence`, `ProfileSnapshot` field mapping, `observed_at` freshness 또는 미측정 경계를 현재 reader 계약과 일치하게 표시한다.

## 3. Runtime validation

- [x] 3.1 새 Marimo kernel에서 valid sample을 실행하고 schema, volume, null, evidence mapping, unmeasured freshness 출력이 렌더링되는지 확인한다.
- [ ] 3.2 필드 수가 불일치하는 temporary CSV를 새 kernel에서 실행하고 DuckDB parse error와 baseline evidence 미생성을 확인한다.
- [ ] 3.3 새 Marimo kernel에서 `data/raw/hmda/year_2025.csv`를 한 번 실행하고 duration, schema, 전체·연도별 volume, null baseline, freshness boundary 또는 reader error를 기록한다.

## 4. Documentation and completion

- [x] 4.1 `docs/references/hmda_eda.md`의 fallback path, parse-error handling, evidence 설명을 실제 reader 계약과 일치시킨다.
- [x] 4.2 runtime 검증 결과에 따라 이 task의 checkbox 상태와 OpenSpec artifact의 설명을 갱신한다.
- [x] 4.3 `uv run ruff check notebooks/eda_mo.py`, `uv run rumdl fmt docs/references/hmda_eda.md openspec/changes/add-hmda-eda-baseline`, `openspec validate add-hmda-eda-baseline --strict`를 실행한다.
