---
type: openspec-rpi
title: "Synthetic Lifecycle Evaluation"
description: "Synthetic HMDA case를 실제 incident lifecycle과 evaluation report에 연결하기 위한 근거와 제약을 조사한다."
category: research
status: ready
relatedArtifacts:
  - add-synthetic-lifecycle-evaluation
tags:
  - synthetic-data
  - incident-lifecycle
  - evaluation
---

# Research: synthetic-lifecycle-evaluation

## Question

기존 synthetic generator, HMDA ingestion, read-only incident lifecycle,
evaluation reporter를 연결해 normal과 4개 defect case를 격리 실행하는 OpenSpec
change를 정의할 근거가 충분한가?

## Scope

| Included | Excluded |
| --- | --- |
| normal, row count drop, null spike, schema drift, freshness delay case 실행 | Dagster job, sensor, asset check 등록 |
| case별 임시 DuckDB와 고정 baseline `ProfileSnapshot` | approval 생성과 backfill 실행 |
| synthetic output의 ingestion 호환 staging | dbt model 또는 test 자동 수정 |
| lifecycle 결과를 `EvaluationCaseResult`로 변환 | remediation candidate의 격리 dbt validation |
| 기존 dbt artifact를 사용한 impact analysis | cloud 실행과 장기 monitoring |
| 결정적 evaluation report 생성 | 기존 `pipeline_job` 변경 |

## Findings

| Finding | Evidence | Class |
| --- | --- | --- |
| lifecycle baseline은 source EDA가 아니라 같은 asset과 partition의 `ProfileSnapshot`이어야 한다. | `src/project_pivot/data_operations/incident_lifecycle.py:37`, `src/project_pivot/data_operations/incident_lifecycle.py:97` | Observed |
| baseline은 정상 HMDA source를 별도 임시 DuckDB에 적재한 뒤 기존 `create_profile_snapshot()`으로 생성할 수 있다. | `src/project_pivot/reliability/profiling/profile_snapshot_builder.py:26`, runtime spike: 정상 fixture baseline row count 2와 schema hash 생성 | Observed |
| synthetic writer는 `row_count_drop.parquet`처럼 연도가 없는 filename을 만든다. | `src/project_pivot/hmda_data/synthetic/_writer.py:25` | Observed |
| partition ingestion은 filename에서 네 자리 연도를 추출해 `source_year`로 filter한다. 현재 synthetic filename을 직접 전달하면 네 defect case 모두 빈 partition으로 거부된다. | `src/project_pivot/hmda_data/ingestion/_source_query.py:42`, `src/project_pivot/hmda_data/ingestion/partition.py:127`, runtime spike: schema drift와 freshness 모두 `HMDA 소스 파티션에 적재할 행이 없습니다.` | Observed |
| case file을 `year_2025.parquet`처럼 연도 포함 staging name으로 복사하면 임시 DuckDB ingestion과 lifecycle 실행이 가능하다. | runtime spike: normal과 4개 defect case 모두 lifecycle 반환 | Observed |
| schema drift는 baseline table을 overwrite하는 방식보다 case별 새 DuckDB table을 만들 때 보존된다. 새 table의 inferred schema hash가 baseline과 달라 detector까지 도달한다. | `src/project_pivot/hmda_data/ingestion/partition.py:48`, `src/project_pivot/reliability/profiling/profile_snapshot_builder.py:61`, runtime spike: `schema_drift` 단독 탐지 | Observed |
| freshness generator는 기존 source에 `observed_at` 컬럼을 추가한다. baseline에는 이 컬럼이 없어 현재 상태 그대로면 freshness case가 `schema_drift`와 `freshness_delay`를 함께 탐지한다. | `src/project_pivot/hmda_data/synthetic/cases.py:127`, runtime spike: freshness case detected `schema_drift`, `freshness_delay` | Observed |
| freshness는 request의 `freshness_column`을 명시할 때만 table 값으로 계산된다. 그렇지 않으면 `observed_at` request가 fallback으로 사용되어 delay가 사라진다. | `src/project_pivot/data_operations/request.py:24`, `src/project_pivot/reliability/profiling/profile_snapshot_builder.py:135` | Observed |
| impact analysis는 case별 dbt build 결과를 해석하지 않는다. manifest graph를 읽고 run results file 존재만 확인한다. 따라서 고정 artifact 재사용으로 detection/action evaluation을 격리할 수 있다. | `src/project_pivot/reliability/impact/analyzer.py:11`, `tests/reliability/test_impact_analysis.py:17` | Observed |
| `LifecycleResult`의 detected incident, recommended action, evidence ref를 `EvaluationCaseResult`로 직접 변환할 수 있다. action pass는 required action이 remediation action의 subset인지로 계산된다. | `src/project_pivot/data_operations/lifecycle_result.py:6`, `src/project_pivot/reliability/evaluation/case_result.py:6` | Observed |
| detector와 lifecycle은 incident 및 action 순서를 결정적으로 유지하고 중복을 제거한다. profile, incident, evidence, lineage identifier도 asset과 partition 기반이다. | `src/project_pivot/reliability/detection/detector.py:17`, `src/project_pivot/data_operations/incident_lifecycle.py:126`, `tests/data_operations/test_incident_lifecycle.py:46` | Observed |
| project vision은 null spike, schema drift, freshness delay의 end-to-end evaluation을 다음 단계로 명시한다. | `docs/vision.md:32` | Authoritative |
| 기존 evaluation report는 caller가 만든 case result 집계만 소유하며 test runner orchestration은 명시적 non-goal이었다. 새로운 runner는 별도 capability여야 한다. | `openspec/changes/archive/2026-06-10-add-evaluation-report/design.md:14`, `openspec/specs/evaluation-report/spec.md:9` | Supporting |
| synthetic, lifecycle, report의 기존 focused tests는 독립적으로 통과한다. | `uv run pytest tests/hmda_data/test_synthetic.py tests/data_operations/test_incident_lifecycle.py tests/reliability/test_evaluation_report.py`: 12 passed | Observed |

