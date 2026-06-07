---
title: "영향 범위 분석 구현"
description: "dbt lineage(manifest.json) 정보를 분석하여 인시던트의 다운스트림 영향 자산을 계산합니다."
tags:
    - "impact-analysis"
    - "lineage"
class: "backlog"
---

# 영향 범위 분석 구현

## Context

- 데이터 품질 장애가 발생했을 때 영향 범위를 파악하여 어떤 대시보드나 리포트가 오염되었는지 downstream을 추적할 수 있어야 합니다.

## Goal

- 인시던트 발생 자산을 기준으로 dbt 리니지를 탐색하여 `LineageEvidence`를 자동 생성하고 affected assets를 계산합니다.

## Non-Goal

- dbt 외부(예: BI 대시보드 내부 필드 수준 등)의 fine-grained lineage 추적

## Scope

- dbt `manifest.json` 파서 및 downstream 탐색 알고리즘
- 인시던트 객체의 `affected_assets` 필드 자동 업데이트 로직

## Todo

- [ ] `manifest.json` 파싱 및 특정 모델의 후속 노드(downstream) 목록 추출 유틸 구현
- [ ] 추출 결과를 `LineageEvidence`로 매핑하고 인시던트 정보에 반영하는 모듈 구현

## Acceptance Criteria

- 테스트 구동 시, 특정 마트 테이블의 오류에 영향받는 다운스트림 모델 목록이 인시던트의 `affected_assets`에 누락 없이 채워져야 합니다.
