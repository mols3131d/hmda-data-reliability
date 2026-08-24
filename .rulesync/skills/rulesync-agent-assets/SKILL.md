---
name: rulesync-agent-assets
description: >-
  Use when generating harness-native agent assets from one Rulesync source, or
  porting one harness's native rules, agents, skills, commands, hooks,
  permissions, checks, or MCP configuration to other harnesses through Rulesync.
  Do not use for a single target-specific edit with no cross-harness sync need.
compatibility: >-
  Requires a Rulesync runtime. Exact targets and feature support follow the
  effective Rulesync version selected by project policy, or the installed CLI
  when the project does not define one.
---

# Rulesync Agent Assets

Rulesync를 cross-harness 변환 backend로 사용한다. 이 Skill은 source, target,
scope와 safety를 결정하고, parsing·normalization·serialization은 Rulesync에
맡긴다.

## Modes

| Mode | Source | Backend operation |
| --- | --- | --- |
| Canonical fan-out | Rulesync canonical source (`.rulesync/`) | `generate` |
| Native bridge | 한 harness의 native asset | `convert` |

두 mode를 별도 구현으로 만들지 않는다. source model만 다르고 target 선택,
preview, compatibility 확인과 validation 원칙은 공유한다.

## Workflow

1. project authority와 현재 asset ownership을 읽고 write boundary를 정한다.
1. project가 Rulesync execution entrypoint나 version policy를 정의하면 그것을 우선한다.
   없으면 `rulesync --version`으로 backend availability를 확인하고 명시적 허용 없이
   install 또는 upgrade하지 않는다.
1. source mode를 결정한다.
   - project가 canonical source를 지정했거나 사용자가 fan-out을 요청하면 Canonical fan-out을 쓴다.
   - 사용자가 source harness를 명시하면 Native bridge를 쓴다.
   - 명시가 없으면 project policy를 우선하고, 그 다음 명확한 existing source를 사용한다.
     여러 source가 경쟁하면 추측하지 않는다.
1. target과 feature를 최소 범위로 결정한다. source harness를 target에 포함하지 않고,
   사용자나 project policy가 요구하지 않으면 `*`로 범위를 넓히지 않는다.
1. exact command, target ID 또는 feature behavior가 필요할 때만
   [Rulesync backend](references/rulesync.md)를 읽는다. deployed copy에
   `references/project.md`가 있으면 project-specific default가 필요한 경우에만 읽는다.
1. mutation 전에 project entrypoint 또는 Rulesync `--dry-run`으로 preview를 실행한다.
1. preview의 warning, 누락 feature, simulation 또는 표현력 차이를 compatibility gap으로
   취급한다. 확인되지 않은 semantic parity를 주장하지 않는다.
1. preview가 요청 범위와 일치할 때만 실제 generation 또는 conversion을 실행한다.
1. generated diff와 applicable project validation을 확인한다. Canonical fan-out은 가능한
   경우 Rulesync `--check`도 사용한다.
1. source, mode, targets, features, 생성된 asset, warning과 실제 수행한 validation을 보고한다.

## Canonical Fan-out

Project-owned execution entrypoint가 있으면 direct CLI보다 우선한다. 없으면 다음 기본
Rulesync flow를 사용한다.

```bash
rulesync generate --dry-run --targets <targets> --features <features>
rulesync generate --targets <targets> --features <features>
rulesync generate --check --targets <targets> --features <features>
```

`generate` output은 derived asset으로 취급한다. target file을 직접 수정해서 source와
drift를 만들지 않는다.

## Native Bridge

한 harness의 native asset을 유지하면서 다른 harness asset을 만들 때 사용한다.

```bash
rulesync convert --from <source> --to <targets> \
  --features <features> --dry-run
rulesync convert --from <source> --to <targets> \
  --features <features>
```

단순 port를 위해 먼저 `.rulesync/`로 import하지 않는다. canonicalization 자체가
요구사항일 때만 `import -> generate` 경로를 선택한다.

## Boundaries

- project가 선택한 source of truth를 이 Skill의 선호로 바꾸지 않는다.
- generated target asset을 수동 편집하지 않는다. 수정은 source 또는 명시된
  compatibility layer에서 한다.
- Project-owned Rulesync wrapper가 있으면 재사용하고 경쟁하는 wrapper를 추가하지 않는다.
- Rulesync가 발견하지 못하는 custom path나 unsupported semantic을 지원한다고 가정하지 않는다.
- backend warning이나 omitted feature를 조용히 무시하지 않는다.
- simulation은 native support와 동일하게 취급하지 않으며 명시적으로 필요한 경우에만 사용한다.
- `--global`, destructive cleanup, install 또는 upgrade는 project policy나 사용자 요청 없이 실행하지 않는다.

## Completion

요청된 source에서 요청된 target만 생성했고, source는 보존되었으며, compatibility gap과
validation evidence를 정확히 보고하면 완료한다.
