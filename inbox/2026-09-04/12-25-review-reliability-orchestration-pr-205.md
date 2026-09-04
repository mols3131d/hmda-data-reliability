---
type: review
title: "PR 205 Review: 2026 Defect Evaluation and Orchestration Quality Gate"
description: "PR 205 최신 헤드(77779b1)의 2026년 가상 합성 결함 평가 체계와 Airflow 품질 게이트를 종합 검토하고 발견된 결함 및 개선 사항을 기록한다."
status: completed
tags:
  - reliability
  - orchestration
  - hmda-data
  - data-operations
  - openspec
---

# PR 205 Review: 2026 Defect Evaluation and Orchestration Quality Gate

> [!NOTE]
> PR 205는 2026년 가상 결함 생성(`null_spike`) 제약과 샌드박스 격리 수명주기 E2E 검증 체계를 충실히 완성하고 Airflow 품질 게이트를 추가했습니다. 그러나 **(1) 0-row 빈 파티션 인제스션 시 품질 게이트가 `status=clean`으로 침묵 통과하는 결함 은폐 위험**, **(2) `evaluate_quality_gate_task`에서 `raise ... from None`으로 인한 예외 인과 체인 절단**, **(3) 테스트 단언문의 불린 연산자 우선순위로 인한 느슨한 검증**, **(4) 단일 PR 내 2개 독립 OpenSpec 변경 번들링**이 확인되어 현재 판정은 **Revise**입니다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| PR #205 `feat(reliability): 2026년 가상 합성 결함 평가 체계 및 수명주기 검증 추가` | [77779b1](https://github.com/mols3131d/hmda-data-reliability/commit/77779b1df21a7576b73aab60fcb34535e606ee21) | [`src/hmda_reliability/hmda_data/synthetic/cases.py`](../../src/hmda_reliability/hmda_data/synthetic/cases.py), [`src/hmda_reliability/orchestration/quality_gate.py`](../../src/hmda_reliability/orchestration/quality_gate.py), [`src/hmda_reliability/orchestration/dags/hmda_data_plane.py`](../../src/hmda_reliability/orchestration/dags/hmda_data_plane.py), [`tests/data_operations/test_incident_lifecycle.py`](../../tests/data_operations/test_incident_lifecycle.py), [`tests/orchestration/test_quality_gate.py`](../../tests/orchestration/test_quality_gate.py), [`tests/orchestration/test_airflow_execution.py`](../../tests/orchestration/test_airflow_execution.py), [`openspec/changes/`](../../openspec/changes/) | Revise |

## Findings

### F1. Silent Pass and Defect Masking on Empty Partition (0-Row) in Quality Gate

