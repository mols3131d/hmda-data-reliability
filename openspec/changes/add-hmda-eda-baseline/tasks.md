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

## 5. Shared EDA computation

- [ ] 5.1 작은 deterministic HMDA CSV fixture로 현재 schema, row count, null rate, activity-year count와 freshness evidence를 고정하는 characterization test를 추가한다.
- [ ] 5.2 `src/project_pivot/hmda_data/eda.py`에 입력 path, DuckDB memory/thread/temp 설정과 activity-year cardinality bound를 받는 public entrypoint를 구현한다.
- [ ] 5.3 원천을 dataframe으로 materialize하지 않는 DuckDB aggregate query와 JSON-serializable evidence 생성을 entrypoint로 이동한다.
- [ ] 5.4 정상·parse/query 실패 모두에서 DuckDB connection이 닫히고 원천 파일이 변경되지 않음을 test로 검증한다.
- [ ] 5.5 activity-year grouping 결과가 bound를 초과하면 무제한 `fetchall()` 대신 validation failure가 발생함을 test로 검증한다.

## 6. Marimo entrypoint integration

- [ ] 6.1 `notebooks/eda_mo.py`의 계산 셀을 공유 entrypoint 호출로 교체하고 기존 schema, volume, null, freshness와 mapping UI를 유지한다.
- [ ] 6.2 valid fixture와 malformed fixture에 대해 노트북 smoke 동작 및 fail-fast 경계를 새 kernel에서 확인한다.
- [ ] 6.3 `uv run marimo check notebooks/eda_mo.py`와 notebook 대상 lint를 통과시킨다.

## 7. Representative workload

- [ ] 7.1 대표 fixture의 version, seed, schema, row 수, row 폭, null 비율, activity-year cardinality/skew와 파일 수를 담는 manifest schema를 정의한다.
- [ ] 7.2 대표 fixture를 측정 process 밖에서 deterministic하게 준비하는 command 또는 versioned artifact 연결을 구현한다.
- [ ] 7.3 fixture와 manifest가 없거나 불일치하면 memory-budget 실행이 통과하지 않는 사전 검증을 추가한다.

## 8. Memory-budget validation

- [ ] 8.1 `memory` pytest marker를 등록하고 기본 병렬 test에서 memory workload를 제외한다.
- [ ] 8.2 대표 fixture의 schema, row count, null, activity-year count와 freshness invariant를 검증하는 memory test를 추가한다.
- [ ] 8.3 process 3 GiB, swap 0, DuckDB 1600 MB, 2 threads, timeout 15분과 실행별 temp directory를 강제하는 `systemd-run` 또는 동등한 container wrapper를 구현한다.
- [ ] 8.4 hard limit 적용 사전 확인이 실패하면 memory-budget 통과로 기록되지 않도록 wrapper를 검증한다.
- [ ] 8.5 동일 fixture를 세 번 실행하고 최대 peak RSS, elapsed time, temp disk, exit/resource-control 상태, 결과 검증과 environment version을 보고한다.
- [ ] 8.6 최대 peak RSS 85% 초과, OOM, timeout, temp disk 초과 또는 invariant 실패가 올바른 판정으로 이어지는지 검증한다.

## 9. Memory documentation and completion

- [ ] 9.1 `docs/references/hmda_eda.md`의 공유 entrypoint와 memory-budget command 설명을 구현과 일치시킨다.
- [ ] 9.2 `docs/DEVELOPMENT.md`에 correctness, memory, stress test 선택 및 지원 runner 조건을 기록한다.
- [ ] 9.3 HMDA correctness test, 기본 test exclusion, Marimo check와 지원 환경의 3회 memory baseline을 실행해 결과를 기록한다.
- [ ] 9.4 OpenSpec change와 Markdown 문서를 검증하고 실제 검증 범위를 데이터·예산·환경과 함께 보고한다.
