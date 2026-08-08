---
type: openspec-spec-driven-tdd-design
category: design
title: "Reconcile HMDA EDA core contract"
description: "Align runtime evidence, Python/YAML exploration, static visualizations, and controlled observation around the six-core EDA contract."
tags:
  - "domain:hmda-data"
  - "subdomain:eda"
  - "capability:hmda-eda-baseline"
  - "contract-reconciliation"
---

> [!NOTE]
> EDA runtime은 6-core descriptive contract만 계산하고, Python 기반 탐색 결과를 에이전트 친화적인 YAML(`yml`) 에비던스로 직렬화한다. 필요 시 정적 이미지(PNG) 또는 HTML 차트를 내보내며, Marimo 노트북은 제거한다. Actual-source evidence는 동일한 run의 JSON을 source로 Markdown summary를 만들어 값의 분기를 제거한다.

## Context

- **Current State:** runtime은 `county_code`를 EDA required column으로 포함하고, grain distinct count는 null key를 포함할 수 있으며, duration이 이후 aggregate를 제외한다. 반응형 Marimo UI 노트북은 에이전트 환경에서 무겁고 비효율적이다.
- **Constraints:** ingestion의 7-column source contract를 바꾸지 않고 EDA의 6-core contract만 정렬한다. 대용량 workload 검증과 query 최적화는 범위 밖이다.
- **Dependencies:** DuckDB aggregate entrypoint, PyYAML (또는 stdlib/ruamel) 직렬화, Altair/Plotly 정적 내보내기, actual-source CSV와 Foundation readiness artifact.

## Goals / Non-Goals

| Goals | Non-Goals |
| --- | --- |
| 6-core runtime evidence, complete-key grain, end-to-end duration 검증 | ingestion required column 제거 또는 source schema 변경 |
| 에이전트 친화적 Python API 및 YAML(`yml`) 에비던스 반환, 정적 시각화(PNG/HTML) 내보내기 | 지속적 성능 관찰, OOM budget, query materialization 최적화 |
| Marimo 반응형 노트북(`eda_mo.py`) 완전 제거 | Marimo UI 라이프사이클 유지 |

## Architecture

`analyze_hmda_csv`는 validation을 통과한 뒤 volume, distribution, numeric summary, complete-key grain을 계산하고 마지막에 duration을 측정한다. 일반 Python helper/CLI 모듈이 결과를 YAML 형식으로 직렬화하고, 시각화 요청 시 정적 PNG 차트 또는 독립 HTML 파일로 내보낸다. Actual-source script는 동일 evidence object에서 portable JSON과 Markdown summary를 생성한다.

## Components

| Component | Responsibility | Change |
| --- | --- | --- |
| EDA runtime | 6-core descriptive evidence와 complete-key grain 계산 | `county_code` EDA metric 제외, freshness query 제거, duration 범위 확장 |
| Component tests | 6-core input, null-key grain, duration 의미 보호 | 작은 deterministic CSV regression 추가 |
| Python/YAML Explorer | EDA 결과를 YAML(`yml`) 형식으로 반환 및 CLI 내보내기 | 에이전트 환경에 최적화된 YAML 직렬화 제공 |
| Static Visualizer | EDA 분포/통계 정적 차트(PNG/HTML) 생성 | Altair/Plotly/Vega 기반 정적 이미지 또는 HTML 인라인 차트 내보내기 |
| Marimo Notebook Removal | 복잡한 UI 노트북 및 관련 테스트 제거 | `notebooks/eda_mo.py` 및 `test_eda_notebook.py` 삭제 |
| Evidence generator | one run의 evidence에서 portable JSON·Markdown 생성 | source fingerprint, revision, timestamp와 invariant 검증 |
| Readiness | evidence 상태를 정확히 표현 | evidence 재생성 전 EDA gates blocked 유지 |