- **Severity** - Major
- **Location** - [`src/hmda_reliability/orchestration/quality_gate.py`](../../src/hmda_reliability/orchestration/quality_gate.py#L60-L125)
- **Evidence** - 적재된 파티션에 데이터가 없는(`row_count == 0`) 상태에서 `evaluate_quality_gate`를 실행하면 [`src/hmda_reliability/reliability/profiling/profile_snapshot_builder.py`](../../src/hmda_reliability/reliability/profiling/profile_snapshot_builder.py#L208-L210)에서 `_null_rate`가 `0.0`을 반환하고 `_build_baseline()`이 `row_count=0`을 그대로 복제합니다. 그 결과 [`src/hmda_reliability/reliability/detection/detector.py`](../../src/hmda_reliability/reliability/detection/detector.py#L40)의 `_detect_volume_drop`은 `baseline.row_count == 0` 가드에 걸려 이상을 감지하지 않고, `_detect_null_spike`는 `0.0 - 0.003 = -0.003 < 0.05`로 평가되어 탐지 결과가 0건이 됩니다. 이로 인해 `QualityGateError`가 발생하지 않고 `status=clean` 로그를 남기며 정상 통과합니다.
- **Impact** - 소스 파일 누락이나 인제스션 필터 오류로 파티션이 0건 적재된 비정상 상태에서도 품질 게이트가 파이프라인을 실패시키지 못하고 downstream `build_dbt_loan_analytics` 태스크로 진행되는 False Negative가 발생합니다.
- **Required Change** - [`src/hmda_reliability/orchestration/quality_gate.py`](../../src/hmda_reliability/orchestration/quality_gate.py)에서 스냅샷 생성 후 `current.row_count == 0`일 때 명시적으로 `QualityGateError`를 발생시키거나 최소 행 수 검증 가드를 추가하고, 관련 테스트 케이스를 작성해야 합니다.

### F2. Exception Chaining Severed with `raise AirflowException(...) from None`

- **Severity** - Major
- **Location** - [`src/hmda_reliability/orchestration/dags/hmda_data_plane.py`](../../src/hmda_reliability/orchestration/dags/hmda_data_plane.py#L98-L104), [`tests/orchestration/test_airflow_execution.py`](../../tests/orchestration/test_airflow_execution.py#L273-L288)
- **Evidence** - `evaluate_quality_gate_task`에서 `QualityGateError` 외의 일반 예외(`except Exception:`)를 처리할 때 `raise AirflowException(...) from None`을 사용하여 PEP 3134 예외 인과 체인을 단절하고 있으며, 테스트([`tests/orchestration/test_airflow_execution.py`](../../tests/orchestration/test_airflow_execution.py#L287))에서도 `assert exc_info.value.__cause__ is None`을 강제하고 있습니다. 이는 저장소의 [`.github/instructions/python.instructions.md`](../../.github/instructions/python.instructions.md) 원칙("preserve causal context when translating exceptions") 및 narrow exception 처리 원칙과 충돌합니다.
- **Impact** - DuckDB 파일 락 경합, I/O 오류, `ValueError`(지원되지 않는 baseline 프로파일 컬럼 요청 시 발생) 등 런타임 장애 발생 시 근본 원인(`__cause__`)이 유실되어 Sentry나 운영 모니터링 체계에서 장애 원인 식별이 지연됩니다.
- **Required Change** - `raise AirflowException(f"품질 게이트 평가 실패: source_year={request.source_year} asset={request.asset_name}: {exc}") from exc` 형태로 원본 예외 체인을 보존하도록 수정하고, 테스트 단언문도 `assert exc_info.value.__cause__ is not None`으로 갱신해야 합니다.

### F3. Loose Test Assertion Caused by Boolean Operator Precedence

- **Severity** - Minor
- **Location** - [`tests/orchestration/test_quality_gate.py`](../../tests/orchestration/test_quality_gate.py#L70-L75)
- **Evidence** - `test_quality_gate_passes_when_no_anomaly_detected`의 단언문이 다음과 같이 작성되어 있습니다:

  ```python
  assert any(
      "품질 게이트 통과" in record.message
      and "status=clean" in record.message
      or getattr(record, "status", None) == "clean"
      for record in caplog.records
  )
  ```

  Python에서 `and`가 `or`보다 연산 우선순위가 높아 `(A and B) or C`로 결합됩니다. 그러나 실제 구현([`src/hmda_reliability/orchestration/quality_gate.py`](../../src/hmda_reliability/orchestration/quality_gate.py#L119-L126))의 로그 메시지에는 `"status=clean"` 문자열이 포함되지 않고 `extra` 필드로만 넘겨지므로, `(A and B)`는 항상 `False`가 되며 오직 `C` 조건만으로 단언문이 성립하고 있습니다.
- **Impact** - 핵심 로그 메시지 문구인 `"품질 게이트 통과"` 검증이 실질적으로 무력화되어 있어, 로그 문구가 유실되거나 변조되어도 `extra` 필드만 존재하면 테스트가 통과하는 False Green 위험이 발생합니다.
- **Required Change** - `assert any("품질 게이트 통과" in record.message and getattr(record, "status", None) == "clean" for record in caplog.records)` 형태로 단언문을 결합하여 메시지와 메타데이터를 모두 엄격히 검증해야 합니다.

### F4. Scope Mismatch and Bundled Independent OpenSpec Changes

- **Severity** - Minor
- **Location** - [`openspec/changes/reliability-synthetic-2026-evaluation/`](../../openspec/changes/reliability-synthetic-2026-evaluation/), [`openspec/changes/orchestration-quality-gate/`](../../openspec/changes/orchestration-quality-gate/), [`openspec/changes/orchestration-quality-gate/tasks.md`](../../openspec/changes/orchestration-quality-gate/tasks.md)
- **Evidence** - PR 제목 및 설명은 `reliability` 도메인(2026년 합성 결함 평가 체계)에 국한되어 있으나, 커밋 [77779b1](https://github.com/mols3131d/hmda-data-reliability/commit/77779b1df21a7576b73aab60fcb34535e606ee21)에서 `orchestration` 도메인(Airflow 품질 게이트)의 신규 capability 및 OpenSpec 변경이 함께 추가되었습니다. 또한 [`openspec/changes/orchestration-quality-gate/tasks.md`](../../openspec/changes/orchestration-quality-gate/tasks.md) 프론트매터에 `title`, `description`, `tasks_completed`, `tasks_total` 메타데이터가 누락되어 있습니다.
- **Impact** - OpenSpec 도메인 격리 원칙이 약화되고, 릴리즈 및 스펙 아카이빙 시 변경 추적성이 저하됩니다.
- **Required Change** - PR을 두 개의 독립 PR로 분리(권장)하거나, 단일 PR 유지 시 PR 제목과 본문에 품질 게이트 작업을 명시하고 [`tasks.md`](../../openspec/changes/orchestration-quality-gate/tasks.md) 프론트매터를 표준에 맞게 보완해야 합니다.

### F5. Partition Ingestion Risk When Custom `case_name` Lacks 4-Digit Year

- **Severity** - Minor
- **Location** - [`src/hmda_reliability/hmda_data/synthetic/cases.py`](../../src/hmda_reliability/hmda_data/synthetic/cases.py#L210-L215), [`src/hmda_reliability/hmda_data/ingestion/_source_query.py`](../../src/hmda_reliability/hmda_data/ingestion/_source_query.py#L110-L117)
- **Evidence** - 파티션 인제스션 엔진([`_source_year_sql`](../../src/hmda_reliability/hmda_data/ingestion/_source_query.py#L110-L117))은 파일명에서 `(\d{4})` 정규식으로 `source_year`를 추출합니다. `null_spike()`의 기본 파일명은 `null_spike_{target_year}.parquet`로 안전하지만, 호출자가 숫자가 없는 임의의 `case_name`(예: `case_name="custom_spike"`)을 전달하면 `source_year`가 `NULL`이 되어 `load_hmda_loans_partition` 실행 시 `HMDADataLoadError("HMDA 소스 파티션에 적재할 행이 없습니다.")`가 발생합니다.
- **Impact** - 합성 결함 산출물을 파티션 인제스션 파이프라인으로 연계할 때 예기치 않은 런타임 적재 실패를 유발합니다.
- **Required Change** - `target_year` 전달 시 `case_name`에 해당 연도 숫자가 포함되어 있는지 검증하거나, `case_name`에 자동으로 `_{target_year}` 접미사를 보장하도록 방어 가드를 추가하는 것을 권장합니다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| 도메인 통합 회귀 테스트 | `pytest tests/orchestration/ tests/hmda_data/ tests/data_operations/` 131개 통과 | Pass |
| Python 정적 린트 | `ruff check .` 전체 통과 | Pass |
| Markdown 정적 린트 | `rumdl check .` 151개 파일 전체 통과 | Pass |
| OpenSpec 스키마 검증 | `openspec validate` 20개 항목 통과 | Pass |
| 이전 코드 리뷰(F1~F6) 개선 확인 | DuckDB `REPLACE` 절 충돌 방지, 다중 연도 가드, `target_year` 정수 범위 검증 확인 | Pass |
| 빈 파티션(0-row) 게이트 방어 가드 | `current.row_count == 0`일 때 `QualityGateError` 미발생 및 clean 침묵 통과 (F1) | Fail |
| 에러 체이닝 및 단언문 엄격성 | `raise ... from None` 사용 및 불린 결합 오라클 확인 (F2, F3) | Fail |

## Remaining Risks

- **DuckDB 동시성 및 파일 잠금**: 멀티 프로세스 Airflow 환경에서 `retries=0` 태스크 실행 시 파일 경합으로 인한 간헐적 실패 위험이 남아 있으며, 이는 F2의 원본 예외 체인 보존을 통해 운영 관측성을 확보해야 합니다.
- **기준선 고정값 편차**: `_BASELINE_NULL_RATES`가 2025년 기준 정적 매핑(`income: 0.003`, `loan_amount: 0.001`)으로 고정되어 있어 향후 실제 2026년 공공 데이터 유입 시 정상 데이터셋의 기본 결측률 변동에 대응하기 위한 동적 기준선 확장이 요구될 수 있습니다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | 빈 파티션 무결함 침묵 통과(F1)와 예외 체이닝 단절(F2), 단언문 오라클 결함(F3) 등 신뢰성 및 운영 안정성 개선이 필요함 | PR #205 브랜치(`agent/feat/synthetic-2026-reliability-workflow`) 보완 커밋 반영 |
