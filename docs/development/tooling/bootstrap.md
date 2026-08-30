---
title: "Bootstrap"
description: "Repository clone 이후 setup, 작업 session 준비와 external tooling update를 scripts/bootstrap.py 하나의 entrypoint로 사용하는 방법을 설명합니다."
categories:
  - software-engineering
tags:
  - bootstrap
  - tooling
---

# Bootstrap

Repository bootstrap은 [`scripts/bootstrap.py`](../../../scripts/bootstrap.py)가 소유한다. 개별 tool을 따로 설치하거나 동기화하기보다 목적에 맞는 action 하나를 실행한다.

## Commands

| Action | Use when | Repository behavior |
| --- | --- | --- |
| `setup` | clone 후 최초 환경 준비 | locked Python dependency sync, Git hook 설치, Agent Asset 복원, local Node tool 준비, OpenSpec integration update |
| `session` | 일반적인 작업 시작 | locked Python dependency sync, Agent Asset 복원, local Node tool 존재 확인 |
| `update` | external tooling source를 갱신할 때 | Agent Asset source update, OpenSpec integration update, repository-local Node tool 재설치 |

```bash
uv run --no-sync python scripts/bootstrap.py setup
uv run --no-sync python scripts/bootstrap.py session
uv run --no-sync python scripts/bootstrap.py update
```

평소 작업 시작에는 `session`을 사용한다. `setup`은 Git hook과 OpenSpec setup까지 포함하므로 매 session마다 반복할 필요가 없다.

## Repository-specific Behavior

- Python dependency는 `uv sync --locked`로 현재 lock 상태를 복원한다.
- Agent Asset은 [`scripts/agent_assets.py`](../../../scripts/agent_assets.py)를 통해 Rulesync와 Skills CLI 상태를 복원하거나 갱신한다.
- Biome과 Tombi는 `.local/tooling` 아래 repository-local Node tool로 관리한다. 직접 해당 경로의 binary를 호출하지 않고 repository wrapper를 사용한다.
- OpenSpec은 project dependency로 설치하지 않고 `npm exec`를 통해 integration update를 수행한다.
- `update`는 Python dependency lock을 올리지 않는다. Python dependency 변경은 별도의 dependency change로 다룬다.

## Boundary

이 문서는 bootstrap entrypoint의 **repository contract**만 설명한다. `uv`, npm, OpenSpec, Rulesync 같은 tool의 일반 설치법이나 전체 option reference는 각 공식 문서를 따른다.

Tool별 repository usage는 [Tooling](README.md)에서 해당 guide를 선택한다.
