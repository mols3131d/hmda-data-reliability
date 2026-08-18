---
type: checklist
title: Apache Airflow 마이그레이션 체크리스트
description: Dagster에서 Apache Airflow로의 cutover를 단계별로 검증하기 위한 실행 및 acceptance checklist다.
tags:
  - orchestration
  - airflow
  - migration
  - checklist
---

# Apache Airflow 마이그레이션 체크리스트

관련 문서:

- [`20-58-decision-orchestration-apache-airflow-migration.md`](20-58-decision-orchestration-apache-airflow-migration.md)
- [`20-59-plan-orchestration-apache-airflow-migration.md`](20-59-plan-orchestration-apache-airflow-migration.md)

## 0. Baseline

- [ ] current migration branch가 최신 `main` 기준인지 확인
- [ ] `src/project_pivot/orchestration/**` active surface 확인
- [ ] `tests/orchestration/**` current behavior 확인
- [ ] `orchestration-pipeline` canonical Spec 확인
- [ ] `reliability-data-contracts` canonical Spec 확인
- [ ] Dagster-specific active reference inventory 작성
- [ ] historical/archive reference는 cleanup scope에서 제외

## 1. Dependency gate

- [ ] Airflow 3.3.x + Python 3.13 resolution 성공
- [ ] official Airflow constraints 적용 가능 여부 확인
- [ ] `uv.lock` 생성/갱신 성공
- [ ] `uv sync --locked` 성공
- [ ] `import airflow` 성공
- [ ] `airflow version` 성공
- [ ] `import project_pivot` 성공
- [ ] `dbt --version` 성공
- [ ] DuckDB import 성공
- [ ] pytest collection 성공
- [ ] 기존 핵심 dependency의 위험한 downgrade 없음

### Dependency stop gate

- [ ] unresolved dependency incompatibility가 있으면 implementation 시작 금지

## 2. OpenSpec

- [ ] Change `orchestration-pipeline-migrate-airflow` 생성
- [ ] Proposal 작성
- [ ] affected capability에 `orchestration-pipeline` 포함
- [ ] affected capability에 `reliability-data-contracts` 포함
- [ ] scheduling/retry/cloud/LLMOps를 non-goal로 명시
- [ ] orchestration Spec을 observable behavior 중심으로 갱신
- [ ] `EvidenceSource.DAGSTER` vendor coupling 제거를 Spec에 반영
- [ ] Design에 Airflow-specific implementation decision 기록
- [ ] Tasks가 독립적으로 검증 가능한 결과 단위로 구성됨

## 3. Config adapter

- [ ] Dagster `ConfigurableResource`에서 generic precedence logic 분리
- [ ] plain mapping 기반 adapter 작성
- [ ] 최종 validation authority가 `DataOperationRequest`임을 유지
- [ ] `database_path` override 지원
- [ ] `source_root` override 지원
- [ ] `source_year` override 지원
- [ ] `source_file` override 지원
- [ ] `run_dbt_build` override 지원
- [ ] explicit > environment > default 검증
- [ ] invalid environment가 explicit value에 가려지는 기존 behavior 검증
- [ ] empty path rejection 검증
- [ ] invalid year rejection 검증
- [ ] empty `source_file` rejection 검증
- [ ] adapter unit test가 Airflow runtime 없이 실행 가능

## 4. DAG skeleton

- [ ] `src/project_pivot/orchestration/dags/` 생성
- [ ] DAG module 생성
- [ ] DAG ID `project_pivot_data_plane`
- [ ] Task `load_raw_hmda_loans`
- [ ] Task `build_dbt_loan_analytics`
- [ ] raw → analytics dependency
- [ ] task count = 2
- [ ] `schedule=None`
- [ ] `catchup=False`
- [ ] `max_active_runs=1`
- [ ] `retries=0`
- [ ] new Airflow code가 `airflow.sdk` public interface를 사용
- [ ] DAG top-level에 DuckDB/dbt/file scan side effect 없음
- [ ] DAG import 성공

## 5. Asset/evidence model

- [ ] raw logical Asset identity 정의
- [ ] analytics logical Asset identity 정의
- [ ] environment-specific file path를 Asset identity로 사용하지 않음
- [ ] raw task success 시 raw asset event 기록
- [ ] analytics task complete success 시 analytics asset event 기록
- [ ] task execution state와 asset update 의미를 분리

## 6. Raw stage

- [ ] task가 runtime config를 `DataOperationRequest`로 변환
- [ ] `load_raw_data()`만 호출
- [ ] ingestion implementation duplication 없음
- [ ] `database_path` evidence 확인 가능
- [ ] `source_root` evidence 확인 가능
- [ ] `source_file_count` evidence 확인 가능
- [ ] `source_year` evidence 확인 가능
- [ ] `hmda_loans_row_count` evidence 확인 가능
- [ ] raw failure 시 analytics 미실행
- [ ] raw failure 시 raw asset event를 성공으로 남기지 않음

## 7. Analytics stage

- [ ] `run_dbt_build()` 호출
- [ ] 성공한 build 뒤에만 `promote_dbt_artifacts()` 호출
- [ ] `return_code` evidence 확인 가능
- [ ] `manifest_path` evidence 확인 가능
- [ ] `run_results_path` evidence 확인 가능
- [ ] `projection_id` evidence 확인 가능
- [ ] dbt build failure 시 promotion 미호출
- [ ] dbt build failure 시 analytics asset event 없음
- [ ] promotion failure 시 task FAILED
- [ ] promotion failure 시 analytics asset event 없음

## 8. Skip semantics

