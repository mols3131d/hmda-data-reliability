---
type: openspec-spec-driven-tdd-design
category: design
title: Localize Review AI Prompts
description: 기존 버전 선택과 JSON 계약을 유지하면서 텍스트 리소스의 설명 언어를 바꿉니다.
---

## Technical Delta

`prompt/v1.txt`, `v2.txt`, `v3.txt`의 자연어를 한국어로 바꾸고 네 종류의 설명 필드에 한국어 출력을 지시한다. `context.py`가 자체 생성하는 gap과 빈 요약 대체 문구도 한국어로 바꾼다. 필드명·열거값·식별자와 원본 Evidence/Draft의 데이터는 번역하지 않는다. 기존 `importlib.resources` 로더, Python 기본 v1과 live 기본 v2는 유지한다.

번역은 새 application revision의 변경으로 식별하며 현재 한국어 리소스의 golden digest를 별도로 고정한다. 과거 영어 실행은 저장된 `project_revision`의 renderer와 리소스로 재생한다. 언어 준수는 프롬프트와 사람 평가의 책임이며 validator에 문자 집합 검사나 자연어 분류기를 추가하지 않는다.
