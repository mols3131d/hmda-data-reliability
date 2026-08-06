---
status: approved
reviewer: review-lead
date: 2026-08-06
target: hmda-eda
review-topic: baseline-reduce-core-scope
revision: 887853cb
---

# Review: HMDA EDA Baseline Core Scope Reduction

## Overview

본 리뷰는 `hmda-eda-baseline-reduce-core-scope` 변경 사항(Commit `887853cb`) 및 최신 코드베이스 상태를 기준(Revision)으로 수행된 최종 검토 결과입니다.

`reviews/` 디렉토리 규칙(`reviews/<target>-<review-topic>.md`)에 맞춰 작성되었으며, 기존 하위 폴더 레거시 리뷰 기록은 유지됩니다.

**최종 결정: Approved (제한적 승인)**

- 6개 Core 컬럼 중심의 EDA 에비던스 수축, 불필요한 계산/모듈(fixture, memory) 제거 및 API 격리가 안정적으로 수행되었습니다.
- 단, Marimo 통합 테스트의 거짓 통과(False Green) 위험과 하드코딩된 Dead Code 등 후속 해결이 필요한 지적 사항이 존재합니다.

---

## 1. Reviewed Revision & Scope

- **Target**: `hmda-eda` / `baseline-reduce-core-scope`
- **Revision**: Commit `887853cb` (`feat(hmda-data): reduce eda scope to core contract and minimal notebook`)
- **Scope**:
  - `src/project_pivot/hmda_data/eda/`
  - `tests/hmda_data/eda/`
  - `notebooks/eda_mo.py`
  - `docs/references/hmda_eda.md`

---

## 2. Verified Facts

1. **Core Scope 계산 수축**:
   - `analysis.py`에서 `anomalies`, `freshness`, `schema_hash`, 고유값이 큰 `county_code` 분포 계산이 정상 제거되었습니다.
   - 6개 핵심 컬럼(`activity_year`, `state_code`, `county_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`)에 대한 분포 및 기술통계 에비던스만 안전하게 반환합니다.
1. **Fixture/Memory 서브시스템 완전 제거**:
   - `fixture.py`, `memory.py`, `scripts/prepare_hmda_eda_fixture.py`, `scripts/run_hmda_eda_memory.py`가 완전 삭제되었습니다.
   - `__init__.py`에서 관련 API export가 제거되었으며, public API 격리가 보호됨을 확인했습니다 (`test_eda_public_api_compatibility`).
1. **코드 스타일 및 가독성 개선**:
   - `tests/hmda_data/eda/test_eda_notebook.py` 함수 내부에 존재하던 로컬 `import os`, `import shutil` 선언이 최상단(Module level)으로 정리되었습니다.

---

## 3. Defects & Risks

### 3.1. [Defect / Maintainability] Marimo 통합 테스트의 거짓 통과 (False Green)

- **Location**: [tests/hmda_data/eda/test_eda_notebook.py](tests/hmda_data/eda/test_eda_notebook.py#L79)
- **Evidence**: `assert "activity_year_counts" in content or "evidence" in content`
- **Impact**: Marimo HTML export 시 노트북의 Python 소스 코드가 HTML 내부에 임베딩됩니다. 이로 인해 셀 렌더링 실패나 런타임 오류가 발생하더라도 소스 코드 내 `"evidence"` 문자열로 인해 테스트가 항상 참(True)으로 평가될 수 있습니다.
- **Required Action**: 단순 문자열 매칭 대신 구조화된 결과 검증 또는 Marimo 런타임 셀 에러 비존재를 명시적으로 검증하도록 단언문 개선 필요.

### 3.2. [Defect / Dead Code] 도달 불가능한 데이터 소스 분기

- **Location**: [notebooks/eda_mo.py](notebooks/eda_mo.py) (Cell 2)
- **Evidence**: `data_is_sample = True` 상수가 고정되어 있어 `else` 구문(`data/raw/hmda/year_2025.csv`)으로 진입이 불가능합니다.
- **Impact**: UI 위젯과 바인딩되어 있지 않아 실제 Raw 데이터 경로로의 동적 전환이 불가합니다.
- **Required Action**: `mo.ui.checkbox` 등 UI 컴포넌트와 연결하여 동적 스위칭 지원.

### 3.3. [Risk / Operational Reliability] 대용량 메모리 워크로드 자동 검증 부재

- **Evidence**: `test_eda_memory.py` 및 `run_hmda_eda_memory.py` 삭제.
- **Impact**: 1,350만 건 규모의 대용량 HMDA 데이터셋 처리 시 DuckDB 메모리 초과(OOM)를 감지하는 자동화 회귀 테스트가 부재합니다.
- **Required Action**: 추후 DuckDB 스트리밍 쿼리 단위 테스트 등 가벼운 형태의 메모리 안전망 구축 검토.

### 3.4. [Improvement] 상대 경로 의존성

- **Location**: [tests/hmda_data/eda/test_eda_notebook.py](tests/hmda_data/eda/test_eda_notebook.py#L38)
- **Evidence**: `notebook_path = Path("notebooks/eda_mo.py")`
- **Impact**: pytest 실행 위치(CWD)가 루트가 아닐 경우 테스트가 `pytest.skip`되거나 실패할 수 있습니다.
- **Required Action**: `Path(__file__)` 기준 절대 경로 동적 계산으로 변경.

---

## 4. Validations Performed & Omitted

- **Performed Validation**:
  - `uv run pytest tests/hmda_data/eda/` 실행 (14개 테스트 모두 통과)
  - `uv run ruff format . && uv run ruff check --fix .` 실행 (All checks passed)
- **Omitted Validation**:
  - 대용량 raw dataset(1,350만 건) 부하 검증 (Core Scope 축소 방침에 따라 제외됨)

---

## 5. Remaining Risk

Marimo 통합 테스트의 False Positive 단언문 문제(3.1)로 인해, 향후 노트북 렌더링 셀 파이프라인 오류 발생 시 CI에서 이를 즉시 포착하지 못할 가능성이 일부 남아있습니다. 이는 후속 릴리스/변경 단계에서 최우선 개선해야 합니다.
