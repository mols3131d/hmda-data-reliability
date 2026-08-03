# Bronze

HMDA 원천 파일을 DuckDB raw table에 보관하는 단계다.

## 기준

- 입력: `data/raw/hmda`의 CSV 또는 Parquet
- 보존: 원천 row와 `source_file`, `source_year`, `ingested_at`
- 재실행: 같은 partition을 다시 적재해도 중복 row가 없어야 함
- 검증: `activity_year` 등 핵심 column이 있어야 함

구현 위치: `src/project_pivot/hmda_data/ingestion/`  
검증 위치: `tests/hmda_data/`, `tests/data_operations/`
