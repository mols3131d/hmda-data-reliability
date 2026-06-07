---
title: "조치 제안 초안 생성"
description: "RCA 분석과 테스트 보강, 백필 및 검증 액션이 담긴 조치 제안(Remediation Draft)을 구성합니다."
tags:
    - "remediation"
    - "agent"
class: "backlog"
---

# 조치 제안 초안 생성

## Context

- 감지된 품질 문제에 대해 근본 원인(RCA)을 분석하고, 이를 수정하기 위한 테스트 보강 방안 및 데이터 재처리(Backfill) 액션 리스트를 자동으로 구성해야 합니다.

## Goal

- LangGraph 에이전트를 통해 `recommended_actions`가 명확히 명시된 조치 제안 초안을 생성합니다.

## Non-Goal

- 사람의 승인 단계 없이 자동으로 즉시 백필을 실행하는 행위

## Scope

- LangGraph 기반 에이전트 RCA 분석 플로우
- 백필 실행에 필요한 구체적 매개변수(파티션 ID, 대상 자산 등) 추출 로직
- 조치 제안 Pydantic 스키마 검증

## Todo

- [ ] 에비던스 데이터를 해석하여 원인을 진단하는 LangGraph 에이전트 워크플로우 구현
- [ ] 에이전트 분석 결과를 기반으로 해결 방안(Remediation)을 구조화된 출력(Pydantic)으로 추출하는 유틸 구현

## Acceptance Criteria

- 생성된 조치 제안서의 `recommended_actions`에 이상 유형에 대처하는 작업(예: `prepare_partition_backfill`, `validate_source_partition` 등)이 올바르게 포함되어 있어야 합니다.
