---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Format Review AI Prompts as Markdown
description: Markdown 프롬프트 리소스와 관련 계약·로더·회귀 검증을 맞춥니다.
tasks_completed: 1
tasks_total: 1
---

## Tasks

- [x] 버전별 Markdown 프롬프트와 로딩·작성 계약을 일치시킨다.
  - **Test first:** `.md` 리소스가 실제 system 메시지와 같아야 하는 테스트가 기존 `.txt` 구현에서 실패하는지 확인한다.
  - **Done when:** 세 프롬프트가 한국어 제목·목록·코드 표기로 읽기 쉽게 구분되고 기존 JSON 응답·검토 경계를 유지한다. 관련 테스트, Markdown·타입·OpenSpec 검사와 wheel/sdist 리소스 로딩이 통과하며 현재 문서 링크와 digest가 갱신된다.

## Validation

- Markdown 리소스 전달 테스트의 변경 전 실패 3개와 변경 후 통과를 확인했다.
- Review AI/Runtime AI offline suite: 291 passed, 1 skipped.
- Ruff, format, ty, Markdown, Inbox 형식과 editor diagnostics 검사를 통과했다.
- wheel/sdist에서 세 `.md` 리소스의 바이트와 `.txt` 제거를 확인했다. Checkout 밖에서 wheel을 import해 세 version의 현재 golden digest를 대조했다.
