---
title: "프로파일 스냅샷 생성 구현"
description: "파티션별 row count, null rate, schema hash, freshness 품질 지표를 계산해 저장합니다."
tags:
    - "profiling"
    - "quality"
class: "backlog"
---

# 프로파일 스냅샷 생성 구현

## Context

- 데이터 품질 저하를 수치로 감지하기 위해, 파티션별로 주요 데이터 프로파일 지표를 계산하고 스냅샷 형태로 기록해야 합니다.

## Goal

- 파티션별 `ProfileSnapshot` 에비던스를 계산하여 정형 데이터 형태로 저장합니다.

## Non-Goal

- 시각화용 대시보드 연동 및 차트 구성

## Scope

- row count, null rate, schema hash, freshness 시간 계산 로직
- `ProfileSnapshot` 규약과의 데이터 직렬화 호환성 보장

## Todo

- [ ] Custom Profiler 모듈 작성
- [ ] 수집된 지표를 `ProfileSnapshot` 모델로 포매팅 및 저장하는 로직 작성

## Acceptance Criteria

- 특정 파티션에 대해 프로파일러를 구동하면 `ProfileSnapshot` 계약에 적합한 JSON 형태의 지표 세트가 생성되어야 합니다.
