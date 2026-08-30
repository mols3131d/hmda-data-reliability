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

일반적인 설치 방법, 전체 CLI reference와 tool 자체의 기능 설명은 가능한 한 공식 문서에 맡긴다. 여기에는 이 repository에서 선택한 사용 방식, wrapper, configuration, entrypoint와 주의사항처럼 **이 repository에 한정된 내용**만 기록한다.

## Boundary

`tooling`에는 OpenSpec, Rulesync, Skills CLI, Lefthook, formatter/linter와 repository bootstrap처럼 개발 workflow를 보조하는 도구가 들어간다.

DuckDB, dbt, Apache Airflow, Polars, PyArrow, Pydantic, LangGraph, OpenAI SDK처럼 application 또는 runtime을 구성하는 기술은 이 directory의 소유 범위가 아니다. Active tool choice와 기술 스택은 [`DEVELOPMENT.md`](../../../DEVELOPMENT.md), 시스템 구조와 runtime boundary는 [`ARCHITECTURE.md`](../../ARCHITECTURE.md)와 domain guide를 따른다.

## Guides

| Guide | Repository-specific responsibility |
| --- | --- |
| [Bootstrap](bootstrap.md) | clone 이후 setup, session 준비와 external tooling update entrypoint |
| [OpenSpec](openspec.md) | 이 repository의 OpenSpec integration, config와 contract boundary |
| [Rulesync](rulesync.md) | Agent Asset 관리의 Rulesync-first 경로와 Skills CLI 보조 연동 |
| [Lefthook](lefthook.md) | Git hook 설치, current behavior와 pre-commit/pre-push 운영 baseline |
| [Formatting](formatting.md) | Ruff, rumdl, Biome, Tombi의 repository-owned 실행 경로와 configuration |

## Owning Sources

| Concern | Owning source |
| --- | --- |
| setup / session / tooling update | [`scripts/bootstrap.py`](../../../scripts/bootstrap.py) |
| OpenSpec project configuration | [`openspec/config.yaml`](../../../openspec/config.yaml) |
| Rulesync targets and external sources | [`rulesync.jsonc`](../../../rulesync.jsonc) |
| Agent Asset synchronization | [`scripts/agent_assets.py`](../../../scripts/agent_assets.py), [`scripts/rulesync.py`](../../../scripts/rulesync.py) |
| Git hooks | [`lefthook.yml`](../../../lefthook.yml) |
| Python formatter/linter | [`pyproject.toml`](../../../pyproject.toml) |
| Markdown formatter/linter | [`.rumdl.toml`](../../../.rumdl.toml) |
| repository-local Biome / Tombi execution | [`scripts/biome.py`](../../../scripts/biome.py), [`scripts/tombi.py`](../../../scripts/tombi.py) |

Agent instruction surface와 Rule/Skill asset management policy는 [AI Agent](../ai-agent/README.md)가 소유한다. 이 directory는 해당 정책을 반복하지 않고 도구의 repository-specific operation만 설명한다.
