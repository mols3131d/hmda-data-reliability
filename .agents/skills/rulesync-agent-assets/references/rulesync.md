# Rulesync Backend

Load this reference only when exact CLI syntax, target identifiers, feature support,
or source discovery matters. The installed Rulesync version is the runtime authority.

## Preflight

```bash
rulesync --version
rulesync <command> --help
```

Do not assume a target or flag exists because it existed in another Rulesync
version.

## Canonical Fan-out

Use when `.rulesync/` is authoritative.

```bash
rulesync generate --dry-run \
  --targets <targets> \
  --features <features>

rulesync generate \
  --targets <targets> \
  --features <features>

rulesync generate --check \
  --targets <targets> \
  --features <features>
```

`generate --check` verifies that generated files are up to date for the selected
scope.

## Native Bridge

Use when one harness's native configuration remains authoritative.

```bash
rulesync convert \
  --from <source> \
  --to <targets> \
  --features <features> \
  --dry-run

rulesync convert \
  --from <source> \
  --to <targets> \
  --features <features>
```

`convert` performs direct native-to-native translation without writing `.rulesync/`
source files. Do not include the source harness in `--to`.

## Features

Common feature identifiers:

```text
rules
mcp
commands
subagents
skills
hooks
permissions
checks
```

`ignore` is a deprecated compatibility feature; prefer `permissions` for new work.
Use the smallest feature set that matches existing source assets. Use `*` only for
an intentionally broad synchronization.

## Common Targets

| Harness | Target |
| --- | --- |
| GitHub Copilot | `copilot` |
| Claude Code | `claudecode` |
| Codex CLI | `codexcli` |
| Google Antigravity IDE | `antigravity-ide` |
| Google Antigravity CLI | `antigravity-cli` |

For any other harness, confirm the identifier with the installed CLI or current
Rulesync documentation instead of guessing.

## Discovery

Rulesync converts only assets its source adapter discovers. Custom editor settings,
non-native paths, alternate filenames, or project-specific layouts may therefore be
valid for the source harness but invisible to Rulesync.

When an expected source is not discovered, do not hide the gap by copying or
renaming it automatically. Choose explicitly among:

1. keep the native source and report the backend limitation;
2. normalize the source path as a separate, intentional project change;
3. adopt a canonical Rulesync source when canonicalization is itself desired.

## Fidelity

A successful conversion proves that Rulesync emitted files, not that both harnesses
have identical runtime semantics. Treat warnings, omitted fields, target simulation,
and unsupported concepts as compatibility evidence that must be reported.

Prefer native output. Use simulation flags only when the user or project policy
accepts simulated behavior.

## Scope Safety

- Preview writes with `--dry-run`.
- Use project scope unless user-global configuration is explicitly requested.
- Do not install, update, clean, or delete as part of an ordinary conversion.
- Plugin-packaging targets are not ordinary `convert` targets; use their supported
  import/generate workflow only when plugin packaging is the actual task.
