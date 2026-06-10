## 1. Shared Runner

- [x] 1.1 pipeline request/result 모델을 추가한다.
- [x] 1.2 raw load, dbt build, lifecycle runner 함수를 추가한다.
- [x] 1.3 full `run_mvp_pipeline` orchestration 함수를 추가한다.

## 2. Dagster

- [x] 2.1 Dagster resource/config를 추가한다.
- [x] 2.2 raw/dbt/lifecycle asset을 추가한다.
- [x] 2.3 MVP pipeline job/definitions를 추가한다.

## 3. FastAPI

- [x] 3.1 FastAPI app과 health endpoint를 추가한다.
- [x] 3.2 `POST /pipeline/run` endpoint를 추가한다.

## 4. Tests / Docs

- [x] 4.1 runner unit test를 추가한다.
- [x] 4.2 Dagster definitions test를 추가한다.
- [x] 4.3 FastAPI endpoint test를 추가한다.
- [x] 4.4 README/.env.example 실행 방법을 갱신한다.
- [x] 4.5 ruff, mypy, pytest를 실행한다.
