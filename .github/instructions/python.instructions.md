---
description: "Python-specific source rules under src. Covers imports, typing, resource handling, exceptions, mutable state, and docstrings."
applyTo: "src/**/*.py"
name: "Python"
---

# Python

- Use explicit imports and deliberate `__init__.py` exports. Prefer public package surfaces; avoid wildcard imports, deep private imports, and parallel public APIs.
- Keep type annotations precise at public boundaries and for non-obvious values. Contain `Any` at untyped integration boundaries rather than propagating it.
- Use `pathlib.Path` for filesystem paths and context managers for managed resources.
- Catch narrow exception types. Do not silently swallow failures; preserve causal context when translating exceptions.
- Avoid mutable default arguments and hidden module-level mutable state.
- Add docstrings to public or non-obvious APIs when names, signatures, and types do not fully express the caller contract. Document only caller-relevant semantics such as purpose, non-obvious inputs or outputs, exceptions, side effects, preconditions, or ordering.
- Keep docstrings durable and contract-level: state what callers may rely on and why non-obvious constraints exist, not implementation steps; do not repeat type annotations or obvious names.
