---
title: "데이터 플랫폼 핵심 구간 구성"
description: "NYC Taxi 데이터를 적재하고 Iceberg table과 metadata 조회 경로를 준비한다."
tags:
    - "data-platform"
    - "ingestion"
    - "iceberg"
class: backlog
---

## Context

MVP는 데이터 품질 incident를 evidence 기반으로 설명해야 한다. 이를 위해 먼저 원천 데이터를 로컬에 적재하고, 핵심 table의 snapshot, schema, partition metadata를 조회할 수 있는 기반이 필요하다.

## Goal

NYC Taxi 샘플 데이터와 lookup 데이터를 raw Parquet로 저장하고, `fct_taxi_trips_iceberg` table을 생성한다. 이후 RCA evidence로 사용할 snapshot id, schema, partition metadata, partition별 row count를 조회할 수 있게 한다.

## Non-Goal

- 전체 lakehouse를 Iceberg로 전환하지 않는다.
- dbt model, Dagster asset, Agent workflow는 포함하지 않는다.
- 대규모 데이터 처리 성능 검증은 포함하지 않는다.

## Scope

- NYC Taxi Trip Records 샘플 적재
- Taxi Zone Lookup 적재
- raw Parquet 저장
- Iceberg local catalog 구성
- `fct_taxi_trips_iceberg` 생성
- snapshot metadata 조회 함수 작성
- schema metadata 조회 함수 작성
- partition metadata 조회 함수 작성
- partition별 row count metadata 추출
- 같은 partition 재실행 시 중복 적재 방지

## Todo

- [ ] NYC Taxi Trip Records 샘플 적재 경로를 정의한다.
- [ ] Taxi Zone Lookup 적재 경로를 정의한다.
- [ ] raw Parquet 저장 로직을 작성한다.
- [ ] Iceberg local catalog를 구성한다.
- [ ] `fct_taxi_trips_iceberg` 생성 로직을 작성한다.
- [ ] snapshot id 조회 함수를 작성한다.
- [ ] schema metadata 조회 함수를 작성한다.
- [ ] partition metadata 조회 함수를 작성한다.
- [ ] partition별 row count metadata 추출 로직을 작성한다.
- [ ] 같은 partition 재실행 시 중복 적재가 없는지 검증한다.

## Acceptance Criteria

- raw Parquet query가 가능하다.
- `fct_taxi_trips_iceberg` table이 생성된다.
- snapshot id, schema, partition metadata를 읽을 수 있다.
- partition별 row count metadata를 추출할 수 있다.
- 같은 partition을 재실행해도 중복 데이터가 생기지 않는다.
