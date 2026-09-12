---
type: review
title: "Review: Domain 1-3 Code Comprehension Refactor and Clarification"
description: "Domain 1(data_platform), Domain 2(hmda_data), Domain 3(orchestration)에 적용된 코드 이해 비용 리팩터링 및 불변식 설명 보강에 대한 품질 및 적대적 통합 리뷰"
tags:
  - review
  - comprehension
  - quality
  - adversarial
  - data-platform
  - hmda-data
  - orchestration
---

# Review: Domain 1-3 Code Comprehension Refactor and Clarification

## Executive Summary

Domain 1 (`data_platform`), Domain 2 (`hmda_data`), Domain 3 (`orchestration`)을 대상으로 진행된 `mols-clarify-code`, `mols-clarify-runtime`, `mols-code-comprehension-refactor` 작업에 대해 품질(Quality) 및 적대적(Adversarial) 관점의 통합 리뷰를 수행했다.

모든 변경은 **외부 관찰 가능한 기능, 입출력, 에러 시맨틱스 및 DB 스키마를 100% 보존**하면서 복잡한 익명 튜플 언패킹, 동적 리플렉션 간접성, 거대한 중첩 제어 흐름을 도메인 명명 구조(`NamedTuple`)와 단계별 함수로 분리하여 코드 이해 비용을 대폭 절감했다.

관련 단위/컴포넌트 테스트 **119개 전체가 무회귀(Zero Regression)로 통과**되었으며, Ruff 린트 및 포맷 검증도 완비되었다.

---

## Review Scope & Inspected Changes

| Domain | Files Changed | Main Interventions | Skill |
| --- | --- | --- | --- |
| **Domain 1**<br/>(`data_platform`) | `src/hmda_reliability/data_platform/sql.py`<br/>`src/hmda_reliability/data_platform/artifacts.py`<br/>`src/hmda_reliability/data_platform/duckdb.py`<br/>`tests/data_platform/test_duckdb.py` | - SQL 쿼팅 전제조건 및 NUL 거부 계약 문서화<br/>- 길이 프리픽스 기반 해시 다이제스트 및 락 정책 명시<br/>- DB 뮤테이션 락 캐노니컬화 및 커넥션 수명주기 명시<br/>- `test_duckdb.py`의 런타임 리플렉션 간접성 제거 및 정적 임포트 전환 | `mols-clarify-code`<br/>`mols-code-comprehension-refactor` |
| **Domain 2**<br/>(`hmda_data`) | `src/hmda_reliability/hmda_data/eda/analysis.py`<br/>`src/hmda_reliability/hmda_data/ingestion/partition.py`<br/>`src/hmda_reliability/hmda_data/synthetic/cases.py` | - `_ValidatedSchema`, `_VolumeAndNullMetrics` 명명 튜플 도입으로 익명 4-튜플 해소<br/>- `_SourceFileClause` 도입으로 쿼리 필터 튜플 명확화<br/>- `_validate_target_year_and_case_name` 분리로 40라인 검증 중첩 완화<br/>- `_TargetCounts` 도입 및 6개 SQL 플레이스홀더 파라미터 매핑 순서 주석 명시 | `mols-code-comprehension-refactor`<br/>`mols-clarify-code` |
| **Domain 3**<br/>(`orchestration`) | `src/hmda_reliability/orchestration/config.py`<br/>`src/hmda_reliability/orchestration/dags/hmda_data_plane.py` | - 런타임 오버라이드 우선순위 및 모델 결합 규칙 명시<br/>- Airflow 태스크 의존성 흐름 및 품질 게이트 차단 경계 명문화 | `mols-clarify-code` |

---

## Quality Assessment (품질 평가)

### 1. Intended Behavior & Contract Preservation

- **익명 튜플 해소 (`NamedTuple`)**: `analysis.py`의 `_ValidatedSchema`, `_VolumeAndNullMetrics` 및 `cases.py`의 `_TargetCounts`, `partition.py`의 `_SourceFileClause`는 모두 `NamedTuple`로 정의되어 기존 튜플의 인덱스 기반 접근(`row[0]`, `row[1]`)과 필드명 접근(`.total_count`, `.non_null_count`)을 모두 완벽히 호환한다. 외부 호출자 계약을 전혀 손상시키지 않는다.
- **파라미터 및 인자 검증 로직 보존**: `cases.py`에서 분리된 `_validate_target_year_and_case_name`은 기존의 `isinstance`, 연도 범위(`2000 <= target_year <= 2100`), 정규식 매칭, 에러 타입(`SyntheticCaseError`) 및 `context` 딕셔너리 페이로드를 100% 동일하게 유지한다.
- **테스트 가독성 향상**: `tests/data_platform/test_duckdb.py`에서 `getattr` 기반 동적 리플렉션을 제거하고 정적 임포트를 사용함으로써 테스트가 검증하려는 실제 락 동작과 예외 클래스 계약을 코드상에서 직접 파악할 수 있게 개선되었다.

---

## Adversarial Assessment (적대적/안전성 평가)

### 1. Reachable Failure Paths & Side Effects

- **락 순서 및 예외 전파**: `data_platform/duckdb.py`의 `database_mutation_lock` 및 `artifacts.py`의 `artifact_projection_lock`의 주석 보강 시 본문 블록 예외 우선 보존 정책을 명시하였으며, 기존 코드의 `body_failed` 플래그 및 `try...finally` 구조를 전혀 건드리지 않아 동시성/예외 전파 경로가 온전히 유지됨을 확인했다.
- **SQL Injection 방지 및 바인딩 불변식**: `synthetic/cases.py`의 SQL 쿼리 매핑 주석 추가 시, 파라미터 리스트의 순서나 인자 구성을 변경하지 않고 플레이스홀더 순서에 대한 설명을 정확히 일치시켰다.

### 2. Isolated Out-of-Scope Issues

전수 조사 중 발견된 아래 2건의 중요 위험 요인은 본 리팩터링에서 임의로 수정하지 않고 [inbox/2026-09-12-refactor-code-comprehension-clarification/01-note-out-of-scope-issues.md](01-note-out-of-scope-issues.md)에 안전하게 격리 기록되었다.

1. `ISSUES-data_platform-01`: `artifact_projection_lock`이 shared reader 락(`exclusive=False`)임에도 `"w"` 쓰기 모드로 락 파일을 열어 읽기 전용 환경에서 `PermissionError`를 유발할 수 있는 안전성 위험
1. `ISSUES-data_platform-02`: `artifact_projection_id`의 핵심 불변식을 검증하는 직접적인 단위 테스트가 `test_artifacts.py`에 누락된 테스트 부채

---

## Validation Evidence

- **Pytest Suite Result**:
  - `uv run pytest tests/data_platform tests/hmda_data tests/orchestration`
  - **119 passed in 105.27s** (Domain 1: 17개, Domain 2: 76개, Domain 3: 26개)
  - 결함, false green, 또는 기존 단언문 완화 없음.
- **Lint & Format Validation**:
  - `uv run ruff check` 및 `uv run ruff format --check` 43개 파일 검사 완료, **All checks passed!**

---

## Final Disposition

- **Verdict**: **APPROVED (Clear)**
- **Disposition**: Domain 1~3의 코드 이해 리팩터링 및 불변식 설명 보강 작업은 완전하게 완료되었으며, 다른 세션에서 진행 중인 Domain 4~8 작업과의 충돌 요인이 배제되어 안전하게 병합 준비가 완료되었다.
