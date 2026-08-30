---
title: "Tooling"
description: "Repository 개발·검증·유지보수 workflow를 지원하는 도구의 project-specific usage와 owning source를 연결하는 entrypoint입니다."
categories:
  - software-engineering
tags:
  - bootstrap
  - lefthook
  - openspec
  - rulesync
  - tooling
---

# Tooling

이 directory는 **제품을 구성하는 기술 스택이 아니라 repository의 개발·검증·유지보수 workflow를 지원하는 도구**만 다룬다.

## Documentation Rule

- 일반 설치 방법, 전체 CLI reference, tool 자체의 기능과 일반 troubleshooting은 공식 문서에 맡긴다.
- 이 repository에서 선택한 wrapper, configuration, entrypoint, ownership boundary와 예외만 local guide에 기록한다.
- 자주 바뀌는 exact version, tool 내부 command/glob과 generated state는 owning source를 우선하고, 사람이 반복해서 알아야 하는 안정적인 의도만 문서에 요약한다.

## Boundary

`tooling`에는 OpenSpec, Rulesync, Skills CLI, Lefthook, formatter/linter와 repository bootstrap처럼 개발 workflow를 보조하는 도구가 들어간다.

Application 또는 runtime을 구성하는 기술 스택은 이 directory의 소유 범위가 아니다. 예를 들어 DuckDB, dbt, Apache Airflow, LangGraph와 application SDK는 [`DEVELOPMENT.md`](../../../DEVELOPMENT.md), [`ARCHITECTURE.md`](../../ARCHITECTURE.md)와 domain guide의 owning boundary를 따른다.

## Guides

| Guide | Repository-specific responsibility |
| --- | --- |
| [Bootstrap](bootstrap.md) | clone 이후 setup, session 준비와 intentional external tooling update entrypoint |
| [OpenSpec](openspec.md) | 이 repository의 OpenSpec integration과 project configuration 경로 |
| [Rulesync](rulesync.md) | Rulesync source sync·projection과 Skills CLI 보조 실행 경로 |
| [Lefthook](lefthook.md) | Git hook 설치, current behavior와 pre-commit/pre-push 운영 baseline |
| [Formatting](formatting.md) | Ruff, rumdl, Biome, Tombi의 repository-owned fix/check 경로와 configuration |

## Owning Sources

| Concern | Owning source |
| --- | --- |
| setup / session / tooling update | [`scripts/bootstrap.py`](../../../scripts/bootstrap.py) |
| OpenSpec project configuration | [`openspec/config.yaml`](../../../openspec/config.yaml) |
| Rulesync targets and external sources | [`rulesync.jsonc`](../../../rulesync.jsonc) |
| Rulesync external source lock | [`rulesync.lock`](../../../rulesync.lock) |
| Agent Asset synchronization | [`scripts/agent_assets.py`](../../../scripts/agent_assets.py), [`scripts/rulesync.py`](../../../scripts/rulesync.py) |
| Git hooks | [`lefthook.yml`](../../../lefthook.yml) |
| Python formatter/linter | [`pyproject.toml`](../../../pyproject.toml) |
| Markdown formatter/linter | [`.rumdl.toml`](../../../.rumdl.toml) |
| repository-local Biome / Tombi execution | [`scripts/biome.py`](../../../scripts/biome.py), [`scripts/tombi.py`](../../../scripts/tombi.py) |

Skills CLI의 optional project lock은 `skills-lock.json`이 존재할 때만 사용한다. Agent instruction surface와 Rule/Skill asset management policy는 [AI Agent](../ai-agent/README.md)가 소유한다. 이 directory는 해당 정책을 반복하지 않고 도구의 repository-specific operation만 설명한다.
