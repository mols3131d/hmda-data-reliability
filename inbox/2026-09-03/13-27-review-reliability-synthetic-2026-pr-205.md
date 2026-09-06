---
type: review
title: "PR 205 Review"
description: "PR 205의 2026년 합성 결함 생성 확장, 격리 수명주기 평가 통합 테스트, OpenSpec 명세 일관성을 검토하고 머지 전 필요한 수정 사항을 기록한다."
status: completed
tags:
  - reliability
  - hmda-data
  - data-operations
  - openspec
---

# PR 205 Review

> [!NOTE]
> PR 205는 격리된 샌드박스 환경에서 2026년 가상 합성 결함 데이터(`null_spike`)를 평가하고 신뢰성 수명주기(`run_incident_lifecycle`)를 종단간으로 검증하는 핵심 기반을 잘 마련했습니다. 다만 (1) `target_column == "activity_year"`와 `target_year` 동시 지정 시 DuckDB 쿼리 엔진의 `REPLACE` 절 충돌 런타임 오류, (2) 통합 테스트에서 실제 `null_spike()` 산출물을 적재하지 않고 수동 SQL 주입을 사용하여 발생한 E2E 단절 및 파일명 정규식 불일치 위험, (3) 멀티 연도 입력 시 윈도우 파티션 붕괴, (4) `target_year` 범위 유효성 검증 부재, (5) OpenSpec 델타 스펙 누락 등의 결함이 확인되어 현재 판정은 **Revise**입니다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| PR #205 `feat(reliability): 2026년 가상 합성 결함 평가 체계 및 수명주기 검증 추가` | [dc172379bee2649de0a084516c37ad581575c1a0](https://github.com/mols3131d/hmda-data-reliability/commit/dc172379bee2649de0a084516c37ad581575c1a0) | [`src/hmda_reliability/hmda_data/synthetic/cases.py`](../../src/hmda_reliability/hmda_data/synthetic/cases.py), [`tests/hmda_data/test_synthetic.py`](../../tests/hmda_data/test_synthetic.py), [`tests/data_operations/test_incident_lifecycle.py`](../../tests/data_operations/test_incident_lifecycle.py), [`openspec/changes/reliability-synthetic-2026-evaluation/`](../../openspec/changes/reliability-synthetic-2026-evaluation/) | Revise |

## Findings

### F1. `target_column == "activity_year"`와 `target_year` 동시 지정 시 DuckDB `REPLACE` 절 충돌 및 런타임 오류

