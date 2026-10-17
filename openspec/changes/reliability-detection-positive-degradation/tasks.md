---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Positive Degradation Detection
description: Volume/null의 실제 양의 악화 조건과 기존 독립 규칙을 회귀 테스트 및 현재 명세와 일치시킵니다.
tasks_completed: 1
tasks_total: 1
---

## Tasks

- [x] Volume/null의 양의 악화 경계를 구현하고 독립 탐지 규칙 및 현재 명세를 일치시킨다.
  - **Covers:** Rule-based profile comparison, Volume drop detection, Null spike detection.
  - **Test first:** Zero threshold의 무변화·한 규칙만 악화·독립 schema/freshness 사례에서 정확한 incident 목록을 검사해 수정 전 observable assertion 실패를 확인한다.
  - **Done when:** 고정 입력의 무변화·개선·양의 악화·양수 equality·zero-row baseline·독립 schema/freshness 회귀가 통과하고, 기존 quality gate 계약을 유지하며 구현된 계약이 canonical Spec과 설명에 반영된다.
