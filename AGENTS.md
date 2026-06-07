# AGENTS.md

## Language & Terminology

- **Korean Priority**: Add/change user docs/comments/logs in Korean.
  - Keep identifiers/API specs/error codes in English.
  - Avoid repeating code in comments.

## Code Style & Architecture

- **SRP**: Keep functions/classes focused. Extract helpers only to reduce complexity/duplication.
- **One Class per File**: Put major classes/models in individual files (SRP).
- **LangGraph**: Use `TypedDict` for State. Node = 1 workflow step.
- **Structured Output**: Use Pydantic for LLM outputs/contracts.
- **Idempotency**: Ingestion/dbt must overwrite partitions or use deterministic upserts. No duplicates.

## Documentation & Commits

- **Conciseness**: Keep docs short/scannable.
- **Docstrings**: 1-3 lines.
- **Commit Messages**: Conventional Commits.
- **Visualization**: 단순 시각화는 Markdown/Mermaid/인라인 HTML을 사용하고, 복잡한 시각화는 별도 HTML 파일로 분리 생성 후 상대 경로 링크로 연결합니다.

## Observability

- **Logging**: No `print()`. Use `logging` + `extra`.
- **Exceptions**: Custom exceptions. Include context, hide stack traces from users/API.

---

@`.agents/rules/*.md`