## Impact

| Area | Impact or risk |
| --- | --- |
| `hmda_data.synthetic` | output file을 ingestion에 전달할 staging naming과 freshness schema 정책이 필요하다. 기존 generator API를 불필요하게 변경하지 않고 evaluation boundary가 정규화할 수 있다. |
| `data_operations` | 기존 load와 lifecycle API를 조합한다. lifecycle의 read-only 경계는 유지해야 한다. |
| `reliability.evaluation` | `EvaluationCaseResult`와 report API는 재사용한다. runner orchestration 책임을 reporter에 넣으면 기존 경계가 흐려진다. |
| DuckDB | case별 database file을 사용해야 schema와 실행 순서가 서로 영향을 주지 않는다. 임시 file만 변경한다. |
| dbt artifacts | manifest와 run results는 read-only input이다. case별 build를 생략하면 data model correctness가 아니라 lifecycle detection/action만 평가한다는 범위를 명시해야 한다. |
| Tests | normal과 4개 defect의 expected incident/action, 반복 실행 결정성, 원본 database와 source 불변성을 검증해야 한다. |

## Conflicts

| Sources | Conflict | Required resolution |
| --- | --- | --- |
| freshness synthetic case vs schema drift rule | freshness generator가 baseline에 없는 `observed_at`을 추가해 freshness 전용 case가 schema drift까지 발생시킨다. | OpenSpec design에서 baseline과 모든 case의 profile schema를 동일하게 만들거나, freshness metadata를 table schema 밖에서 주입하는 정책을 정한다. |
| synthetic writer vs partition ingestion | writer filename에 연도가 없지만 ingestion은 filename에서 `source_year`를 추출한다. | Evaluation runner가 연도 포함 staging filename을 소유한다. 전체 synthetic public API의 naming 변경은 별도 필요가 확인될 때만 수행한다. |
| archived evaluation design vs 새 runner | 기존 evaluation report는 test runner orchestration을 non-goal로 두었다. | `evaluation-report`를 수정하지 않고 새 `synthetic-lifecycle-evaluation` capability로 분리한다. |
| case별 dbt build 기대 vs current impact implementation | lifecycle은 artifact를 요구하지만 impact는 manifest graph와 run results 존재만 사용한다. | 이번 change는 고정 artifact 기반 lifecycle 평가로 제한하고 실제 dbt build validation은 후속 change로 둔다. |

## Assumptions

| Assumption | Validation or containment |
| --- | --- |
| 작은 HMDA fixture가 네 detection threshold를 안정적으로 넘도록 구성할 수 있다. | case별 expected metric과 detector threshold를 integration test에서 직접 assert한다. |
| 고정 manifest가 source에서 downstream asset까지의 현재 lineage를 대표한다. | repository의 dbt artifact fixture 또는 최소 manifest를 사용하고 affected asset을 assert한다. |
| action success는 이번 change에서 remediation 실행 성공이 아니라 required draft action 존재를 뜻한다. | 기존 `EvaluationCaseResult.action_passed` semantics를 그대로 사용하고 report field 이름을 변경하지 않는다. |
| 임시 directory cleanup이면 source와 project database를 보존할 수 있다. | test 전후 원본 file hash와 configured database path 불변성을 확인한다. |

## Open Questions

- Freshness case의 schema를 맞추는 최소 방식은 baseline 정상 case에도 고정
  `observed_at`을 추가하는 것인가, 아니면 freshness 값을 profile input으로 분리하는
  것인가? 두 방식은 public data contract와 구현 범위를 materially 바꾸므로
  OpenSpec design에서 선택해야 한다.

## Handoff

| Field | Content |
| --- | --- |
| Problem | 개별 synthetic generator, lifecycle, evaluation reporter는 존재하지만 실제 case 실행 결과를 연결하는 production evaluation API가 없다. 현재 synthetic output은 filename과 freshness schema 때문에 ingestion/lifecycle에 그대로 연결되지 않는다. |
| Scope | normal과 4개 defect를 case별 임시 DuckDB에서 실행하고, 연도 포함 staging과 freshness schema 정규화 뒤 lifecycle 결과를 `EvaluationCaseResult`와 report로 변환한다. Dagster, recovery, dbt mutation은 제외한다. |
| Validation candidates | 5개 case expected incident/action 일치, detection/action success 100%, 두 번 실행 결과 동일, case 간 schema 격리, 원본 source와 project database 불변, freshness case의 의도치 않은 schema drift 없음 |
| Risks | freshness schema 정규화가 synthetic data contract를 넓힐 수 있음, 고정 dbt artifact는 actual dbt model execution을 검증하지 않음, filename staging이 숨은 ingestion convention이 될 수 있음 |
| Next action | OpenSpec proposal에서 새 `synthetic-lifecycle-evaluation` capability와 non-goals를 정의하고, design에서 freshness schema 정책을 결정한다. |
