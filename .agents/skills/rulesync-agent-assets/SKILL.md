---
name: rulesync-agent-assets
description: >-
  Use when synchronizing or porting agent customization assets across coding-agent
  harnesses with Rulesync: either generate multiple harness-native outputs from a
  `.rulesync/` canonical source, or translate one harness's native rules, agents,
  skills, commands, hooks, permissions, checks, or MCP configuration into other
  harnesses. Also use when keeping Copilot, Claude Code, Codex CLI, Antigravity,
  or other Rulesync targets aligned. Do not use for a single-harness edit or when
  the target already consumes the same source without conversion.
compatibility: >-
  Requires the Rulesync CLI and a Rulesync-supported source/target harness. Exact
  targets, discovery paths, and feature support follow the installed Rulesync
  version.
metadata:
  author: mols3131d
  version: "0.1.0"
---

# Rulesync Agent Assets

Preserve one clear source and do the least transformation needed. This Skill owns
routing, scope, safety, and evidence. Rulesync owns format translation.

## Route

Choose the first route that satisfies the request.

| Situation | Route | Backend |
| --- | --- | --- |
| Target already consumes the same source correctly | Reuse it | none |
| `.rulesync/` is the source of truth | Canonical fan-out | `generate` |
| One harness's native assets are the source of truth | Native bridge | `convert` |

Do not introduce `.rulesync/` merely to perform a native-to-native port. Use
`import -> generate` only when adopting or rebuilding a canonical Rulesync source
is itself part of the request.

If multiple sources compete for authority and project policy does not resolve it,
stop before mutation and report the ambiguity.

## Execute

1. Read project authority and identify the current source owner. Keep the write
   boundary limited to requested targets.
2. Select the route above. If no transformation is required, verify discovery and
   stop without generating duplicate assets.
3. For a Rulesync route, confirm the CLI is available with `rulesync --version`.
   Do not install or upgrade it implicitly.
4. Resolve explicit targets and the smallest applicable feature set. Default to
   project scope; do not broaden to `*` or `--global` without a reason.
5. Read [Rulesync backend](references/rulesync.md) only when exact commands, target
   IDs, feature support, or discovery behavior matter. If
   `references/project.md` exists, read it only for project-specific defaults or
   known gaps.
6. Preview every write with the matching Rulesync dry-run.
7. Inspect the preview for unexpected files, missing source assets, warnings,
   simulated behavior, and semantics the target cannot express.
8. Apply only when the preview matches the requested scope. Then inspect the
   generated diff and run the strongest applicable validation.

## Compatibility Contract

- Preserve the selected source of truth. Generated targets are derived artifacts.
- Do not silently rename, copy, relocate, or normalize source assets just to make
  Rulesync discover them.
- Treat `converted` as a file-generation result, not proof of semantic parity.
- Report omitted, approximated, simulated, or undiscovered behavior as a
  compatibility gap.
- Prefer native target support over simulation. Enable simulation only when the
  request explicitly accepts that tradeoff.
- Do not add a wrapper script, custom adapter, or parallel schema until a concrete
  Rulesync limitation requires one.
- Do not perform install, upgrade, cleanup, deletion, or user-global mutation as a
  side effect of asset conversion.

## Validate

For Canonical fan-out, use the same target and feature scope with Rulesync
`generate --check` when available after generation.

For Native bridge, use the dry-run, generated diff, target-native validation, and
project-owned checks. Do not invent a `generate --check` equivalent for `convert`.

For a no-transform route, verify that the target actually discovers the retained
source; otherwise choose a transformation route.

## Report

Return only evidence needed to understand the result:

```text
mode: <reuse | canonical-fan-out | native-bridge>
source: <owner>
targets: <targets>
features: <features>
generated: <paths or none>
gaps: <none or concise list>
validation: <checks actually run>
```

Complete when the requested targets are available, the source remains authoritative,
and every known compatibility gap or unrun validation is stated explicitly.
