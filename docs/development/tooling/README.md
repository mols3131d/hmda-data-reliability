---
title: "Tooling"
description: "Repository 개발·검증·유지보수 workflow를 지원하는 도구의 project-specific usage, owning source와 managed state를 연결하는 entrypoint입니다."
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
- 자주 바뀌는 exact version과 tool 내부 command/glob은 owning source를 우선하고, 사람이 반복해서 알아야 하는 안정적인 의도만 문서에 요약한다.
- Lock과 generated output은 관리되는 state 또는 projection이지 정책 owner가 아니다. 직접 편집하지 않고 해당 repository workflow로 갱신한다.

## Boundary

`tooling`에는 OpenSpec, Rulesync, Skills CLI, Lefthook, formatter/linter와 repository bootstrap처럼 개발 workflow를 보조하는 도구가 들어간다.

Application 또는 runtime을 구성하는 기술 스택은 이 directory의 소유 범위가 아니다. 예를 들어 DuckDB, dbt, Apache Airflow, LangGraph와 application SDK는 [`DEVELOPMENT.md`](../../../DEVELOPMENT.md), [`ARCHITECTURE.md`](../../ARCHITECTURE.md)와 domain guide의 owning boundary를 따른다.

## Deferred Dependency Audit

현재 MVP 개발 중에는 dependency vulnerability audit를 CI나 Lefthook에 도입하지 않는다. 현재 [`MVP`](../../mvp.md)의 acceptance가 완료되어 이 개발 단계가 종료되면, locked dependency graph의 알려진 취약점을 검증하는 자동화된 audit를 도입한다.

도입 시점에는 당시의 공식 문서와 tool stability를 다시 확인하되, Python dependency authority가 `uv`와 `uv.lock`으로 유지된다면 `uv audit`을 기본 후보로 사용한다. PR에서는 `pyproject.toml` 또는 `uv.lock` 변경에 대해 blocking audit을 수행하고, dependency file 변경 없이 새 advisory가 공개되는 경우도 탐지할 수 있도록 scheduled audit을 별도로 둔다.

`uv audit`의 stability나 governance가 이 용도에 충분하지 않거나 Python 외 ecosystem, PR base/head vulnerability diff, richer suppression lifecycle 같은 요구가 실제로 생기면 OSV-Scanner를 대안으로 평가한다. 이 trigger 전에는 audit workflow, ignore policy 또는 별도 scanner configuration을 repository에 추가하지 않는다.

## Guides

| Guide | Repository-specific responsibility |
| --- | --- |
| [Bootstrap](bootstrap.md) | clone 이후 setup, session 준비와 intentional external tooling update entrypoint |
| [OpenSpec](openspec.md) | 이 repository의 OpenSpec integration과 project configuration 경로 |
| [Rulesync](rulesync.md) | Rulesync source sync·projection과 Skills CLI 보조 실행 경로 |
| [Lefthook](lefthook.md) | Git hook 설치, current behavior와 pre-commit/pre-push 운영 baseline |
| [Formatting](formatting.md) | Ruff, rumdl, Biome, Tombi의 repository-owned fix/check 경로와 configuration |
| [Tach](tach.md) | Python dependency boundary의 repository-specific ownership, coverage와 검증 경계 |

## Repository Surfaces

| Concern | Surface | Role |
| --- | --- | --- |
| setup / session / tooling update | [`scripts/bootstrap.py`](../../../scripts/bootstrap.py) | repository bootstrap workflow owner |
| OpenSpec project configuration | [`openspec/config.yaml`](../../../openspec/config.yaml) | repository-specific schema와 context/rule owner |
| Rulesync source intent | [`rulesync.jsonc`](../../../rulesync.jsonc) | target과 external source declaration |
| Rulesync resolved source state | [`rulesync.lock`](../../../rulesync.lock) | tool-managed lock; 직접 편집하지 않음 |
| Agent Asset operation | [`scripts/agent_assets.py`](../../../scripts/agent_assets.py), [`scripts/rulesync.py`](../../../scripts/rulesync.py) | restore, update, projection과 route orchestration |
| Git hooks | [`lefthook.yml`](../../../lefthook.yml) | hook behavior owner |
| Python formatter/linter | [`pyproject.toml`](../../../pyproject.toml) | Ruff configuration owner |
| Markdown formatter/linter | [`.rumdl.toml`](../../../.rumdl.toml) | rumdl configuration owner |
| repository-local Biome / Tombi execution | [`scripts/biome.py`](../../../scripts/biome.py), [`scripts/tombi.py`](../../../scripts/tombi.py) | local Node tool wrapper |
| docs index projection | [`scripts/generate_docs_indexes.py`](../../../scripts/generate_docs_indexes.py) | `docs/**/INDEX.tsv` generator; generated index는 직접 편집하지 않음 |

Skills CLI의 optional project lock은 `skills-lock.json`이 존재할 때만 사용하는 tool-managed state다. Agent instruction surface와 Rule/Skill asset management policy는 [AI Agent](../ai-agent/README.md)가 소유한다. 이 directory는 해당 정책을 반복하지 않고 도구의 repository-specific operation만 설명한다.
