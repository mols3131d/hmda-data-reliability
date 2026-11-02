---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Extract Review AI Prompt Resources
description: 지시문 분리와 import, digest 및 배포 리소스 호환성을 검증합니다.
tasks_completed: 1
tasks_total: 1
---

## Tasks

- [x] 프롬프트를 텍스트 리소스로 분리하고 기존 렌더링 동작을 보존한다.
  - **Done when:** 세 버전의 변경 전 golden digest, Review AI/Runtime AI 테스트와 정적 검사가 통과한다. 빌드된 wheel에서 세 텍스트 리소스와 기존 import 경로를 확인하고 현재 문서 링크를 새 경로로 맞춘다.
