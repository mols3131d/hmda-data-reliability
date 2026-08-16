# Rulesync Backend

이 reference는 exact CLI surface나 target identifier가 필요할 때만 읽는다. installed
Rulesync가 최종 authority다. 먼저 `rulesync --version`과 해당 command의 `--help`를
확인한다.

## Core Commands

Canonical source에서 여러 target을 생성한다.

```bash
rulesync generate --dry-run --targets <targets> --features <features>
rulesync generate --targets <targets> --features <features>
rulesync generate --check --targets <targets> --features <features>
```

한 native harness에서 다른 harness로 직접 변환한다. 이 경로는 `.rulesync/`를 쓰지
않는다.

```bash
rulesync convert --from <source> --to <targets> \
  --features <features> --dry-run
rulesync convert --from <source> --to <targets> \
  --features <features>
```

Rulesync canonical source를 점검할 때는 필요에 따라 다음을 사용한다.

```bash
rulesync doctor
rulesync doctor --strict
```

## Features

현재 Rulesync의 주요 feature vocabulary는 다음과 같다.

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

`ignore`는 deprecated compatibility feature다. 새 workflow에서는 `permissions`를
우선한다.

변환 범위가 명확하면 `--features "*"`보다 필요한 feature를 명시한다. broad fan-out이
요구사항일 때만 `*`를 사용한다.

## Common Targets

자주 쓰는 target identifier:

| Harness | Rulesync target |
| --- | --- |
| GitHub Copilot | `copilot` |
| Claude Code | `claudecode` |
| Codex CLI | `codexcli` |
| Google Antigravity IDE | `antigravity-ide` |
| Google Antigravity CLI | `antigravity-cli` |

지원 target과 feature matrix는 Rulesync release에 따라 바뀔 수 있다. 이 표에 없는
harness를 추측해서 identifier를 만들지 않는다.

## Source Discovery

Native bridge는 Rulesync가 source harness의 native locations에서 발견한 asset만
변환한다. project가 editor setting이나 custom path로 asset location을 바꾼 경우,
그 위치가 Rulesync source adapter의 discovery contract에 포함되는지 확인한다.

발견되지 않는 custom location을 임의 copy해서 native source인 것처럼 위장하지 않는다.
필요하면 다음 중 하나를 명시적으로 선택한다.

1. native location으로 normalize한다.
2. canonical Rulesync source로 import한다.
3. backend limitation으로 보고한다.

## Validation

Canonical fan-out은 generation 뒤 같은 scope로 `generate --check`를 사용할 수 있다.

Native `convert`에는 `generate --check`와 같은 post-conversion check를 가정하지 않는다.
preview, generated diff, target format validation과 project-owned checks로 검증한다.

Rulesync warning이나 target에서 표현되지 않은 semantic이 있으면 conversion 성공과
semantic parity를 구분해서 보고한다.

## Safety

- `--dry-run`을 write 전에 실행한다.
- source harness를 `--to`에 포함하지 않는다.
- `--global`은 user-scope mutation이 명시된 경우에만 사용한다.
- plugin packaging target은 ordinary `convert` 대상으로 가정하지 않는다.
- install, update, cleanup은 asset conversion과 별도 mutation으로 취급한다.
