---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Retain Provider Responses
description: 응답 원문 보존과 실패 시 경로 제공의 구현·검증 결과를 추적합니다.
tasks_completed: 3
tasks_total: 3
---

## Tasks

- [x] Exact UTF-8 응답 저장소를 구현한다.
  - **Done when:** Test-first로 byte bound, 빈 본문, create-only identity와 기존 invocation 충돌, 원자적 쓰기·권한 및 I/O failure를 검증한다.
- [x] 검증 전 저장과 결과의 response_path를 연결한다.
  - **Done when:** Schema-invalid/guard-failed/accepted의 본문과 경로가 보존되고 저장 실패는 provenance_failed다. 원문은 sanitized record·result 본문·로그·외부 projection에 추가되지 않는다. 실제 SDK fake transport 경로도 검증한다.
- [x] 정본 계약과 실행 가이드를 실제 동작에 맞춘다.
  - **Done when:** 원문 위치·실패 시 읽는 방법·기존 파일 복원 불가와 Runtime 반환 경계를 명시하고 관련 suite와 static/document 검증을 통과한다.
