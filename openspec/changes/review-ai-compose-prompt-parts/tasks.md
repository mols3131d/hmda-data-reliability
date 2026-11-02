---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Compose Review AI Prompt Parts
description: 공통 조각·결정적 조립과 단일 기본값 전환 방침을 구현하고 검증합니다.
tasks_completed: 3
tasks_total: 3
---

## Tasks

- [x] 전체 프롬프트를 공유 Markdown 조각으로 분리하고 순서대로 조립한다.
  - **Test first:** 각 version의 조각 실재·순서·누락/중복·실제 system 본문을 검증하는 회귀가 기존 전체 파일 구조에서 실패하는지 확인한다.
  - **Done when:** 공통 규칙은 같은 파일을 사용하며 기존 메시지 문자열과 세 golden digest가 그대로다. Input projection, version 기본값, output schema와 validator는 보존된다.
- [x] 채택 후 단일 active 기본값 방침과 조각 작성 계약을 정본·Change·가이드에 일치시킨다.
  - **Done when:** 현재 개발 비교와 향후 채택 전환이 구별되고 진입점별 다른 기본값을 영구 보존하는 문구가 제거된다. 관련 테스트·정적 검사·Markdown·OpenSpec 검증과 배포 패키지의 조각 로딩을 완료한다.
- [x] 모듈의 적용 범위를 경로로 드러내고 재사용·조립·agent 전달 설계를 문서화한다.
  - **Test first:** 작업·정책·예시 경로를 기대하도록 조합 회귀를 바꿔 기존 경로에서 실패함을 확인한다.
  - **Done when:** 역할은 `tasks/`, 정책은 `policies/`, 예시는 `examples/`로 이동하고 기존 세 메시지와 digest가 보존된다. 개발 가이드에서 모듈 책임, 분할·재사용 기준, system/user 조립, 실제 Runtime AI 전달 및 로컬 확인 절차를 설명하고 Spec·진입점을 연결한다.

## Validation

### Initial Extraction

최초 분리 단계의 검증 기록이다. 아래 모듈 경계 보완 단계에서 전체 suite를 다시 실행했다는 의미는 아니다.

- 조각 조립 테스트의 변경 전 실패 3개와 변경 후 focused 23개 통과를 확인했다. Review AI/Runtime AI suite는 291 passed, 1 skipped다.
- 분리 전 전체 원문과 source 및 checkout 밖 wheel의 실제 system 메시지를 대조했다. 세 version의 바이트·순서·공백·개행과 기존 golden digest는 모두 동일하다.
- wheel/sdist에 12개 Markdown 조각이 포함되고 이전 전체 파일이 제거되었음을 확인했다.
- Ruff, format, ty, Markdown, Inbox 형식, editor diagnostics와 diff 검사를 통과했다. OpenSpec strict 검증은 29 passed, 0 failed다.
- 채택 정책은 명문화했으며 이번 변경으로 현재 version 기본값이나 모델의 검토 결과를 바꾸지 않는다.

### Module Boundaries

- 경로를 바꾼 조합 회귀는 구현 전 3 failed, 파일 이동 후 프롬프트·Runtime 전달 focused suite는 23 passed다. 세 기존 golden digest는 그대로이며 이전 전체 본문과도 일치한다.
- 새 개발 가이드의 합성 사례 예제를 그대로 실행해 system/user 메시지 두 개와 7,803-byte 프롬프트를 확인했다. 모델 호출과 데이터 적재는 수행하지 않았다.
- 새 경로의 12개 모듈이 wheel/sdist에 포함됐다. 별도 process를 checkout 밖에서 wheel로 실행해 세 조합의 전체 메시지와 digest가 source와 일치함을 확인했다.
- 모듈·재사용 계약을 canonical Spec과 관련 MODIFIED delta에 맞췄다. OpenSpec strict는 29 passed, 0 failed이며 Ruff·format·Markdown·상대 링크·editor diagnostics·diff 검사도 통과했다.
