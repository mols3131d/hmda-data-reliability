---
status: approved
reviewer: review-lead
date: 2026-08-06
---

# Review: HMDA EDA Core Scope Reduction

## Overview

이 리뷰는 `hmda-eda-baseline-reduce-core-scope` 작업 변경 사항에 대해 Quality Review와 Adversarial Review 결과를 종합한 최종 평가입니다. 이 변경 사항은 HMDA EDA의 복잡성을 줄이고(fixture/memory 관련 워크로드 삭제), 노트북 통합 테스트 방식을 업데이트하는 것을 목표로 합니다.

**최종 결정: Approved (제한적 승인)**

- 계획된 Core Scope 축소(불필요한 코드 제거 및 API 정리)가 계약(Contract)을 충족하며 성공적으로 적용되었습니다.
- 단, 통합 테스트의 검증력 상실(False Green)과 메모리 보호망 상실 위험 등 중요한 문제점들이 식별되었습니다. 이 변경 사항 자체는 `tasks.md`의 구현을 완수했으므로 병합을 승인하되, 식별된 결함은 반드시 후속 작업이나 리팩토링으로 해결되어야 합니다.

---

## 1. Quality Review Findings (Correctness & Regression)

### 1.1. 안전한 코드 제거 및 API 정리

- `analysis.py`에서 `anomalies`, `freshness`, `schema_hash`, 고유값이 큰 `county_code` 분포 계산이 의도대로 제거되었습니다.
- 불필요한 fixture 및 memory 관련 구현체(`fixture.py`, `memory.py`, `scripts/*`)가 제거되었습니다.
- `__init__.py`에서의 export가 차단되어 의도하지 않은 API 노출 회귀(Regression)가 발생하지 않음이 확인되었습니다. (기존 호환성 테스트로 보호됨)

### 1.2. 노트북 통합 테스트 구조 및 의존성 문제 (Maintainability Risk)

- `tests/hmda_data/eda/test_eda_notebook.py` 파일 내에 상대 경로(`Path("notebooks/eda_mo.py")`)가 하드코딩되어 있습니다. 테스트가 repository root가 아닌 다른 곳에서 실행될 경우 경로를 찾지 못할 수 있습니다.
- `os`, `shutil` 등의 모듈 import가 함수 내부에 위치하여 가독성을 떨어뜨리고 PEP-8 가이드에 어긋납니다.
- **조치 권고**: 테스트 파일의 위치를 기준으로 절대 경로를 동적으로 계산하도록 수정하고, 지역 import를 최상단으로 옮겨야 합니다.

---

## 2. Adversarial Review Findings (Risks & Failure Paths)

### 2.1. 노트북 통합 테스트의 거짓 통과 (False Green)

- **발견 사항**: `test_valid_fixture_completes_notebook_rendering`에서 출력된 HTML에 `"evidence" in content` 문자열이 포함되어 있는지 검사합니다.
- **위험**: Marimo가 HTML을 내보낼 때 노트북의 소스 코드를 내부에 임베드하기 때문에, 실제 렌더링이나 분석 성공 여부와 관계없이 소스 코드 자체의 `"evidence"`라는 단어로 인해 무조건 참(True)으로 평가될 수 있습니다.
- **조치 권고**: 단순 문자열 매칭 대신 구조화된 결과물 검증(JSON 결과 파싱 등) 또는 Marimo 실행 시 오류가 없음을 구체적으로 증명하는 방향으로 테스트 검증 방식을 변경해야 합니다.

### 2.2. 도달 불가능한 데이터 소스 분기 (Dead Code)

- **발견 사항**: `notebooks/eda_mo.py`에서 `data_is_sample = True`가 상수로 하드코딩되어 있습니다.
- **위험**: 실제 원본 데이터(Raw 데이터) 경로로 분기하는 `else` 구문은 영원히 도달할 수 없습니다. UI와 바인딩되지 않아 샘플 데이터 이외의 실행이 제한됩니다.
- **조치 권고**: UI 위젯(예: `mo.ui.checkbox`)과 연결하여 동적으로 스위칭할 수 있도록 노트북을 업데이트해야 합니다.

### 2.3. 메모리 제약 자동화 보호망 상실 (High-Impact Risk)

- **발견 사항**: `test_eda_memory.py`와 `run_hmda_eda_memory.py`가 제거됨에 따라 대용량 데이터(수백만 건 이상)를 처리할 때 메모리 한도를 초과하는지 확인하는 자동화 테스트가 완전히 사라졌습니다.
- **위험**: 향후 메모리를 많이 사용하는 쿼리(`fetchall()` 등)나 잘못된 `GROUP BY`가 추가될 경우 CI에서는 통과하지만 실제 운영 시 OOM(Out of Memory)이 발생할 수 있습니다.
- **조치 권고**: 이번 Scope 축소의 결정 사항이므로 당장의 수정 대상은 아니나, 향후 운영 안정성(Reliability)을 위해 DuckDB 스트리밍 쿼리 단위 테스트 추가 등 대안적인 안전망(Safeguard) 구축을 고려해야 합니다.

---

## 3. Summary & Next Steps

변경 사항은 "HMDA EDA Core Scope Reduction" 이라는 목적과 작업을 정확하게 이행했습니다. 불필요한 기능이 완전히 삭제되었고 의도한 방향으로 아키텍처가 단순화되었습니다.

따라서 리뷰는 **Approved** 상태로 마무리합니다. 다만, 노트북 테스트의 False Positive 문제(2.1)와 하드코딩된 Dead Code(2.2)는 다음 변경(Follow-up Change)에서 반드시 개선해야 하는 핵심 과제로 남깁니다.
