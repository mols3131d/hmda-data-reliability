---
type: openspec-spec-driven-tdd-design
category: design
title: Compose Review AI Prompt Parts
description: 정적인 조각 순서와 LF 구분자로 기존 메시지 바이트를 보존합니다.
---

## Technical Delta

`prompt/__init__.py`에 version별 Markdown 상대 경로 tuple을 고정한다. 제목, 공통 역할·언어·자문, 간략/상세 출력 계약, 예시와 v3 검토 지침을 조각으로 나눈다. 외부 입력에서 경로나 include 지시를 읽는 템플릿 엔진은 추가하지 않는다.

각 조각은 기존 섹션에서 추출해 마지막 LF 하나를 유지한다. 로더는 원문 사이에 LF 하나를 넣어 기존 섹션 사이의 빈 줄을 재현한다. 본문을 `strip()`하거나 Markdown을 변환하지 않는다. 기존 세 메시지 digest를 변경하지 않고 조립 전후의 전체 문자열도 대조한다.

단일 active 기본값은 채택 변경이 충족해야 할 lifecycle이다. 이번 구조 분리에서는 현재 API v1과 live v2를 유지한다. 과거 실행의 명시된 identity와 revision은 미래 기본값과 분리한다.
