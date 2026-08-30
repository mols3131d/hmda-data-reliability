---
type: research
title: Code Comprehension Refactoring Candidates Research
description: mols-code-comprehension-refactor 기준에 따른 소스 코드 이해도 개선 후보군 전수 조사 및 우선순위 분석 보고서.
status: completed
tags:
  - refactor
  - code-comprehension
  - source
  - quality
---

# Code Comprehension Refactoring Candidates Research

> [!NOTE]
> **핵심 결론:** `src/hmda_reliability` 전역을 대상으로 독자의 정신적 시뮬레이션(Mental Simulation) 및 해독 비용을 줄일 수 있는 고신호 리팩터링 후보를 조사했습니다. **[src/hmda_reliability/review_ai/service.py](../../src/hmda_reliability/review_ai/service.py)**(에러 분기별 중복 증적 조립 통합)와 **[src/hmda_reliability/hmda_data/eda/analysis.py](../../src/hmda_reliability/hmda_data/eda/analysis.py)**(다차원 튜플 슬라이싱 해체)가 동작 보존 및 이해도 개선 효과가 가장 높은 **1차 착수 후보**입니다.

## Question

`src/hmda_reliability` 소스 코드 중 `mols-code-comprehension-refactor` 스킬의 기준(불투명한 표현, 복잡한 상태/순서 추적, 책임 혼재, 불필요한 간접화)에 부합하며 외부 동작 계약을 100% 보존하면서 인지 부하를 실질적으로 낮출 수 있는 최적의 후보와 우선순위는 무엇인가?

### Scope

| 구분 | 대상 |
| --- | --- |
| **In Scope** | `src/hmda_reliability/` 내 모든 프로덕션 파이썬 모듈, 관련 단위/컴포넌트 테스트 |
| **Exclusion** | 이미 파일럿 리팩터링이 적용된 [src/hmda_reliability/data_operations/runner.py](../../src/hmda_reliability/data_operations/runner.py), 단순 주석/독스트링 수정만 필요한 모듈, 아키텍처 재설계 영역 |

### Stop Condition

후보 모듈의 병목 현상, 제안 변환, 보존해야 할 계약, 검증 커맨드 및 위험 요소를 근거와 함께 정리하면 조사를 종료한다.

## Findings

### F1. Top Priority Candidates

공개 API 및 도메인 계약을 완벽히 보존하면서 내부 구현 복잡도를 즉시 완화할 수 있는 후보입니다.

#### 1. [src/hmda_reliability/review_ai/service.py](../../src/hmda_reliability/review_ai/service.py) (`review_null_spike`)

- **병목 현상 (Repetitive State Assembly & Duplicated Error Flow):**
  - `ProviderUnavailableError`, `ProviderResponseTooLargeError`, JSON 파싱 실패, 결정론적 가드 검증 실패 등 4개 이상의 에러 경로마다 14개 인자를 전달하는 `_build_record(...)` 및 `_persist_result(...)` 호출이 반복됨.[^review-service]
  - 불변 컨텍스트(`invocation_id`, `review_input`, `rendered`)와 분기별 가변 상태(`status`, `failure_code`, `parsed_output`, 메트릭)가 분리되지 않아 제어 흐름 추적 비용이 큼.
- **제안하는 최소 안전 변환:**
  - 호출 결과 레코드 조립을 캡슐화하는 내부 헬퍼를 도입하여, 불변 공통 컨텍스트를 바인딩하고 분기별 가변 상태만 주입받도록 단일화.
- **보존해야 할 계약:**
  - `review_null_spike`의 반환 모델(`AgenticReviewResult`), 모든 상태 코드(`INPUT_REJECTED`, `UNAVAILABLE`, `VALIDATION_FAILED`, `ACCEPTED`, `PROVENANCE_FAILED`), 디스크 감사 증적 포맷.
- **집중 검증 커맨드:**

  ```bash
  uv run pytest tests/review_ai/test_service.py -q
  ```

#### 2. [src/hmda_reliability/hmda_data/eda/analysis.py](../../src/hmda_reliability/hmda_data/eda/analysis.py) (`_collect_volume_and_null_metrics`)

