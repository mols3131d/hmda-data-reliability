# AGENTS.md

## Code Style

- **SRP**: Keep functions/classes focused. Extract helpers only to reduce complexity/duplication.
- **One Class per File**: Put major classes/models in individual files (SRP).

### Observability

- **Logging**: No `print()`. Use `logging` + `extra`.
- **Exceptions**: Custom exceptions. Include context, hide stack traces from users/API.

## Documentation

- **Conciseness**: Keep docs short/scannable.
- **Docstrings**: 1-3 lines.
- **Visualization**: Use Markdown, Mermaid, ASCII art, or inline HTML for simple visualizations; for complex visualizations, create a separate HTML file and link to it using a relative path.

## Others

- **Git Commit Messages**: Conventional Commits.
