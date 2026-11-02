---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Localize Review AI Prompts
description: 한국어 프롬프트 작성 계약과 지원 버전의 한국어 지시문을 구현하고 검증합니다.
tasks_completed: 2
tasks_total: 2
---

## Tasks

- [x] 버전별 프롬프트와 설명문 출력을 한국어로 지시한다.
  - **Test first:** 모든 버전의 한국어 지시문 및 네 설명 필드의 출력 언어 지침이 없는 현재 상태에서 회귀 테스트가 실패하는지 확인한다.
  - **Done when:** v1/v2/v3 지시문·v2 예시와 자체 생성하는 context gap·빈 요약 대체 문구가 한국어이며 JSON 필드·열거값·식별자·수치와 기존 version 기본값은 보존된다. 한국어 설명과 영어 설명 모두 기존 구조 검증 경계를 사용하고 한국어 리소스의 golden digest가 고정된다.
- [x] 프롬프트 작성 Spec과 historical replay 계약을 정본·Change·가이드에 일치시킨다.
  - **Done when:** 전용 Spec이 리소스·한국어·변경 추적을 소유하고 과거 revision의 replay와 실제 모델 준수 평가를 구분한다. Review AI/Runtime AI 테스트, 정적 검사, 리소스 패키징 및 OpenSpec 검증을 완료한다.

## Validation

- Review AI/Runtime AI suite: 285 passed, 1 skipped. 한국어 요구의 변경 전 실패와 변경 후 통과를 확인했다.
- Ruff, format, ty 및 한국어 리소스의 wheel/sdist 포함·checkout 밖 로딩을 확인했다.
- 로컬 합성 live 실행 `ar-20261028-4fa304794462`: v3, `project_revision=local-korean-prompt-worktree`, `accepted`. 보존된 응답의 네 종류 설명 필드가 한국어임을 읽어 확인했다. Clean commit의 live proof 또는 human utility 평가로 취급하지 않는다.
- 호출 기록과 원문은 로컬 artifact root의 `agentic-review/invocations/ar-20261028-4fa304794462.json`, `agentic-review/responses/ar-20261028-4fa304794462.txt`에 있다. 재시도와 외부 projection은 사용하지 않았다.