- **병목 현상 (Opaque Positional Indexing & Manual Tuple Slicing):**
  - `GROUPING SETS` 단일 쿼리 결과 튜플에서 `metric_offset = 2 if has_activity_year else 0`과 같은 매직 오프셋 연산을 수행하고 `total_row[metric_offset + 1 : ...]` 형태로 튜플을 슬라이싱함.[^eda-analysis]
  - activity_year 유무에 따른 인덱스 오프셋을 머릿속으로 계산해야 쿼리와 결과 딕셔너리의 매핑을 이해할 수 있음.
- **제안하는 최소 안전 변환:**
  - 단일 DuckDB 쿼리는 그대로 유지하면서, 결과 튜플의 위치 기반 산술을 명시적인 행 파싱 헬퍼나 구조화된 언패킹 모델로 대체.
- **보존해야 할 계약:**
  - `analyze_hmda_csv`가 반환하는 JSON 딕셔너리 구조 전체 및 메모리/단일 쿼리 성능 특성.
- **집중 검증 커맨드:**

  ```bash
  uv run pytest tests/hmda_data/eda/test_eda.py -q
  ```

---

### F2. Conditional Candidates

개선 효과는 분명하지만, 핵심 안전 경계이거나 수학적/쿼리 연산에 극도로 민감하여 보수적으로 접근해야 하는 후보입니다.

#### 3. [src/hmda_reliability/hmda_data/synthetic/cases.py](../../src/hmda_reliability/hmda_data/synthetic/cases.py) (`null_spike`)

- **병목 현상 (Opaque Representation & Hard Math/Query Reasoning):**
  - 다중 계층 문자열 SQL 조합과 플랫 파라미터 리스트(`[*source_params, sample_fraction, null_fraction, ...]`)로 인해 바인딩 관계 추적이 어려움.[^synthetic-cases]
  - Strict Null Rate 증가를 보장하는 정수 나눗셈 식(`least(..., greatest(...))`)이 SQL 내에 압축되어 있음.
- **제안하는 최소 안전 변환:**
  - SQL 쿼리 빌더를 명확한 CTE 단계별 생성 블록으로 정리하고, 핵심 수식의 서브 표현식을 상수로 분리.
- **보존해야 할 계약:**
  - 출력 Parquet 스키마, 행 정렬, $\text{output\_null\_rate} > \text{source\_null\_rate}$ 불변성, `SyntheticCaseError` 발생 조건.
- **집중 검증 커맨드:**

  ```bash
  uv run pytest tests/hmda_data/test_synthetic.py -q
  ```

#### 4. [src/hmda_reliability/reliability/recovery/executor.py](../../src/hmda_reliability/reliability/recovery/executor.py) (`ApprovalBackfillValidator.execute`)

- **병목 현상 (Hard State/Order Reasoning & Mixed Responsibilities):**
  - 승인 검증, 소스 스테이징, 이원화된 상태 조정(컨텐츠 해시 vs 시계열 바인딩), 파티션 교체, 프로파일 검증 실패 후 상태 재구성이 단일 `execute()`에 집중됨.[^recovery-executor]
- **제안하는 최소 안전 변환:**
  - `execute()`를 명확한 선형 단계(`_validate_approval_scope` $\rightarrow$ `_reconcile_target_state` $\rightarrow$ `_execute_backfill_and_verify`)로 평탄화.
- **보존해야 할 계약:**
  - `BackfillValidationResult` 반환 모델, `ApprovalGateError` 및 `BackfillValidationError` 예외 경계, 트랜잭션 롤백 순서.
- **집중 검증 커맨드:**

  ```bash
  uv run pytest tests/reliability/test_approval_backfill_validation.py -q
  ```

---

### F3. Non-Recommended Candidate

- **[src/hmda_reliability/reliability/remediation/workflow.py](../../src/hmda_reliability/reliability/remediation/workflow.py) (`StateGraph`):**
  - 단방향 3단계 노드(`triage` $\rightarrow$ `rca` $\rightarrow$ `plan`)에 LangGraph `StateGraph`를 사용하여 간접화가 있으나, 저장소의 공식 도구 선택([DEVELOPMENT.md](../../DEVELOPMENT.md))이 remediation draft에 LangGraph를 명시하고 있음.[^remediation-workflow]
  - 이를 순수 함수로 바꾸는 것은 코드 이해도 리팩터링의 범위를 넘어 아키텍처/도구 선택 결정을 변경하는 행위이므로 권장하지 않음.

