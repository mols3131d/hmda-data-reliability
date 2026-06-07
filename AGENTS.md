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

## Observability

- **Logging**: No `print()`. Use `logging` + `extra`.
- **Exceptions**: Custom exceptions. Include context, hide stack traces from users/API.

---

@`.agents/rules/*.md`
