# Project Pivot Profile

Use this file only to resolve Project Pivot defaults and known discovery gaps. The
shared Skill owns the workflow; this profile owns only project-specific facts.

## Default Source

When a cross-harness port does not name a source, treat **GitHub Copilot-owned
native assets** as the default source.

```text
mode: native-bridge
source: copilot
targets: explicit per request
features: smallest applicable set
scope: project
```

If the request explicitly selects `.rulesync/` as canonical source, use Canonical
fan-out instead.

## Source Inventory

| Feature | Current owner | Rulesync `copilot` discovery |
| --- | --- | --- |
| `rules` | `.github/instructions/*.instructions.md` | expected |
| `subagents` | `.github/agents/*.agent.md` | expected |
| `hooks` | `.github/hooks/dogfooding-observability.json` | gap |
| `skills` | `.agents/skills/` | not a Copilot-source assumption |

Include a feature only when its source is actually present and discoverable.

## Known Gaps

### Hooks

Rulesync's Copilot project hook adapter expects:

```text
.github/hooks/copilot-hooks.json
```

Pivot currently owns:

```text
.github/hooks/dogfooding-observability.json
```

Do not assume `convert --from copilot --features hooks` reads that alternate file.
Confirm discovery in preview. If hooks must be portable, report the gap or propose
source normalization as a separate intentional change; do not silently rename or
copy the file.

### Skills

Pivot keeps project Skills in:

```text
.agents/skills/
```

Treat these as portable Skills first. If a target already discovers them, use the
shared Skill's no-transform route. Do not claim Rulesync's `copilot` source adapter
will import them merely because Copilot can consume Skills from other supported
locations.

## Boundaries

- Do not modify `.github/` Copilot source assets as a conversion side effect.
- Do not relocate `.agents/skills/` just to satisfy a backend discovery path.
- Generated target assets are derived; fix source or a confirmed compatibility gap
  rather than hand-editing generated output.
- Prefer explicit features over `--features "*"`.