- **Severity** - Major
- **Location** - [`src/hmda_reliability/hmda_data/synthetic/cases.py`](../../src/hmda_reliability/hmda_data/synthetic/cases.py#L111-L151)
- **Evidence** - `null_spike()` 함수에서 `target_column="activity_year"`와 `target_year=2026`을 동시에 전달하면, DuckDB의 `REPLACE` 절 내부에 동일한 대상 컬럼이 중복으로 렌더링됩니다:

  ```sql
  REPLACE (
      CASE WHEN "activity_year" IS NOT NULL AND ... THEN NULL ELSE "activity_year" END AS "activity_year",
      CAST(? AS INTEGER) AS activity_year
  )
  ```

  DuckDB는 `REPLACE` 절에서 동일 컬럼의 중복 지정을 허용하지 않으므로 바인더 예외(`Binder Error: Column with name "activity_year" specified more than once in REPLACE clause`)가 발생하며, 저수준 오류가 `SyntheticCaseError`로 래핑되어 실행이 중단됩니다.
- **Impact** - 특정 연도의 `activity_year` 자체에 결측치를 주입하려는 시나리오에서 쿼리 바인딩 실패가 발생하거나, 만약 후행 표현식이 적용되더라도 모든 행의 `activity_year`가 결측치 없이 `target_year`로 덮어써져 결측치 증가 계약이 무효화됩니다.
- **Required Change** - [`src/hmda_reliability/hmda_data/synthetic/cases.py`](../../src/hmda_reliability/hmda_data/synthetic/cases.py#L75) 부근에서 `target_year is not None and target_column == "activity_year"`인 경우 상호 모순을 명시하는 `SyntheticCaseError`를 즉시 발생시키도록 사전 가드를 추가해야 합니다.

### F2. 합성 결함 생성 체계(`null_spike`)와 수명주기 검증 간 통합 단절 및 파일명-파티션 불일치 위험

- **Severity** - Major
- **Location** - [`tests/data_operations/test_incident_lifecycle.py`](../../tests/data_operations/test_incident_lifecycle.py#L190-L245), [`src/hmda_reliability/hmda_data/synthetic/cases.py`](../../src/hmda_reliability/hmda_data/synthetic/cases.py#L58-L60), [`src/hmda_reliability/hmda_data/ingestion/_source_query.py`](../../src/hmda_reliability/hmda_data/ingestion/_source_query.py#L110-L117)
- **Evidence** - [`openspec/changes/reliability-synthetic-2026-evaluation/proposal.md`](../../openspec/changes/reliability-synthetic-2026-evaluation/proposal.md) 및 [`openspec/changes/reliability-synthetic-2026-evaluation/tasks.md`](../../openspec/changes/reliability-synthetic-2026-evaluation/tasks.md)에서는 "2026년 합성 결함 데이터셋 생성 및 샌드박스 격리 적재를 통한 신뢰성 수명주기 종단간 검증"을 명시하고 있습니다.
  그러나 추가된 통합 테스트 [`tests/data_operations/test_incident_lifecycle.py`](../../tests/data_operations/test_incident_lifecycle.py#L190-L245)는 `null_spike()` 생성기나 파티션 인제스션 API(`load_hmda_loans_partition`)를 전혀 사용하지 않고, 샌드박스 DB에 DDL(`CREATE TABLE raw.hmda_loans`)과 4건의 레코드를 수동 문자열 SQL `INSERT INTO`로 직접 주입하고 있습니다.
  또한 `null_spike()`의 기본 `case_name`은 `"null_spike"`이며, 이 경우 생성되는 파일은 `null_spike.parquet`이 됩니다. 리포지토리의 파티션 적재 메타데이터 생성 쿼리인 [`src/hmda_reliability/hmda_data/ingestion/_source_query.py`](../../src/hmda_reliability/hmda_data/ingestion/_source_query.py#L110-L117)은 파일명에서 4자리 연도를 정규식(`regexp_extract(parse_filename(filename), '(\\d{4})', 1)`)으로 추출하므로, 기본 파일명으로 생성된 산출물을 파티션 인제스션 함수에 전달하면 `source_year`가 `NULL`이 되어 `WHERE source_year = 2026`에서 0개 행이 조회되어 `HMDADataLoadError("HMDA 소스 파티션에 적재할 행이 없습니다.")`로 적재가 실패합니다.
- **Impact** - 실제 합성 생성기 산출물과 신뢰성 수명주기 러너 간의 결합 검증이 누락되어, 실전 파이프라인에서 합성 파일을 인제스션하여 평가하려고 할 때 파일명 제약 및 `source_year` 메타데이터 불일치로 실패하는 결함이 은폐됩니다 (False Green 위험).
- **Required Change** - [`tests/data_operations/test_incident_lifecycle.py`](../../tests/data_operations/test_incident_lifecycle.py#L190-L245)에서 수동 SQL `INSERT` 대신 `null_spike(..., target_year=2026, case_name="null_spike_2026")`로 실제 Parquet 산출물을 생성하고 이를 파티션 인제스션(`load_hmda_loans_partition`)하여 `run_incident_lifecycle()`로 평가하는 종단간 흐름으로 재구성하거나, 최소한 합성 생성 산출물의 적재 호환성을 검증하는 통합 테스트를 명시적으로 보강해야 합니다.

### F3. 멀티 연도 원천 데이터 입력 시 윈도우 파티션 계산 왜곡 및 파티션 붕괴

- **Severity** - Minor
- **Location** - [`src/hmda_reliability/hmda_data/synthetic/cases.py`](../../src/hmda_reliability/hmda_data/synthetic/cases.py#L115-L150)
- **Evidence** - CTE `year_stats` 내부에서는 원천 데이터의 기존 `activity_year` 컬럼을 기준으로 윈도우 집계(`PARTITION BY activity_year`)를 수행하여 연도별 행 수(`__year_count`), non-null 개수(`__year_non_null`), 샘플 순위(`__sample_rank`, `__non_null_rank`)를 계산합니다. 이후 최외곽 `SELECT`에서 `REPLACE ( ... CAST(? AS INTEGER) AS activity_year )`를 통해 모든 원천 연도 행의 `activity_year`를 `target_year`로 강제 오버라이드합니다.
- **Impact** - 호출자가 2개 이상의 연도(예: 2024년과 2025년 데이터)가 혼합된 원천 파일 목록을 `source_paths`로 넘겨주고 `target_year=2026`을 지정할 때, 각 원천 연도 파티션별로 독립적으로 결측치 변환 개수가 계산된 후 단일 2026년으로 병합되므로, 원천 그룹 간 결측률 차이에 따라 2026년 파티션 내 결측치 분포가 왜곡되거나 순위 번호가 중복 집계되는 통계적 비균질성(Partition Collapse)이 발생합니다.
- **Required Change** - `target_year`가 지정된 경우, 원천 데이터가 단일 연도 파티션인지 검증하거나, `year_stats` CTE의 `PARTITION BY` 기준을 오버라이드된 연도(또는 전체 단일 파티션)로 일관되게 정렬하도록 명확한 계약을 수립해야 합니다.

### F4. `target_year` 매개변수 유효성 검증(타입 및 도메인 범위) 부재

- **Severity** - Minor
- **Location** - [`src/hmda_reliability/hmda_data/synthetic/cases.py`](../../src/hmda_reliability/hmda_data/synthetic/cases.py#L69-L80)
- **Evidence** - `null_fraction`과 `sample_fraction`은 `_validate_fraction`을 통해 범위를 엄격히 검증하지만, `target_year`에 대해서는 타입(정수 여부, `bool` 제외 여부) 및 도메인 유효 범위($2000 \le \text{year} \le 2100$) 검증이 없습니다. Python에서 `bool`은 `int`의 서브클래스이므로 `target_year=True`가 전달되면 DuckDB의 `CAST(true AS INTEGER)`에 의해 `activity_year=1`인 데이터가 에러 없이 조용히 생성됩니다.
- **Impact** - 리포지토리 전역 표준인 [`src/hmda_reliability/data_operations/request.py`](../../src/hmda_reliability/data_operations/request.py#L20) 및 [`src/hmda_reliability/reliability/contracts/recovery_proposal.py`](../../src/hmda_reliability/reliability/contracts/recovery_proposal.py#L82)에서는 `ge=2000, le=2100`으로 연도 범위를 명확히 제한하고 있습니다. 비정상적인 연도 파티션(예: 1년, 음수 연도)이 포함된 Parquet 파일이 생성되어 후속 dbt 모델 빌드나 파티션 기반 분석 마트에서 잠재적 장애를 유발할 수 있습니다.
- **Required Change** - `target_year is not None`일 때 `isinstance(target_year, int) and not isinstance(target_year, bool)` 및 $2000 \le \text{target\_year} \le 2100$ 범위를 검증하고 위반 시 `SyntheticCaseError`를 발생시키도록 가드를 추가해야 합니다.

### F5. OpenSpec 델타 스펙 누락 및 문서 최신화 누락

- **Severity** - Minor
- **Location** - [`openspec/changes/reliability-synthetic-2026-evaluation/proposal.md`](../../openspec/changes/reliability-synthetic-2026-evaluation/proposal.md), `openspec/changes/reliability-synthetic-2026-evaluation/specs/data-operations-incident-lifecycle/spec.md`, [`src/hmda_reliability/hmda_data/synthetic/cases.py`](../../src/hmda_reliability/hmda_data/synthetic/cases.py#L63-L68)
- **Evidence** -
  1. `proposal.md`에서 `Modified Capabilities`로 `hmda-data-synthetic-defects`를 선언했으나, `specs/` 하위에는 `data-operations-incident-lifecycle/spec.md`만 존재하고 `hmda-data-synthetic-defects/spec.md` 델타 스펙이 누락되었습니다.
  1. [`src/hmda_reliability/hmda_data/synthetic/cases.py`](../../src/hmda_reliability/hmda_data/synthetic/cases.py#L63-L68)의 `null_spike` docstring에 신규 매개변수인 `case_name`과 `target_year`에 대한 설명이 갱신되지 않았습니다.
  1. `openspec/changes/reliability-synthetic-2026-evaluation/specs/data-operations-incident-lifecycle/spec.md`에 명시된 시나리오 조건인 `AND 메인 데이터베이스 상태는 변경되지 않아야 한다.`를 검증하는 단언문이 통합 테스트 [`tests/data_operations/test_incident_lifecycle.py`](../../tests/data_operations/test_incident_lifecycle.py#L190-L245)에 누락되어 있습니다.
- **Impact** - OpenSpec 스펙 시스템의 계약 일관성 훼손 및 API 문서 최신화 누락, 명세와 테스트 간 검증 단절이 발생합니다.
- **Required Change** - `openspec/changes/reliability-synthetic-2026-evaluation/specs/hmda-data-synthetic-defects/spec.md` 델타 스펙을 작성하여 추가하고, `null_spike()` docstring에 매개변수 설명을 보강하며, 통합 테스트에 메인 DB 파일 변경 없음 단언문을 보강해야 합니다.

### F6. 테스트 오라클 단언문 엄격성 부족

- **Severity** - Minor
- **Location** - [`tests/data_operations/test_incident_lifecycle.py`](../../tests/data_operations/test_incident_lifecycle.py#L245)
- **Evidence** - [`tests/data_operations/test_incident_lifecycle.py`](../../tests/data_operations/test_incident_lifecycle.py#L245)에서 수명주기 결과의 권고 조치 검증이 `assert len(result.recommended_actions) > 0`으로만 단언되어 있습니다. 동일 파일의 다른 테스트([`tests/data_operations/test_incident_lifecycle.py`](../../tests/data_operations/test_incident_lifecycle.py#L70-L82))에서 구체적 액션 목록(`inspect_source_columns`, `add_dbt_not_null_test`)과 `evidence_refs`를 엄격히 검증하는 것과 대조적입니다.
- **Impact** - 잘못된 권고 조치(예: 엉뚱한 컬럼이나 액션 타입)가 도출되더라도 테스트가 통과하는 false green 위험이 있습니다.
- **Required Change** - 기대되는 구체적인 권고 조치 목록(`inspect_source_columns`, `add_dbt_not_null_test` 등)을 명시적으로 비교 검증하도록 단언문을 강화해야 합니다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| 정적 타입 및 진단 검사 | Pylance / Ruff `check` 통과 (0 error) | Pass |
| 변경 단위 및 통합 테스트 | `pytest tests/hmda_data/test_synthetic.py tests/data_operations/test_incident_lifecycle.py` (21 passed in 3.47s) | Pass |
| 관련 도메인 전체 회귀 테스트 | `pytest tests/data_operations/ tests/hmda_data/ tests/orchestration/` (116 passed in 4.67s) | Pass |
| 합성 Parquet 적재 E2E 결합 검증 | 수동 SQL `INSERT`로 대체되어 미실행 | Not Verified |

## Remaining Risks

- `null_spike` 외의 대등한 합성 결함 함수군(`row_count_drop`, `schema_drift`)에는 `target_year` 및 `case_name` 파라미터가 아직 확장되지 않아 향후 복합 결함 시나리오 평가 시 추가 확장이 필요합니다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | 쿼리 엔진 런타임 오류 가능성(F1), E2E 테스트 오라클 단절(F2), 연도 유효성 검증 누락(F4) 및 OpenSpec 델타 스펙 누락(F5)에 대한 보완 필요 | PR #205 revision |
