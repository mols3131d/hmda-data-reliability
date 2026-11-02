---
type: openspec-spec-driven-tdd-design
category: design
title: Review AI Evaluation Package Boundaries
description: Evaluation ownership, executable child entrypoint과 serialized compatibility를 하나의 subpackage 안에서 보존한다.
---

## Technical Delta

### D1. Evaluation subpackage ownership

- **Decision:** `review_ai/evaluation/`을 package로 만들고 `value.py`가 rubric, human assessment, comparison과 output digest를 소유하며 `langfuse.py`가 isolated optional projection과 annotation helper를 소유한다. Package `__init__.py`는 value API만 re-export하고 Langfuse adapter는 owning submodule path에서 직접 호출한다.
- **Rationale:** Review AI evaluation 외에 다른 AI consumer가 없으므로 소유권을 Review AI 안에 두고, 공통 abstraction이나 별도 Tach module boundary를 추가하지 않는다.

### D2. Python API rename and compatibility

- **Decision:** `Utility*` evaluation symbols를 계획서의 `ReviewValue*` 이름으로 교체하고 package root의 curated export를 새 이름으로 갱신한다. Deprecated alias나 old-module wrapper는 만들지 않는다.
- **Rationale:** 이 repository의 package version은 `0.1.0`이고 확인된 consumers는 repository 내부뿐이다. Python import rename은 의도적인 pre-1.0 breaking change로 취급한다. External consumer가 확인되면 compatibility 정책을 별도 변경으로 결정한다.

### D3. Child entrypoint and serialized compatibility

- **Decision:** Parent process는 `python -m hmda_reliability.review_ai.evaluation.langfuse`를 실행한다. `langfuse.py`의 `__main__` 경계가 stdin payload 처리, sanitization, SDK import, timeout/environment isolation을 기존처럼 소유한다. `review_output_digest()`는 기존 canonical JSON encoding과 SHA-256 표현을 그대로 사용하고, model field 및 enum serialized values는 rename하지 않는다.
- **Rationale:** Child module path는 런타임 entrypoint이므로 source move와 함께 반드시 바뀌어야 한다. Python symbol 이름은 serialized evaluation payload에 넣지 않아 stored evidence와 annotation binding은 유지한다.
