---
name: prj-testing
description: "Use when running, selecting, debugging, or checking coverage for this project's pytest tests. Follow the commands, markers, and options in docs/DEVELOPMENT.md."
---

# Testing

Use `pytest` through `uv`. Start with the narrowest relevant test.

## Workflow

1. Select a path, test name, keyword, or marker.
2. Project defaults already enable parallel execution, a 60-second timeout, an HTML report, and strict markers through `pyproject.toml`.
3. Use `-n 0 -vv -s` only when debugging order, output, or concurrency issues.
4. Use `--lf` to rerun the last failure.
5. Use coverage when the change needs it.

## Commands

```bash
uv run pytest
uv run pytest tests/data_platform
uv run pytest tests/data_platform/test_sql.py
uv run pytest tests/data_platform/test_sql.py::test_name
uv run pytest -k "keyword"
uv run pytest -m unit
uv run pytest -m "not integration"
uv run pytest --lf
uv run pytest --cov=src/project_pivot
```

For detailed testing guidance and the complete option reference, see [`docs/DEVELOPMENT.md`](../../../docs/DEVELOPMENT.md#testing).