## Candidate Evaluation Matrix

| 후보 모듈 | 인지 부하 원인 | 난이도 | 리팩터링 기대 효과 | 권장 분류 |
| --- | --- | :---: | --- | :---: |
| **[review_ai/service.py](../../src/hmda_reliability/review_ai/service.py)** | 에러 경로별 증적 조립/영속화 중복 | 낮음 | 에러 처리 흐름 가독성 대폭 향상, 공통 컨텍스트 누락 방지 | `🟢 1순위 (즉시 착수)` |
| **[hmda_data/eda/analysis.py](../../src/hmda_reliability/hmda_data/eda/analysis.py)** | 매직 오프셋 기반 튜플 슬라이싱 | 낮음 | DuckDB 쿼리 결과 언패킹 명확화, 인덱스 계산 제거 | `🟢 2순위 (즉시 착수)` |
| **[hmda_data/synthetic/cases.py](../../src/hmda_reliability/hmda_data/synthetic/cases.py)** | 복잡한 SQL 수식 및 파라미터 매핑 | 중간 | 엄격한 결함 합성 수식 의도 전달력 개선 | `🟡 조건부 착수` |
| **[reliability/recovery/executor.py](../../src/hmda_reliability/reliability/recovery/executor.py)** | 복구 단계/상태 조정 제어 흐름 혼재 | 높음 | 핵심 복구 파이프라인의 선형적 가독성 확보 | `🟡 조건부 착수` |
| **[reliability/remediation/workflow.py](../../src/hmda_reliability/reliability/remediation/workflow.py)** | LangGraph 프레임워크 간접화 | 중간 | 저장소 도구 선택 규칙과 충돌하므로 유지 권장 | `🔴 비권장 (규칙 충돌)` |

## Conclusion

`mols-code-comprehension-refactor`의 원칙(One Coherent Bottleneck, Preservation before Transformation, Net Comprehension Gain)에 비추어 볼 때, 가장 안전하고 효과적인 착수 대상은 **[src/hmda_reliability/review_ai/service.py](../../src/hmda_reliability/review_ai/service.py)**입니다.

### Next Step

1. **1단계 파일럿:** [src/hmda_reliability/review_ai/service.py](../../src/hmda_reliability/review_ai/service.py)의 에러 분기 증적 조립 리팩터링 수행 및 `tests/review_ai/test_service.py` 검증.
1. **2단계 파일럿:** [src/hmda_reliability/hmda_data/eda/analysis.py](../../src/hmda_reliability/hmda_data/eda/analysis.py)의 튜플 슬라이싱 구조화 리팩터링 수행 및 `tests/hmda_data/eda/test_eda.py` 검증.

[^review-service]: [src/hmda_reliability/review_ai/service.py](../../src/hmda_reliability/review_ai/service.py#L69-L200)의 `review_null_spike()` 제어 흐름.
[^eda-analysis]: [src/hmda_reliability/hmda_data/eda/analysis.py](../../src/hmda_reliability/hmda_data/eda/analysis.py#L274-L330)의 `_collect_volume_and_null_metrics()`.
[^synthetic-cases]: [src/hmda_reliability/hmda_data/synthetic/cases.py](../../src/hmda_reliability/hmda_data/synthetic/cases.py#L50-L150)의 `null_spike()` 쿼리 및 연산 식.
[^recovery-executor]: [src/hmda_reliability/reliability/recovery/executor.py](../../src/hmda_reliability/reliability/recovery/executor.py#L51-L180)의 `ApprovalBackfillValidator.execute()`.
[^remediation-workflow]: [src/hmda_reliability/reliability/remediation/workflow.py](../../src/hmda_reliability/reliability/remediation/workflow.py#L28-L50)의 LangGraph `StateGraph` 컴파일 흐름.