### Boundaries

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| HMDA ingestion | 7-column source required-column validation | EDA descriptive metric scope |
| EDA | 6-core schema/null/distribution/numeric/grain observation | canonical mart grain 변경, freshness, anomaly, resource budget |
| Python/YAML Explorer | EDA result YAML formatting & static image/HTML export | 별도 EDA calculation, UI server hosting |
| Actual-source evidence | one-time read-only observation artifact | production performance guarantee |

## Decisions

### D1. Six-core EDA contract follows scope-reduction spec

- **Decision** - `activity_year`, `state_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`만 EDA validation과 null baseline에 둔다.
- **Rationale** - `county_code`는 ingestion source contract의 필수 field이나 scope-reduction spec의 EDA type·metric 대상은 아니다.
- **Trade-off** - county-level completeness 관찰은 이 EDA surface에서 제공하지 않는다.

### D2. Grain aggregation explicitly filters incomplete keys

- **Decision** - distinct group count의 population을 complete-key rows로 제한하고 null-key rows를 별도 반환한다.
- **Rationale** - group cardinality와 coverage rate의 분모·분자를 같은 key semantics로 유지한다.
- **Trade-off** - incomplete key의 조합은 group count에 나타나지 않으며 quality signal로만 제공된다.

### D3. Evidence has one structured source

- **Decision** - actual-source script가 portable JSON을 만든 뒤 그 object에서 Markdown summary를 렌더링한다.
- **Rationale** - hand-maintained values가 갈라지는 것을 차단한다.
- **Trade-off** - observed actual-source run 없이는 readiness를 passing으로 표시하지 않는다.

### D4. Agent-first YAML serialization & Static Chart Exports instead of Marimo Notebook

- **Decision** - Marimo 노트북(`eda_mo.py`)을 완전히 제거하고, Python API/CLI 기반으로 YAML(`yml`) 에비던스와 정적 시각화 파일(PNG/HTML)을 생성한다.
- **Rationale** - LLM 에이전트와 CLI 환경에서는 반응형 UI 노트북을 실행·파싱하는 것보다 텍스트 기반 구조화 데이터(YAML)와 정적 렌더링 파일(PNG/HTML)을 다루는 편이 훨씬 직관적이고 경량화된다.
- **Trade-off** - 인터랙티브 웹 UI를 통한 실시간 체크박스/테이블 탐색 기능은 제공되지 않는다.

## Testability

| Boundary / Behavior | Test Strategy | Evidence |
| --- | --- | --- |
| Six-core validation | Component test | `county_code` 없는 valid CSV 성공 및 missing core column failure |
| Complete-key grain | Component test | null-key rows는 group count에서 제외되고 coverage가 일치 |
| Duration scope | Component test with patched monotonic clock | all retained aggregate calls 뒤의 elapsed value |
| YAML & Static Viz Export | Component / Unit test | YAML 직렬화 파싱 성공 및 PNG/HTML 시각화 파일 정상 생성 |
| Evidence consistency | Script/unit-style test or generated artifact invariant | Markdown metrics가 JSON metrics와 일치 |

- **TDD Boundary:** 6-core-only CSV와 null grain keys를 기존 runtime이 실패하거나 잘못 계산하는 regression으로 먼저 고정하고, Marimo 제거 및 YAML/PNG 정적 시각화 함수 생성을 TDD로 진행한다.
- **Failure Signals:** `county_code` validation failure, null-key group 포함, stale freshness field, YAML 직렬화 오류, 시각화 파일 생성 실패, JSON/Markdown metric mismatch.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Actual source를 현 환경에서 재실행하지 못함 | evidence numeric values를 확정할 수 없음 | portable generator를 구현하고 readiness를 blocked로 유지 |
| Plotly/Altair 정적 이미지 내보내기 시 시스템 헤드리스 의존성(vl-convert / chrome 등) 이슈 | 시각화 이미지 생성 실패 | HTML 차트 생성을 기본 보장하고 PNG 선택 생성 지원 |
| Multiple CSV scans | large source response time이 길 수 있음 | 전체 duration을 정확히 기록하고 optimization은 별도 change로 보류 |
