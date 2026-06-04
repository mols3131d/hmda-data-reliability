# AGENTS.md

## Language & Documentation

- **Korean (KO) Priority**: Write all comments, docstrings, markdown docs, logs in clear Korean.
  - *Exception*: Variable names, class names, API specs stay standard English.
- **Commit Messages**: KO. Follow 'Conventional Commits'. Explain "Why".

## Code Style & Architecture

- **SRP**: 1 function/class = 1 task. 1 LangGraph node = 1 logic step.
- **Type Hints**: Explicit `typing` everywhere. `TypedDict` mandatory for LangGraph State.
- **Pydantic Validation**: Structured Output via Pydantic for LLM. Prevent hallucination.
- **Idempotency**: Ingestion/dbt must overwrite partition. No duplicate data.

## Observability

- **Logging**: No `print()`. Use standard `logging` with JSON context in `extra`.
- **Exceptions**: Custom errors with detailed context. No raw stacktrace.
