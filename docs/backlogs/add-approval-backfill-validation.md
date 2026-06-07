---
title: "승인 기반 백필 및 검증 구현"
description: "Human Approval 승인 게이트 통과 후 파티션 재처리(Backfill) 및 검증을 안전하게 실행합니다."
tags:
    - "approval"
    - "backfill"
class: "backlog"
---

# 승인 기반 백필 및 검증 구현

## Context

- 데이터 플랫폼의 오염 방지를 위해, 에이전트가 제안한 데이터 재처리(Backfill) 작업은 승인 장벽(Human Gate)을 통과한 뒤에만 작동해야 합니다.

## Goal

- `human_review_status = approved` 검증 및 승인 후 백필 동작 및 검증 파이프라인의 안전한 구동.

## Non-Goal

- 프로덕션 배포 수준의 분산 백필 및 분산 워크플로우 구성

## Scope

- 승인 상태(`ApprovalStatus.APPROVED`) 확인용 안전 인터페이스
- 백필 실행 모듈(Dagster 연동 준비 단계) 및 데이터 덮어쓰기 로직
- 재처리 완료 후 프로파일러 기반 데이터 재검증(SLA 및 품질 보장)

## Todo

- [ ] 승인 상태 판별 로직 및 백필 태스크 연계
- [ ] 덮어쓰기 적용 후 데이터 퀄리티를 다시 체크하는 사후 검증(Validation) 함수 구현

## Acceptance Criteria

- `ApprovalStatus`가 `APPROVED`가 아닌 경우 어떠한 재처리 명령도 실행되지 않고 예외를 발생시켜야 합니다.
- 승인 후 재처리가 수행되면, 최종적으로 갱신된 데이터를 기반으로 `ProfileSnapshot`이 자동 재생성되어야 합니다.
