---
title: "Lefthook"
description: "이 repository의 Git hook 설치 경로와 pre-commit/pre-push가 지켜야 할 운영 baseline을 설명합니다."
categories:
  - software-engineering
tags:
  - git
  - lefthook
  - tooling
---

# Lefthook

Lefthook 자체의 설치 방법, configuration option과 command reference는 [Lefthook 공식 문서](https://lefthook.dev/)를 따른다. 이 repository에서는 [`lefthook.yml`](../../../lefthook.yml)이 hook 동작을 소유하고 [`scripts/bootstrap.py`](../../../scripts/bootstrap.py)의 `setup`이 hook 설치를 담당한다.

Git hook은 local Git runtime을 사용할 수 있는 기여자에게 빠른 feedback을 주는 local guard다. 모든 기여 환경이 hook을 실행할 수 있다고 가정하지 않는다. Hook을 확장할 때는 검사 수를 늘리는 것보다 **commit과 push 시점에 필요한 최소 품질 경계를 낮은 마찰로 유지하는 것**을 우선한다.

## Setup

Clone 이후 별도로 `lefthook install`을 기억해서 실행하지 않는다. Repository setup entrypoint를 사용한다.

```bash
uv run --no-sync python scripts/bootstrap.py setup
```

`session`과 `update`는 Git hook을 다시 설치하지 않는다.

## Baseline

### Pre-commit

Pre-commit은 **commit에 들어가는 파일을 빠르게 정리하고 즉시 고칠 수 있는 문제를 차단하는 단계**다.

- staged change에 직접 관련된 검사만 수행한다.
- formatting, lint autofix처럼 빠르고 결정론적이며 안전하게 자동 수정할 수 있는 작업을 우선한다.
- 자동 수정한 파일은 commit에 실제 반영되도록 다시 stage한다.
- 긴 test suite, network 의존 작업, dependency/tool update처럼 commit마다 반복하기 비싼 작업은 두지 않는다.
- repository state를 예측하기 어렵게 바꾸는 작업이나 unrelated file까지 수정하는 작업은 피한다.

### Pre-push

Pre-push는 **원격 branch와 CI에 변경을 보내기 전에 relevant correctness를 확인하는 단계**다.

- push되는 변경의 영향 범위에 맞춰 lint, format check와 test를 선택한다.
- pre-commit보다 강한 검증을 허용하지만, 가능한 한 affected scope만 실행해 feedback 시간을 제한한다.
- 검증 단계에서는 source를 자동 수정하거나 stage하지 않는다. 실패하면 원인을 확인하고 명시적으로 수정한 뒤 다시 push한다.
- shared cache나 generated state를 쓰는 검사는 병렬 실행하지 않는다.
- full CI, 고비용 integration/stress 검증 또는 외부 service에 강하게 의존하는 검사를 무조건 복제하지 않는다.
- push되는 변경과 관련된 필수 검증이 실패하면 push를 차단한다.

Hook bypass는 정상 workflow가 아니라 예외적인 escape hatch다. 환경 문제 등으로 hook을 우회하더라도 해당 commit/push를 validated state로 간주하지 않고, 필요한 repository validation을 별도로 수행한다.

## Repository Hooks

현재 hook의 상세 command와 glob은 [`lefthook.yml`](../../../lefthook.yml)을 canonical source로 확인한다. 사람이 알아야 할 동작은 다음 정도다.

| Hook | Repository behavior |
| --- | --- |
| `pre-commit` | staged JSON/JSONC, Markdown, Python, TOML을 각 repository formatter로 고치고 수정된 파일을 다시 stage |
| `pre-push` | 변경된 JSON/JSONC, Python, TOML을 검사하고 Python 변경에는 affected pytest, dbt SQL/YAML 변경에는 dbt test suite 실행 |

Hook 내부 command를 문서에 전체 복제하지 않는다. Formatter와 linter를 직접 실행해야 하면 [Formatting](formatting.md)의 repository command를 사용한다.

## Boundary

Lefthook은 local runtime이 있는 환경의 빠른 feedback과 자동 수정을 최적화하지만 repository validation 전체를 대체하지 않는다. Hook을 사용할 수 없는 기여자에게 hook 실행을 필수 기여 절차로 요구하지 않는다.

Hook 통과는 CI 또는 matching revision의 validation evidence를 대신하지 않는다. 반대로 hook을 실행할 수 없다는 이유만으로 병합 필수 검증이 빠져서는 안 되며, 해당 책임은 [Continuous Integration](../ci.md)의 admission boundary를 따른다.

Test 설계와 pytest 실행 기준은 [Testing Guide](../testing.md), Git/GitHub workflow는 [Version Control and GitHub](../vcs-git/README.md)가 소유한다.

Hook 동작을 변경할 때는 이 baseline과 [`lefthook.yml`](../../../lefthook.yml)의 current scope를 함께 확인한다. 새로운 검사는 해당 Git 시점에 반복해서 실행할 가치가 있고 개발 흐름의 마찰보다 예방 효과가 클 때만 추가한다.
