---
title: "Lefthook"
description: "이 repository의 Git hook 설치 경로와 lefthook.yml이 정의하는 pre-commit/pre-push 동작을 설명합니다."
categories:
  - software-engineering
tags:
  - git
  - lefthook
  - tooling
---

# Lefthook

Lefthook 자체의 설치 방법, configuration option과 command reference는 [Lefthook 공식 문서](https://lefthook.dev/)를 따른다. 이 repository에서는 [`lefthook.yml`](../../../lefthook.yml)이 hook 동작을 소유하고 [`scripts/bootstrap.py`](../../../scripts/bootstrap.py)의 `setup`이 hook 설치를 담당한다.

## Setup

Clone 이후 별도로 `lefthook install`을 기억해서 실행하지 않는다. Repository setup entrypoint를 사용한다.

```bash
uv run --no-sync python scripts/bootstrap.py setup
```

`session`과 `update`는 Git hook을 다시 설치하지 않는다.

## Repository Hooks

현재 hook의 상세 command와 glob은 [`lefthook.yml`](../../../lefthook.yml)을 canonical source로 확인한다. 사람이 알아야 할 동작은 다음 정도다.

| Hook | Repository behavior |
| --- | --- |
| `pre-commit` | staged JSON/JSONC, Markdown, Python, TOML을 각 repository formatter로 고치고 수정된 파일을 다시 stage |
| `pre-push` | 변경된 JSON/JSONC, Python, TOML을 검사하고 Python 변경에는 affected pytest, dbt SQL/YAML 변경에는 dbt test suite 실행 |

Hook 내부 command를 문서에 전체 복제하지 않는다. Formatter와 linter를 직접 실행해야 하면 [Formatting](formatting.md)의 repository command를 사용한다.

## Boundary

Lefthook은 빠른 local feedback을 제공하지만 repository validation 전체를 대체하지 않는다. Test 설계와 pytest 실행 기준은 [Testing Guide](../testing.md), Git/GitHub workflow는 [Version Control and GitHub](../vcs-git/README.md)가 소유한다.

Hook 동작을 변경하려면 일반 Lefthook 사용법보다 먼저 [`lefthook.yml`](../../../lefthook.yml)의 repository-specific 목적과 기존 command scope를 확인한다.
