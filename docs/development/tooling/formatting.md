---
title: "Formatting"
description: "이 repository에서 Python, Markdown, JSON/JSONC, TOML을 formatting·linting할 때 사용하는 fix/check command와 owning source를 정리합니다."
categories:
  - software-engineering
tags:
  - biome
  - formatting
  - ruff
  - rumdl
  - tombi
  - tooling
---

# Formatting

Formatter와 linter의 일반 option과 기능 설명은 각 공식 문서를 따른다. 이 문서는 **이 repository에서 어떤 file type에 어떤 tool, fix/check entrypoint와 configuration을 사용하는지**만 정리한다.

## Repository Commands

| File type | Fix | Check | Config / wrapper |
| --- | --- | --- | --- |
| Python | `uv run ruff check --fix <paths>` → `uv run ruff format <paths>` | `uv run ruff check <paths>` + `uv run ruff format --check <paths>` | [`pyproject.toml`](../../../pyproject.toml) |
| Markdown | `uv run rumdl fmt <paths>` | `uv run rumdl check <paths>` | [`.rumdl.toml`](../../../.rumdl.toml) |
| JSON / JSONC | `uv run python scripts/biome.py format --write <paths>` | `uv run python scripts/biome.py check <paths>` | [`scripts/biome.py`](../../../scripts/biome.py) |
| TOML | `uv run python scripts/tombi.py format <paths>` | `uv run python scripts/tombi.py format --check <paths>` + `uv run python scripts/tombi.py lint <paths>` | [`scripts/tombi.py`](../../../scripts/tombi.py) |

`<paths>`에는 가능한 한 필요한 file만 넘긴다. Directory나 `.`은 의도적으로 해당 tree 전체를 대상으로 할 때만 사용한다. Biome에는 JSON/JSONC file을 직접 넘기는 것을 기본으로 하고, repository 전체 JSON/JSONC formatting은 [`DEVELOPMENT.md`](../../../DEVELOPMENT.md)의 quick command를 사용한다.

Biome과 Tombi는 [`scripts/bootstrap.py`](../../../scripts/bootstrap.py)가 `.local/tooling` 아래에 준비한다. 직접 `.local/tooling`의 binary path에 의존하지 않고 repository wrapper를 사용한다.

Python과 Markdown configuration은 각각 [`pyproject.toml`](../../../pyproject.toml)과 [`.rumdl.toml`](../../../.rumdl.toml)이 소유한다. Biome/Tombi의 package channel과 invocation detail은 bootstrap script와 wrapper가 소유하므로 이 문서에 version number나 tool의 전체 rule set을 복제하지 않는다.

## Git Hooks And CI

[`lefthook.yml`](../../../lefthook.yml)은 local Git hook을 사용할 수 있는 환경에서 staged file에 fix를 적용하고 push 전에는 관련 file을 read-only로 검사한다. 세부 hook baseline은 [Lefthook](lefthook.md)을 따른다.

Local runtime을 사용할 수 있는 기여자는 위 fix/check command를 직접 사용할 수 있다. Local runtime을 사용할 수 없는 기여자에게 이 command 실행을 유일한 복구 경로로 요구하지 않는다. 병합에 필요한 검증과 실패 정보의 기준은 [Continuous Integration](../ci.md)을 따른다.

PR CI의 file selection과 validation scope는 [`.github/workflows/ci-lite.yml`](../../../.github/workflows/ci-lite.yml)이 소유한다. Hook 또는 CI command를 이 문서에 복제하지 않고, 수동 작업에는 위의 repository entrypoint를 사용한다.

## Official Documentation

- [Ruff](https://docs.astral.sh/ruff/)
- [rumdl](https://rumdl.dev/)
- [Biome](https://biomejs.dev/)
- [Tombi](https://tombi-toml.github.io/tombi/)

새 option, editor integration, formatter behavior와 tool-specific troubleshooting은 이 문서에 추가하기 전에 공식 문서로 해결할 수 있는지 먼저 확인한다. Repository configuration이나 wrapper 때문에 달라지는 내용만 여기에 남긴다.
