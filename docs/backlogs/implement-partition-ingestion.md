---
title: "Ingestion 파티션 적재 구현"
description: "daily partition overwrite 기반의 idempotent(멱등성 있는) ingestion 기능을 구현합니다."
tags:
    - "ingestion"
    - "idempotency"
class: "backlog"
---

# Ingestion 파티션 적재 구현

## Context

- 원천 데이터에서 daily 파티션을 추출하여 적재할 때, 중복 적재가 없도록 멱등(Idempotent)하게 데이터를 관리해야 합니다.

## Goal

- `daily partition overwrite` 방식을 보장하는 로컬 적재 모듈을 완성합니다.

## Non-Goal

- dbt 모델 내에서의 복잡한 incremental 빌드 로직 (dbt 파운데이션 단계에서 진행)

## Scope

- 파티션 오버라이트(Overwrite) 적재 쿼리 및 파이썬 로더 구현
- 동일 파티션을 재적재했을 때 데이터 유실 및 중복이 없음을 확인하는 멱등성 검증

## Todo

- [ ] daily 파티션 단위 덮어쓰기(Overwrite) 적재 함수 구현
- [ ] 동일 데이터 재적재 시 중복 유무 확인용 테스트 작성

## Acceptance Criteria

- 동일한 일자의 파티션을 여러 번 적재하더라도 최종 테이블의 행 수 및 내용이 일정하게 유지되어야 합니다.
