---
title: "기본 인시던트 탐지 구현"
description: "프로파일 데이터를 기반으로 row count 급감, null spike 등의 품질 이상을 감지하여 인시던트 결과를 생성합니다."
tags:
    - "detection"
    - "incident"
class: "backlog"
---

# 기본 인시던트 탐지 구현

## Context

- 측정된 `ProfileSnapshot` 지표를 baseline 및 이전 이력과 비교하여 임계치를 초과할 때 인시던트(Incident)를 자동으로 발행해야 합니다.

## Goal

- 비정상 데이터 조건 충족 시 `Incident` 및 `Evidence`를 자동 생성하는 탐지 파이프라인 구축.

## Non-Goal

- 머신러닝 기반의 이상 탐지 (우선은 룰 기반 임계치 탐지에 집중)

## Scope

- 볼륨 급감(volume drop), Null 급증(null spike), 스키마 변형(schema drift), SLA 지연(freshness delay) 탐지 로직
- `Incident` 및 `Evidence` 인스턴스 생성 및 연계

## Todo

- [ ] 4대 품질 지표 임계치 규칙 및 Detector 모듈 작성
- [ ] 이상 감지 시 `Evidence`와 `Incident`를 매핑하여 영구 저장소에 기록하는 로직 구현

## Acceptance Criteria

- 합성 결함 파티션(예: row_count_drop)을 탐색 시 의도한 유형의 인시던트가 감지되고, `evidence_refs`가 올바르게 맵핑되어야 합니다.
