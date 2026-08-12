---
name: pivot-load-context-testing
description: >-
  Load Project Pivot testing context when writing, changing, selecting, running,
  debugging, validating, or checking coverage for pytest tests. Also use for
  test-first work, pytest markers, fixtures, assertions, test failures, test
  plans, scenarios, oracles, and test design.
---

# Testing Context

Load the smallest Project Pivot testing context needed for the task. Canonical testing documents own the detailed rules; this skill selects and anchors the context needed to apply them consistently.

## Load Context

- When changing authored files under `tests/`, read [`tests/AGENTS.md`](../../../tests/AGENTS.md).
- When designing, changing, or reviewing behavior, scenarios, oracles, assertions, or test level, read [`docs/development/test-design-and-implementation.md`](../../../docs/development/test-design-and-implementation.md).
- When selecting, running, or debugging pytest commands, markers, reports, coverage, or traces, read [`docs/development/testing.md`](../../../docs/development/testing.md).
- When exact configured pytest defaults or plugin availability matters, inspect [`pyproject.toml`](../../../pyproject.toml). When Git hook behavior matters, inspect [`lefthook.yml`](../../../lefthook.yml).

Read only the context relevant to the current task. Do not duplicate detailed rules or invent a conflicting convention.

## Execution Defaults

- Run pytest through `uv`.
- Start with the narrowest relevant test path, test node, keyword, or marker.
- `pyproject.toml` supplies the project pytest defaults; do not override them without a task-specific reason.
- Parallel execution, hook selection, and report generation are execution policies owned by `testing.md` and `lefthook.yml`; do not assume they are global pytest defaults.
- Use `--lf` only to rerun a known previous failure.
- Collect HTML, coverage, trace, or JUnit evidence only when it adds evidence for the task.

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

## Boundaries

- Loading testing context does not expand the write scope of the current task.
- Do not weaken assertions, broaden exceptions, or add unconditional skips to make an implementation pass.
- If a failure indicates a production defect, specification gap, environment failure, or unrelated baseline failure, classify and report it; production changes follow the rules of the task that owns them.
- Do not redefine detailed test-design, execution, marker, hook, or reporting policy in this skill.
