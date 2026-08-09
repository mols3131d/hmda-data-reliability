---
name: prj-testing
description: "Use when writing, changing, selecting, running, debugging, validating, or checking coverage for this project's pytest tests. Also use for test-first work, pytest markers, fixtures, assertions, test failures, test plans, scenarios, oracles, and test design."
---

# Project Testing

Use this skill for any pytest-related work in Project Pivot.

## Load Context

- When changing files under `tests/`, read [`tests/AGENTS.md`](../../../tests/AGENTS.md).
- When deciding what behavior to test, read [`docs/development/test-design-and-implementation.md`](../../../docs/development/test-design-and-implementation.md).
- When selecting or running pytest commands, read [`docs/development/testing.md`](../../../docs/development/testing.md).

These documents have separate ownership. Do not duplicate their detailed rules in a test change or invent a conflicting convention.

## Execution Defaults

- Run pytest through `uv`.
- Start with the narrowest relevant test path, test node, keyword, or marker.
- `pyproject.toml` supplies timeout, strict markers, and the default resource-test filter.
- Parallel execution, hook selection, and report generation are execution policies owned by `testing.md` and `lefthook.yml`; do not assume they are global pytest defaults.
- Use `--lf` only to rerun a known previous failure.
- Collect HTML, coverage, trace, or JUnit evidence only when it adds evidence for the change.

## Agent Evidence

When a result must be parsed or persisted, disable decorative output and write JUnit XML.

```bash
mkdir -p artifacts && uv run pytest <focused-target> \
	-p no:sugar \
	--color=no \
	--tb=short \
	-ra \
	--junitxml=artifacts/pytest.xml
```

Replace `<focused-target>` with the narrowest applicable path, node, keyword, or marker. Treat `artifacts/pytest.xml`, HTML reports, cache, and coverage output as generated evidence, not authored source.

Report the executed command, outcome, failure classification, and remaining risk. Never claim an unexecuted test passed.
