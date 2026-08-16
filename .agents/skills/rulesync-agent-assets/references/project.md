# Project Pivot Defaults

Project Pivot에서 source가 명시되지 않은 cross-harness port는 **GitHub Copilot
native assets를 source**로 해석한다.

## Default Route

```text
mode: native bridge
source: copilot
targets: explicit per request
features: smallest applicable set
scope: project
```

사용자가 `.rulesync/` canonical source를 명시하거나 fan-out을 요청하면 이 default를
무시하고 Canonical fan-out mode를 사용한다.

## Copilot Source Inventory

현재 project에서 Rulesync `copilot` source와 자연스럽게 대응하는 주요 asset은 다음과
같다.

| Feature | Project source |
| --- | --- |
| `rules` | `.github/instructions/*.instructions.md` |
| `subagents` | `.github/agents/*.agent.md` |

추가 Copilot-native asset이 생기면 Rulesync의 현재 source discovery contract를 먼저
확인한 뒤 feature 범위에 포함한다.

## Known Discovery Gaps

### Hooks

현재 project hook은 다음 파일에 있다.

```text
.github/hooks/dogfooding-observability.json
```

현재 Rulesync의 `copilot` hook adapter는 project hook source로 다음 파일을 읽는다.

```text
.github/hooks/copilot-hooks.json
```

따라서 `dogfooding-observability.json`을 `convert --from copilot --features hooks`가
자동으로 읽는다고 가정하지 않는다. hook 변환이 요청되면 preview에서 discovery를
확인하고, 필요하면 source normalization을 별도 변경으로 제안하거나 limitation으로
보고한다. 파일을 몰래 rename 또는 copy하지 않는다.

### Skills

Project-local Skills는 현재 다음 위치에 있다.

```text
.agents/skills/
```

Rulesync의 `copilot` project skill location은 `.github/skills/`이므로 `.agents/skills/`를
Copilot native source로 간주하지 않는다. portable Skill 배포 또는 별도 canonical
workflow가 필요하면 그 범위를 명시적으로 다룬다.

## Typical Conversion

예를 들어 Copilot rules와 subagents를 Claude Code, Codex CLI와 Antigravity IDE로
port할 때:

```bash
rulesync convert \
  --from copilot \
  --to claudecode,codexcli,antigravity-ide \
  --features rules,subagents \
  --dry-run
```

preview가 source inventory와 requested target에 맞으면 같은 command에서 `--dry-run`만
제거해 실행한다.

## Project Boundary

- `.github/`의 Copilot source asset을 conversion의 side effect로 수정하지 않는다.
- generated target은 source가 아니다. target-specific fix가 필요하면 먼저 source 또는
  backend compatibility gap인지 판단한다.
- `.agents/skills/`의 기존 project Skill은 이 workflow가 자동으로 재배치하지 않는다.
- broad `--features "*"`보다 실제 source가 있는 feature를 우선한다.
