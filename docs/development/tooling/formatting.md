---
title: "Formatting"
description: "이 repository에서 Python, Markdown, JSON/JSONC, TOML을 formatting·linting할 때 사용하는 tool과 repository-owned command를 정리합니다."
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

Formatter와 linter의 일반 option과 기능 설명은 각 공식 문서를 따른다. 이 문서는 **이 repository에서 어떤 file type에 어떤 tool과 entrypoint를 쓰는지**만 정리한다.

## Repository Commands

| File type | Tool | Common command | Repository configuration |
| --- | --- | --- | --- |
| Python | Ruff | `uv run ruff check src tests`, `uv run ruff format .` | [`pyproject.toml`](../../../pyproject.toml) |
| Markdown | rumdl | `uv run rumdl fmt .` | [`.rumdl.toml`](../../../.rumdl.toml) |
| JSON / JSONC | Biome | `uv run python scripts/biome.py format --write --files-ignore-unknown=true .` | repository-local Biome 2 channel + wrapper |
| TOML | Tombi | `uv run python scripts/tombi.py format .`, `uv run python scripts/tombi.py lint .` | repository-local Tombi 1 channel + wrapper |

Biome과 Tombi는 [`scripts/bootstrap.py`](../../../scripts/bootstrap.py)가 `.local/tooling` 아래에 준비한다. 직접 `.local/tooling`의 binary path에 의존하지 말고 [`scripts/biome.py`](../../../scripts/biome.py)와 [`scripts/tombi.py`](../../../scripts/tombi.py) wrapper를 사용한다.

Python과 Markdown tool version/configuration은 각각 [`pyproject.toml`](../../../pyproject.toml)과 [`.rumdl.toml`](../../../.rumdl.toml)이 소유한다. 이 문서에 version number나 전체 rule set을 복제하지 않는다.

## Git Hooks

[`lefthook.yml`](../../../lefthook.yml)은 staged file에 대해 repository formatter를 자동 실행하고 일부 file type은 push 전에 check를 수행한다. Hook 동작 자체는 [Lefthook](lefthook.md)을 참고한다.

수동 formatting이 필요한 경우에도 hook command를 복사하기보다 위 표의 repository entrypoint를 사용한다.

## Official Documentation

- [Ruff](https://docs.astral.sh/ruff/)
- [rumdl](https://github.com/rvben/rumdl)
- [Biome](https://biomejs.dev/)
- [Tombi](https://tombi-toml.github.io/tombi/)

새 option, editor integration, formatter behavior와 tool-specific troubleshooting은 이 문서에 추가하기 전에 공식 문서로 해결할 수 있는지 먼저 확인한다. Repository configuration이나 wrapper 때문에 달라지는 내용만 여기에 남긴다.
