---
title: "dbt 분석 파운데이션 구현"
description: "dbt staging, mart, test 모델링 및 lineage artifact를 구성합니다."
tags:
    - "dbt"
    - "lineage"
class: "backlog"
---

# dbt 분석 파운데이션 구현

## Context

- 적재 완료된 raw 테이블을 가공하여 실제 지표를 생산하는 mart 레이어를 구성하고, dbt 테스트와 리니지 아티팩트(`manifest.json`)를 연계할 기반이 필요합니다.

## Goal

- `dbt build` 성공 및 downstream 영향도 분석을 위한 리니지 manifest 아티팩트 확보.

## Non-Goal

- dbt 외의 별도 카탈로그 도구(DataHub 등) 연동

## Scope

- staging 및 mart SQL 모델 작성
- dbt test(null check, unique check 등) 적용
- manifest.json 및 run_results.json 생성 확인

## Todo

- [ ] raw_hmda ➔ staging ➔ mart dbt 모델 작성
- [ ] dbt test 및 manifest 아티팩트 생성 자동화 스크립트 작성

## Acceptance Criteria

- `dbt build` 명령이 오류 없이 성공해야 합니다.
- target 디렉터리에 `manifest.json`과 `run_results.json`이 정상 발행되어야 합니다.
