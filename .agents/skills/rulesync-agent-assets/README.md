# Rulesync Agent Assets

여러 coding-agent harness의 agent customization asset을 **하나의 source에서 유지하거나,
한 harness의 native asset을 다른 harness로 이식해야 할 때** 호출하는 Skill이다.

호출자는 변환 방법이나 Rulesync 명령을 알 필요가 없다. 어떤 source를 보존할지와 어떤
target이 필요한지만 전달하면 된다.

## Call This Skill When

다음과 같은 결과가 필요할 때 호출한다.

- 하나의 Rulesync canonical source에서 여러 harness용 asset을 생성한다.
- Copilot, Claude Code, Codex CLI, Antigravity 등 한 harness의 native asset을 다른
  harness로 이식한다.
- 여러 harness의 agent customization asset을 같은 source authority에 맞춰 동기화한다.
- 변환 전후에 어떤 기능이 보존되고 어떤 기능이 손실·근사·simulation되는지 확인한다.
- 기존 portable asset을 변환 없이 그대로 재사용할 수 있는지도 함께 판단한다.

단일 harness 안에서 파일 하나만 수정하면 되는 작업에는 이 Skill이 필요하지 않다.

## What To Tell It

가능하면 다음 정보를 제공한다.

| Information | Meaning |
| --- | --- |
| Source | 어떤 asset 또는 harness가 authoritative한가 |
| Targets | 어떤 harness에서 사용할 결과가 필요한가 |
| Asset scope | rules, agents, skills, hooks 등 무엇을 옮길 것인가 |
| Scope | project-local인지 user-global까지 필요한지 |
| Constraints | source를 유지해야 하는지, simulation을 허용하는지 등 |

모든 항목을 반드시 명시할 필요는 없다. Repository가 source preference나 project scope를
이미 정의하면 Skill은 그 policy를 따른다. Source authority가 실제로 모호한 경우에는
임의로 결정하지 않는다.

### Project Pivot Default

Project Pivot에서 source를 따로 지정하지 않은 cross-harness port는 **GitHub Copilot
native assets를 source**로 해석한다. Canonical Rulesync source를 사용하거나 다른 harness를
source로 유지하려면 호출에서 명시한다.

## Typical Calls

Canonical source에서 여러 harness로 배포:

```text
이 Rulesync 자산을 Copilot, Codex, Claude Code, Antigravity용으로 동기화해줘.
```

Project Pivot의 Copilot 자산을 source로 유지하면서 다른 harness로 이식:

```text
현재 Copilot rules와 agents를 source로 유지하고 Codex와 Claude Code용 자산을 만들어줘.
```

특정 asset만 제한해서 이식:

```text
Copilot rules만 Antigravity로 옮겨줘. Skills나 hooks는 건드리지 마.
```

호환성 확인까지 요청:

```text
현재 Copilot 설정을 Codex와 Antigravity로 옮길 때 의미가 손실되는 부분도 같이 확인해줘.
```

## What The Skill Decides

호출 의도와 repository policy 안에서 다음을 판단한다.

- 기존 source를 target이 그대로 읽을 수 있는지
- canonical fan-out과 native bridge 중 어떤 route가 맞는지
- 요청을 만족하는 최소 target과 asset 범위
- Rulesync가 실제 source를 발견하는지
- 변환 결과에 compatibility gap이 있는지
- 어떤 validation evidence가 필요한지

Rulesync의 parsing, mapping과 target file generation은 backend에 위임한다.

## What The Skill Does Not Decide

다음은 caller 또는 repository가 소유한다.

- 어떤 source가 장기적인 source of truth가 되어야 하는지
- repository architecture를 `.rulesync/` 중심으로 migration할지 여부
- source asset의 위치나 naming convention을 바꿀지 여부
- user-global configuration을 변경할지 여부
- simulation이나 의미 손실을 제품 수준에서 허용할지 여부

이 Skill은 변환 편의를 위해 이러한 결정을 암묵적으로 수행하지 않는다.

## Result

호출이 끝나면 최소한 다음을 구분할 수 있어야 한다.

```text
mode        어떤 route를 사용했는가
source      무엇을 authoritative source로 유지했는가
targets     어떤 harness를 대상으로 했는가
features    어떤 asset category를 다뤘는가
generated   실제 생성된 결과는 무엇인가
gaps        발견된 compatibility gap은 무엇인가
validation  실제로 무엇을 검증했는가
```

`generated`가 성공했다고 해서 모든 harness에서 의미가 완전히 같다는 뜻은 아니다.
지원되지 않거나 근사·simulation된 동작은 별도 gap으로 보고되는 것이 이 Skill의 계약이다.

## Requirements

이 Skill을 통한 실제 변환에는 Rulesync CLI와 해당 Rulesync version이 지원하는 source/target
harness가 필요하다. 설치된 version에 따라 target, discovery path와 feature support가 달라질
수 있다.

Skill은 일반 변환 작업의 부수 효과로 Rulesync를 설치·upgrade하지 않는다.
