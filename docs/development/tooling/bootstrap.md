---
title: "Bootstrap"
description: "Repository clone 이후 setup, 작업 session 준비와 intentional tooling update를 scripts/bootstrap.py 하나의 entrypoint로 사용하는 방법을 설명합니다."
categories:
  - software-engineering
tags:
  - bootstrap
  - tooling
---

# Bootstrap

Repository bootstrap은 [`scripts/bootstrap.py`](../../../scripts/bootstrap.py)가 소유한다. **처음에는 `setup`, 평소에는 `session`, external tooling을 의도적으로 갱신할 때만 `update`**를 사용한다.

## Commands

| Action | Use when | Repository behavior |
| --- | --- | --- |
| `setup` | clone 후 최초 환경 준비 | locked dependency 복원, Git hook 설치, Agent Asset 복원, local Node tool 준비, OpenSpec integration refresh |
| `session` | 일반적인 작업 시작 | locked dependency와 Agent Asset 복원, local Node tool 존재 확인 |
| `update` | external tooling source를 의도적으로 갱신할 때 | Agent Asset source와 OpenSpec integration refresh, repository-local Node tool 재설치 |

```bash
uv run --no-sync python scripts/bootstrap.py setup
uv run --no-sync python scripts/bootstrap.py session
uv run --no-sync python scripts/bootstrap.py update
```

`update`는 `setup`이나 `session`의 상위집합이 아니다. Python dependency sync와 Git hook 설치를 수행하지 않으므로 dependency restore가 필요하면 `session`, clone 직후 전체 준비가 필요하면 `setup`을 별도로 사용한다.

## Repository-specific Behavior

- Python dependency는 `uv sync --locked`로 현재 lock 상태를 복원한다.
- Agent Asset은 [`scripts/agent_assets.py`](../../../scripts/agent_assets.py)를 통해 복원하거나 갱신한다. Rulesync와 Skills CLI의 역할은 [Rulesync](rulesync.md)가 설명한다.
- Biome과 Tombi는 `.local/tooling` 아래 repository-local Node tool로 준비한다. 직접 binary path에 의존하지 않고 [Formatting](formatting.md)의 repository wrapper를 사용한다.
- OpenSpec은 project dependency로 고정 설치하지 않고 `npm exec` 기반 `openspec update`로 integration을 갱신한다. 자세한 repository 경계는 [OpenSpec](openspec.md)을 따른다.
- `update`는 Python dependency lock을 올리지 않는다. Python dependency 변경은 별도의 dependency change로 다룬다.

## Update Boundary

`update`는 session restore가 아니라 **external source와 tooling state를 새 revision으로 전진시키는 작업**이다. `rulesync.lock`, `skills-lock.json`이 존재하는 경우의 Skills CLI lock, generated Agent Asset projection 또는 OpenSpec integration file처럼 tracked state가 바뀔 수 있으므로 실행 후 repository diff와 관련 validation을 확인한다.

Bootstrap action은 여러 tool step을 순서대로 실행하며 전체를 하나의 transaction으로 rollback하지 않는다. 중간 step이 실패하면 앞에서 성공한 step의 변경이 남을 수 있으므로 diff와 현재 state를 확인한 뒤 원인을 해결하고 다시 실행한다.

Routine 작업 시작에는 `session`을 사용하고, 단순히 환경을 복구하려는 이유로 `update`를 실행하지 않는다.

## Boundary

이 문서는 bootstrap entrypoint의 repository contract만 설명한다. `uv`, npm, OpenSpec, Rulesync 같은 tool의 일반 설치법이나 전체 option reference는 각 공식 문서를 따른다.

Tool별 repository usage는 [Tooling](README.md)에서 해당 guide를 선택한다.
