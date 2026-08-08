# OpenSpec Specs

`openspec/specs/` stores the current canonical capability specifications.

## Naming

Spec IDs use:

```text
<domain>[-<subdomain>]-<capability>[-<extensions>]
```

- Start with the owning domain so specs group naturally by responsibility.
- Use a subdomain only when it improves classification inside a domain.
- End at the capability when that is sufficiently specific.
- Add extensions only when a capability needs a stable, meaningful distinction.
- Use lowercase kebab-case.

Examples:

```text
hmda-data-ingestion
data-platform-dbt
reliability-incident-detection
reliability-incident-detection-profile
orchestration-pipeline
```

## Scope

A spec represents a persistent system capability, not a project phase, implementation task, or temporary change.

Requirements describe observable behavior and data contracts. Implementation details belong in design artifacts, source code, tests, or owning project documentation.

## Ownership

Domain ownership follows the canonical domain boundaries documented in [`docs/domains/OVERVIEW.md`](../../docs/domains/OVERVIEW.md).

When a spec spans multiple areas, assign it to the domain that owns the resulting capability rather than listing multiple peer domains in the Spec ID.