- [ ] `run_dbt_build=False` 지원
- [ ] raw task = SUCCESS
- [ ] analytics task = SKIPPED
- [ ] analytics asset event 없음
- [ ] DAG run = SUCCESS
- [ ] skip behavior를 canonical Spec에 명시
- [ ] skip behavior regression test 작성

## 9. XCom boundary

- [ ] `DataOperationRequest`를 XCom으로 전달하지 않음
- [ ] `RawLoadResult`를 XCom으로 전달하지 않음
- [ ] `DbtBuildResult`를 XCom으로 전달하지 않음
- [ ] DataFrame / Arrow table을 XCom으로 전달하지 않음
- [ ] task dependency 자체로 실행 순서를 표현

## 10. Reliability decoupling

- [ ] `EvidenceSource.DAGSTER` 제거
- [ ] `EvidenceSource.ORCHESTRATION` 도입
- [ ] `EvidenceSource.AIRFLOW` 같은 새 vendor coupling을 만들지 않음
- [ ] serialization/test 갱신
- [ ] `reliability-data-contracts` Spec 갱신
- [ ] active reliability guide의 Dagster-specific 문구 갱신
- [ ] reliability behavior 자체는 변경하지 않음

## 11. Test migration

### DAG structure

- [ ] DAG load test
- [ ] DAG ID test
- [ ] task ID test
- [ ] task count test
- [ ] dependency test
- [ ] schedule test
- [ ] catchup test
- [ ] max active runs test
- [ ] retry test
- [ ] asset outlet test

### Config

- [ ] default request
- [ ] environment override
- [ ] explicit override
- [ ] explicit > env
- [ ] invalid env masked by explicit
- [ ] invalid explicit value rejection

### Failure matrix

- [ ] normal run
- [ ] raw failure
- [ ] dbt disabled
- [ ] dbt build failure
- [ ] promotion failure
- [ ] invalid request

## 12. Airflow-native validation

- [ ] Python DAG module import
- [ ] Airflow import-error check
- [ ] focused orchestration pytest
- [ ] `dag.test()` 수준 실행
- [ ] local Airflow runtime bootstrap
- [ ] manual DAG run
- [ ] Airflow UI에서 task state 확인
- [ ] Airflow UI/runtime에서 asset evidence 확인
- [ ] sample HMDA Bronze 적재 확인
- [ ] dbt artifacts 확인
- [ ] current projection 확인

## 13. Local runtime guard

- [ ] local Airflow home을 repository authored source와 분리
- [ ] `.airflow/` 등 runtime generated state가 Git에서 제외됨
- [ ] examples load 비활성화
- [ ] local executor parallelism이 작은 값으로 제한됨
- [ ] production deployment 설정을 migration에 추가하지 않음

## 14. Cutover

Airflow acceptance가 모두 닫히기 전에는 아래를 수행하지 않는다.

- [ ] Airflow runtime behavior parity 확인
- [ ] E2E 성공 확인
- [ ] failure semantics 확인
- [ ] evidence semantics 확인

그 뒤:

- [ ] `dagster` dependency 제거
- [ ] `dagster-dg-cli` 제거
- [ ] `dagster-webserver` 제거
- [ ] `[tool.dg]` 제거
- [ ] `[tool.dg.project]` 제거
- [ ] Dagster definitions 제거
- [ ] Dagster assets 제거
- [ ] Dagster resource 제거
- [ ] Dagster-specific tests 제거/대체
- [ ] `uv.lock`에서 stale Dagster dependency 확인

## 15. Documentation alignment

- [ ] `README.md`
- [ ] `DEVELOPMENT.md`
- [ ] `docs/mvp.md`
- [ ] `docs/ARCHITECTURE.md`
- [ ] `docs/domains/OVERVIEW.md`
- [ ] `docs/domains/orchestration.md`
- [ ] `docs/domains/reliability.md`
- [ ] `openspec/config.yaml`
- [ ] active orchestration instruction/rule
- [ ] vendor-neutral 문서는 불필요하게 수정하지 않음

## 16. Final active-surface scan

아래에서 stale active Dagster reference가 없어야 한다.

- [ ] `src/**`
- [ ] `tests/**`
- [ ] canonical `openspec/specs/**`
- [ ] active docs
- [ ] `pyproject.toml`
- [ ] current agent/rule configuration

다음은 scan failure로 간주하지 않는다.

- [ ] `openspec/changes/archive/**`의 역사 기록
- [ ] 과거 inbox artifact
- [ ] Git history

## 17. Repository validation

- [ ] Ruff check
- [ ] Ruff format check
- [ ] type check
- [ ] focused pytest
- [ ] related integration tests
- [ ] 필요 시 full regression
- [ ] changed Markdown rumdl check
- [ ] CI Lite 통과

## 18. Definition of Done

다음 문장을 하나라도 거짓으로 만들면 migration은 완료가 아니다.

- [ ] Airflow가 유일한 full data-plane orchestrator다.
- [ ] Airflow task는 thin adapter다.
- [ ] Data Operations가 execution/domain behavior를 계속 소유한다.
- [ ] raw → dbt → promotion 순서가 유지된다.
- [ ] control plane은 DAG 밖에 있다.
- [ ] disabled dbt는 `SKIPPED`로 관찰된다.
- [ ] 실패한 analytics는 asset update로 기록되지 않는다.
- [ ] Reliability contract가 Airflow 또는 Dagster vendor에 종속되지 않는다.
- [ ] active Dagster dependency/import/configuration이 없다.
- [ ] canonical Specs, runtime, tests, durable docs가 서로 일치한다.
