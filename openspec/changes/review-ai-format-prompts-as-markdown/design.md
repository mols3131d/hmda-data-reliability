---
type: openspec-spec-driven-tdd-design
category: design
title: Format Review AI Prompts as Markdown
description: Markdown 원문을 가공 없이 system 메시지로 로드합니다.
---

## Technical Delta

기존 `importlib.resources` 로더의 확장자만 `.md`로 바꾸고 Markdown을 제거하거나 HTML로 변환하지 않는다. 프롬프트의 제목과 본문은 사용자가 요청한 한국어를 유지한다. v2의 기존 예시만 JSON 코드 블록으로 표시하며 v3에는 내용 예시를 추가하지 않는다. 모든 버전에 응답은 JSON 객체 하나이고 Markdown 표기를 붙이지 않는다는 지시를 둔다.
