---
name: prj-testing
description: "Use when running, selecting, debugging, or checking coverage for this project's pytest tests. Follow the commands, markers, and options in docs/TESTING.md."
---

# Testing

Use `pytest` through `uv`. Start with the narrowest relevant test. The canonical human and Agent commands are maintained in [`docs/TESTING.md`](../../../docs/TESTING.md).

## Workflow

1. Select a path, test name, keyword, or marker.
1. Project defaults already enable parallel execution, a 60-second timeout, an HTML report, and strict markers through `pyproject.toml`.
1. Use the Agent command from `docs/TESTING.md` when a result must be easy to parse or persist.
1. Use `-n 0 -vv -s` only when debugging order, output, or concurrency issues.
1. Use `--lf` to rerun the last failure.
1. Use coverage when the change needs it.

## Commands

```bash
mkdir -p artifacts && uv run pytest
mkdir -p artifacts && uv run pytest tests/data_platform
mkdir -p artifacts && uv run pytest tests/data_platform/test_sql.py
mkdir -p artifacts && uv run pytest tests/data_platform/test_sql.py::test_name
mkdir -p artifacts && uv run pytest -k "keyword"
mkdir -p artifacts && uv run pytest -m unit
mkdir -p artifacts && uv run pytest -m "not integration"
mkdir -p artifacts && uv run pytest --lf
mkdir -p artifacts && uv run pytest --cov=src/project_pivot
```

For detailed testing guidance and the complete command reference, see [`docs/TESTING.md`](../../../docs/TESTING.md).
