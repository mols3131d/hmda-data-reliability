---
type: openspec-spec-driven-tdd-design
category: design
title: Extract Review AI Prompt Resources
description: 패키지 리소스로 지시문을 읽고 기존 Python API와 메시지 바이트를 보존합니다.
---

## Technical Delta

렌더링 구현은 `prompt/__init__.py`에 유지하고 `importlib.resources`로 같은 패키지의 `v1.txt`, `v2.txt`, `v3.txt`를 UTF-8로 읽는다. 작업 디렉터리나 checkout 경로에 의존하지 않으며 wheel 내부에도 리소스를 포함한다. 기존 문자열에는 마지막 개행이 없으므로 리소스도 같은 바이트를 유지하고 `strip()` 등 내용 변환을 하지 않는다.
