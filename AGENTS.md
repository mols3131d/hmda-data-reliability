# AGENTS.md

## Language & Terminology

- **Korean Priority**: Write user-facing docs, comments, docstrings, and logs in clear Korean when adding or changing them.
  - Keep identifiers, API specs, error codes, and standard technical terms in English.
  - Avoid comments that merely repeat the code.

## Code Style & Architecture

- **SRP**: Keep functions/classes focused. Extract helpers only when they reduce real complexity or duplication.
- **One Class per File**: Organize major classes and domain models into individual files to enforce file-level Single Responsibility Principle (SRP).
- **LangGraph**: Use `TypedDict` for State. Keep each node aligned to one meaningful workflow step.
- **Structured Output**: Use Pydantic for LLM-facing structured outputs and external contracts.
- **Idempotency**: Ingestion and dbt processes must overwrite target partitions or use deterministic upserts. No duplicate rows.

## Documentation & Commits

- **Conciseness**: Keep docs concise and scannable.
- **Docstrings**: Keep docstrings concise, typically 1-3 lines.
- **Commit Messages**: Conventional Commits.

## Observability

- **Logging**: Never use `print()`. Use standard `logging` with structured context in `extra`.
- **Exceptions**: Use custom exceptions for domain/application errors. Include useful context, but do not expose raw stack traces to users or API clients.

---

@`.agents/rules/*.md`
