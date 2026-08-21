---
trigger: glob
globs: "src/**/*"
---

# Development

- Keep dependencies directional; do not bypass an established interface to reach another module's internals.
- Separate domain logic from I/O, framework glue, and environment configuration where practical.
- Do not hard-code secrets, machine-specific paths, environment-dependent values, or operational configuration. Keep genuine domain constants with their owner.
- Preserve observable behavior, including public APIs, return values, exceptions, state transitions, side-effect order, validation, and observability, unless the contract changes.
- Prefer code that explains itself. Use comments only for non-obvious rationale, policy, constraints, invariants, exceptions, or ordering; keep them near their owner and update them with the code.
- When behavior changes, update the owning contract and relevant tests or documentation.
