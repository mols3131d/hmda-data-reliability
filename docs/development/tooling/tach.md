---
title: "Tach"
description: "이 repository에서 Tach가 소유하는 Python dependency boundary, configuration과 검증 경계를 설명합니다."
categories:
  - software-engineering
tags:
  - architecture
  - python
  - tooling
---

# Tach

Tach는 `src/hmda_reliability`의 Python dependency boundary를 실행 가능한 검증으로 유지하는 개발 도구다. 이 guide는 Tach 자체의 사용법이 아니라 **이 repository에서 무엇을 검증하고, 어떤 source를 기준으로 설정하며, 어디까지를 Tach의 책임으로 보는지**를 소유한다.

## Upstream Reference

일반 설치 방법, 전체 command와 configuration reference, troubleshooting은 [Tach 공식 문서](https://docs.gauge.sh/)를 사용한다. CLI에서 현재 설치된 버전의 사용법을 확인할 때는 `uv run tach --help`와 `uv run tach <command> --help`를 사용한다.

이 문서는 upstream reference를 복제하지 않는다. Repository-specific decision과 operation만 아래에 기록한다.

## Repository Role

Tach는 architecture를 새로 정의하는 source of truth가 아니다. Canonical architecture와 domain ownership은 [`docs/ARCHITECTURE.md`](../../ARCHITECTURE.md), [`docs/domains/`](../../domains/)와 해당 OpenSpec Spec이 소유하고, `tach.toml`은 그중 Python import로 검증 가능한 dependency boundary를 실행 가능한 형태로 투영한다.

현재 import graph만 존재한다는 이유로 새로운 architecture rule을 만들지 않는다. Canonical contract에 없는 dependency restriction을 지속적으로 강제하려면 먼저 그 restriction을 소유할 문서 또는 Spec에서 의도를 명확히 한 뒤 Tach configuration에 반영한다.

Tach의 주된 역할은 다음과 같다.

- repository가 의도한 module dependency를 import 수준에서 검증한다.
- 명시적으로 금지된 dependency 방향의 재도입을 차단한다.
- 선택한 module coverage 밖의 Python source가 조용히 검증에서 빠지지 않게 한다.
- 의도하지 않은 circular dependency를 CI에서 차단한다.

## Ownership

| Concern | Owner |
| --- | --- |
| Architecture와 domain dependency 의도 | `docs/ARCHITECTURE.md`, `docs/domains/**`, applicable OpenSpec Spec |
| Executable Tach dependency projection | `tach.toml` |
| Python dependency와 Tach 설치 상태 | `pyproject.toml`, `uv.lock` |
| Repository-wide tool choice와 command entrypoint | `DEVELOPMENT.md` |
| CI 실행 조건과 검증 | `.github/workflows/**`, classifier와 관련 tests |
| Source-level AI forbidden-import guard | `tests/review_ai/test_dependency_boundaries.py` |

Policy와 executable configuration이 충돌하면 `tach.toml`을 임의로 완화해 현재 code를 통과시키지 않는다. 먼저 canonical architecture와 현재 source 중 어느 쪽이 변경되어야 하는지 판단한다.

## Module Coverage

Tach의 source root는 repository의 Python package layout과 일치해야 하며, `src/hmda_reliability` 아래에서 dependency boundary 대상으로 정한 source가 implicit root 처리나 `unchecked` 설정 때문에 조용히 빠져서는 안 된다.

Top-level domain package뿐 아니라 package root의 Python file도 coverage 결정에 포함한다. `root_module`은 Tach의 permissive default에 맡기지 않고 repository layout에 맞는 동작을 명시적으로 선택한다.

새 top-level package를 추가하거나 package-root Python surface를 변경하면 Tach coverage도 함께 검토한다. Package ownership 자체는 [`DEVELOPMENT.md`](../../../DEVELOPMENT.md)와 domain guide가 계속 소유한다.

## Dependency Policy

`depends_on`, `cannot_depend_on`, cycle policy 같은 Tach rule은 canonical architecture를 기계적으로 검증하기 위한 수단이다. 현재 import graph를 그대로 architecture truth로 승격하지 않는다.

특히 AI package의 source dependency 방향은 기존 architecture contract와 일치해야 한다.

- `review_ai`는 `reliability`와 `runtime_ai`를 사용할 수 있다.
- `reliability`는 `review_ai` 또는 `runtime_ai`에 의존하지 않는다.
- `runtime_ai`는 `review_ai` 또는 `reliability`에 의존하지 않는다.

Tach가 broader domain dependency allowlist를 관리하게 된다면 해당 allowlist가 repository architecture로 의도된 것인지 먼저 확인한다. 단순히 현재 code를 통과시키기 위한 permission을 추가하지 않는다.

Circular dependency 검증은 명시적으로 활성화한다. Exhaustive `depends_on` allowlist를 repository policy로 채택하는 경우에는 사용되지 않는 permission이 남아 drift를 숨기지 않도록 strictness도 함께 결정한다.

## Type-Only Imports

이 repository에는 `TYPE_CHECKING` 아래의 cross-domain import가 존재한다. 따라서 Tach의 type-checking import 처리는 단순 default가 아니라 검증 의미를 결정하는 repository policy다.

기존 `tests/review_ai/test_dependency_boundaries.py`는 AST를 사용해 Reliability와 AI package 사이의 source-level forbidden import를 검사하며 `TYPE_CHECKING` 내부 import도 포함한다. Tach를 도입한다고 이 guard를 자동으로 제거하거나 약화하지 않는다.

Tach가 runtime-oriented dependency graph를 검사하고 기존 AST test가 source-level AI boundary를 계속 소유하는 구성을 기본적인 역할 분리로 본다. 이 역할을 변경하려면 먼저 두 검증이 보장하는 범위가 동등하거나 더 강해지는지 확인하고 관련 test와 이 guide를 함께 갱신한다.

## Local And CI Validation

Repository에서 사용하는 기본 check entrypoint는 다음 형태다.

```bash
uv run --no-sync tach check
```

실제 command와 dependency 상태는 `pyproject.toml`, `uv.lock`과 `tach.toml`을 기준으로 확인한다. 일반적인 Tach command 설명은 upstream 문서를 따른다.

CI에서는 Python source 또는 Tach boundary의 의미를 바꿀 수 있는 configuration/dependency 변경이 architecture check를 우회해서는 안 된다. 최소한 다음 변경은 Tach 검증 경로를 다시 평가한다.

- `src/**/*.py`
- `tach.toml`
- `pyproject.toml`
- `uv.lock`

특히 `tach.toml`만 변경된 경우에도 필요한 Python/uv 준비와 dependency sync 뒤 `tach check`가 실행되어야 한다. Classifier를 사용하는 경우 이 경로는 regression test로 고정한다.

Local Git hook에 Tach feedback을 추가할 때는 Tach 자체 hook installer보다 repository-owned `lefthook.yml`을 사용한다. Hook은 CI의 대체물이 아니라 빠른 local feedback 경로다.

## Change Rule

Tach 관련 변경은 다음 순서로 판단한다.

1. 변경하려는 dependency rule의 canonical architecture owner를 확인한다.
1. 현재 source가 그 contract를 만족하는지 확인한다.
1. `tach.toml`을 최소한으로 변경한다.
1. `tach check`와 영향받은 architecture test를 실행한다.
1. CI classifier나 execution surface가 바뀌면 해당 regression test를 함께 갱신한다.
1. Repository-specific operating rule이 달라졌다면 이 guide를 갱신한다.

`uv.lock`은 직접 편집하지 않는다. Tach version과 dependency 변경은 repository의 `uv` workflow로 갱신한다.

## Non-Goals

이 guide와 Tach configuration은 다음을 소유하지 않는다.

- Tach 자체의 설치 tutorial, 전체 CLI reference 또는 일반 troubleshooting
- Python public API 또는 interface 설계 전체
- domain capability의 behavioral contract
- dbt model lineage나 Airflow DAG dependency
- 현재 import graph를 근거 없이 새로운 canonical architecture로 만드는 작업

이 범위를 넘어서는 정보는 upstream Tach 문서나 해당 repository owner로 이동한다.
