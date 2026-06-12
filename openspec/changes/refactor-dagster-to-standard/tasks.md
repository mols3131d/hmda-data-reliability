## 1. 환경 설정 및 의존성 확인

- [x] 1.1 `pyproject.toml`에 `dagster-webserver` 의존성 존재 확인
- [x] 1.2 `uv` 환경에서 Dagster CLI와 웹 서버 import 가능 여부 확인
- [x] 1.3 `tool.dg` CLI 설정이 현재 repo 구조와 맞는지 확인

## 2. 오케스트레이션 및 asset 표준화

- [x] 2.1 `raw_taxi_data`, `dbt_analytics`, `mvp_incident_lifecycle`에 메달리온 group 적용
- [x] 2.2 asset 반환을 Dagster metadata 중심으로 정리
- [x] 2.3 asset dependency를 실제 데이터 전달과 실행 순서 의존성으로 구분
- [x] 2.4 `MvpPipelineDagsterResource` 유지/축소/Config 전환 중 가장 단순한 구조 선택
- [x] 2.5 domain logic은 `pipeline`과 `reliability` 모듈에 유지

## 3. 관측성 개선

- [x] 3.1 raw 적재 결과 metadata 기록
- [x] 3.2 dbt build 결과와 artifact path metadata 기록
- [x] 3.3 incident lifecycle 결과와 evaluation report path metadata 기록
- [x] 3.4 Dagster log에 사용자에게 필요한 실행 맥락만 남기기

## 4. 검증 및 테스트

- [x] 4.1 `pytest tests/orchestration` 실행
- [x] 4.2 필요 시 orchestration 테스트를 metadata/asset group 기준으로 갱신
- [x] 4.3 `dagster dev -m project_pivot.orchestration.dagster.definitions` 로컬 UI smoke test
- [x] 4.4 Dagster UI 또는 CLI에서 `mvp_pipeline_job` materialization 확인
