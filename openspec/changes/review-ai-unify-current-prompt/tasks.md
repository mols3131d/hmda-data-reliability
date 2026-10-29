---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Unify Current Review Prompt
description: 일반 API·CLI와 현재 프롬프트의 선택을 통일합니다.
tasks_completed: 3
tasks_total: 3
---

## Tasks

- [x] 일반 Python 진입점을 현재 단계 실행으로 통일하고 기존 구현을 legacy로 옮긴다.
  - **Test first:** 일반 공개 API와 직접 service에서 실제 세 단계 text 호출·코드 JSON 취합을 확인하는 회귀를 먼저 실패시킨다.
  - **Done when:** 일반 API는 version 없이 현재 실행을 제공하고 명시적 legacy 호출은 기존 structured 계약을 유지한다.
- [x] 버전 렌더러·snapshot을 legacy로 분리하고 현재 언어 정책을 연결한다.
  - **Test first:** 일반 import의 legacy 미로딩, 세 단계 한국어 정책 사용, legacy golden digest 보존을 먼저 확인한다.
  - **Done when:** 현재 모듈과 retired version을 독립적으로 로드하며 배포 wheel에서도 snapshot을 읽을 수 있다.
- [x] CLI·환경 예제·정본 안내를 현재 기본과 명시적 legacy 선택에 맞춘다.
  - **Test first:** 기본 실행, stale version 무시·값 비노출, legacy version 필수, structured 호출 전 거부를 먼저 실패시킨다.
  - **Done when:** CLI와 Python 기본이 같은 현재 실행을 사용하고 기존 기록의 재현·실패 보존 회귀와 정적·OpenSpec 검사가 통과한다.

## Validation

- 기준은 `a6d299e64596de88487e1708acabbba992a0f7e0`이다. 일반 API 2개의 prompt_identity 필수 오류와 CLI 신규 선택 회귀 9개의 구현 전 실패, legacy renderer 부재를 확인했다.
- Review AI/Runtime AI 전체 **407 passed, 1 skipped**. 생략은 optional Langfuse SDK media smoke다. 일반 API와 직접 service에서 세 단계 text 수집·코드 JSON 취합을 검증하고 legacy service의 기존 회귀를 명시적 경로에서 유지했다.
- 현재 API·CLI import에서 legacy 미로딩, 일반 환경의 옛 version 무시·값 비노출, legacy의 명시 version 필수 및 structured 모드의 무호출 거부를 확인했다.
- v1/v2/v3 snapshot 원문과 기존 golden digest 3개를 유지했다. Wheel을 checkout 밖의 isolated Python에서 직접 import해 현재 세 단계와 legacy 메시지·digest가 source와 같고 일반 import가 legacy를 로드하지 않음을 확인했다.
- Ruff·format·ty·Tach·Markdown·diff 및 OpenSpec strict **32 passed, 0 failed**를 확인했다. 문서의 수정된 Mermaid도 문법 검증과 preview를 완료했다.
- 독립 검토에서 찾은 정본의 옛 v1/v2 기본 지시를 legacy 기록 해석으로 한정하고 해당 active delta를 동기화했다.
- 로컬 `.env`에서 기존 PROMPT_VERSION을 제거하고 MODE=staged를 명시했다. 실제 CLI 설정 로딩에서 현재 기본 함수 사용·legacy 미로딩을 provider 호출 전에 확인했다. 모델·credential·기존 시간 설정은 유지했다.
- 실제 모델 생성·main 병합·현재 revision의 hosted CI 확인은 수행하지 않았다. 이 전환은 사용자가 요청한 실행 경로 선택이며 품질 채택 증거가 아니다.
