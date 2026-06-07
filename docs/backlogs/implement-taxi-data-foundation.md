---
title: "NYC Taxi 데이터 파운데이션 구축"
description: "DuckDB 기반 NYC Taxi 데이터를 적재하고 인시던트 탐지 검증을 위한 합성 이상치 데이터를 주입합니다."
tags:
    - "data-foundation"
    - "duckdb"
    - "synthetic-data"
class: "backlog"
---

# NYC Taxi 데이터 파운데이션 구축

## Context

- 1단계(Reliability Contracts) 정의 완료.
- Detector + LangGraph 로컬 검증 위해 실제 물리 데이터(Parquet, CSV) 기반 DuckDB 데이터셋 필요.

## Goal

- 로컬 DuckDB 일자별 NYC Taxi 데이터 적재.
- 검증용 5가지 합성 이상치(Synthetic Incident Cases) 준비.

## Non-Goal

- Iceberg 테이블 메타데이터 실시간 동기화 (다음 단계).
- Dagster 파이프라인 자동 조율 (3단계).

## Scope

- 로컬 `data/raw/tlc` 원본 DuckDB 로드 모듈.
- 5가지 파티션 생성:
  - `normal`: 정상.
  - `row_count_drop`: 행 유실.
  - `null_spike`: Null 급증.
  - `schema_drift`: 스키마 변형.
  - `freshness_delay`: SLA 지연.

## Todo

- [ ] DuckDB 연결 + 스키마 정의 모듈 작성.
- [ ] Parquet/CSV ➔ DuckDB 로드 Ingestion 구현.
- [ ] 정상 + 이상 케이스 디스크 파티션 파일 변형/저장 유틸 작성.
- [ ] 5가지 파티션 개별 쿼리 검증 단위 테스트 작성.

## Acceptance Criteria

- 로컬 DuckDB 각 파티션 정상 쿼리.
- 각 파티션 의도된 결함(행 감소, Null 급증, 스키마 변형 등) 포함 여부 검증 완료.
