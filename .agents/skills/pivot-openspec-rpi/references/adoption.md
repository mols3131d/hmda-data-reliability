# Adoption

`.agents/skills/pivot-openspec-rpi/`가 canonical source다. repository는 `SKILL.md`, reference, template, script, test를 포함한 directory 전체를 Git으로 추적한다.

## GitHub Copilot in VS Code

Copilot은 repository의 `.agents/skills/pivot-openspec-rpi`를 직접 발견한다. 별도 link나 설치 step은 필요하지 않다. VS Code의 **Chat: Open Customizations** 또는 `/skills`로 discovery를 확인한다.

## OpenAI Codex

canonical skill directory를 Codex user skill 위치에 설치한다.

### Codex Windows PowerShell

```powershell
New-Item -ItemType Directory -Force "$HOME\.codex\skills" | Out-Null
New-Item `
  -ItemType Junction `
  -Path "$HOME\.codex\skills\pivot-openspec-rpi" `
  -Target (Resolve-Path .\.agents\skills\pivot-openspec-rpi)
```

### Codex WSL Ubuntu

```bash
mkdir -p ~/.codex/skills
ln -sfn "$(pwd)/.agents/skills/pivot-openspec-rpi" ~/.codex/skills/pivot-openspec-rpi
```

설치 후 agent를 reload 또는 restart한다. skill에는 template·reference·script가 포함되므로 directory link를 사용한다.

## OpenSpec

ROR는 custom OpenSpec schema를 요구하지 않는다. project에 설치된 OpenSpec workflow를 사용한다. decorator artifact의 경로, 생성 시점, Git 추적과 보관 규칙은 [Artifacts](artifacts.md)를 따른다.

첫 artifact를 작성할 때만 필요한 directory를 만든다.
Front Matter CMS를 사용하는 project에서는 ROR artifact를 `openspec-rpi` content
type으로 등록하고 Research와 Review의 status, related artifact, tags를 front matter에 저장할 수 있다.

## Validation

repository root에서 실행한다.

```powershell
python .agents/skills/pivot-openspec-rpi/scripts/validate.py .agents/skills/pivot-openspec-rpi
```

WSL에서도 동일하다.

```bash
python3 .agents/skills/pivot-openspec-rpi/scripts/validate.py .agents/skills/pivot-openspec-rpi
```
