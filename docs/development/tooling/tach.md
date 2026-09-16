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

Tach는 `src/hmda_reliability`의 Python dependency boundary를 실행 가능한 검증으로 유지하는 개발 도구다. 이 guide는 Tach 자체의 사용법이 아니라 이 repository에서 무엇을 검증하고, 어떤 source를 기준으로 설정하며, 어디까지를 Tach의 책임으로 보는지 설명한다.

## Upstream Reference

일반 설치 방법, 전체 command와 configuration reference, troubleshooting은 [Tach 공식 문서](https://docs.gauge.sh/)를 사용한다. CLI에서 현재 설치된 버전의 사용법을 확인할 때는 `uv run tach --help`와 `uv run tach <command> --help`를 사용한다.

이 문서는 upstream reference를 복제하지 않는다. Repository-specific decision과 operation만 아래에 기록한다.

## Activation

Tach는 dev dependency로 설치하며 `uv sync --locked`로 실행 환경을 준비한다. 설치 버전은 `uv.lock`, executable boundary는 `tach.toml`, 실행 entrypoint는 [`DEVELOPMENT.md`](../../../DEVELOPMENT.md)가 소유한다.

## Repository Role

Tach는 architecture를 새로 정의하는 source of truth가 아니다. Canonical architecture와 domain ownership은 [`docs/ARCHITECTURE.md`](../../ARCHITECTURE.md), [`docs/domains/`](../../domains/)와 해당 OpenSpec Spec이 소유하고, `tach.toml`은 그중 Python import로 검증 가능한 dependency boundary를 실행 가능한 형태로 투영한다.

현재 import graph만 존재한다는 이유로 새로운 architecture rule을 만들지 않는다. Canonical contract에 없는 dependency restriction을 지속적으로 강제하려면 먼저 그 restriction을 소유할 문서 또는 Spec에서 의도를 명확히 한 뒤 Tach configuration에 반영한다.

Tach의 주된 역할은 다음과 같다.

- repository가 명시한 module dependency boundary를 import 수준에서 검증한다.
- 금지된 dependency 방향의 재도입을 차단한다.
- dependency boundary 대상으로 정한 Python source가 조용히 검증에서 빠지지 않게 한다.

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

Source root는 `src`다. `hmda_reliability` module이 package root의 `__init__.py`, `logger.py`와 아직 별도 boundary가 없는 하위 source를 포함하고, 현재 top-level package는 개별 module로 선언한다.

`root_module = "forbid"`로 이 package 밖의 implicit root 참조를 거부한다. `exclude = []`, `respect_gitignore = false`로 source 제외를 막으며 `unchecked` module은 두지 않는다. Package root도 검사를 받지만 canonical contract에 없는 import 제한을 추가하지는 않는다.

새 top-level package를 추가하거나 package-root Python surface를 변경하면 Tach coverage도 함께 검토한다. Package ownership 자체는 [`DEVELOPMENT.md`](../../../DEVELOPMENT.md)와 domain guide가 계속 소유한다.

## Dependency Policy

`depends_on`, `cannot_depend_on`, cycle policy 같은 Tach rule은 canonical architecture를 기계적으로 검증하기 위한 수단이다. 현재 import graph를 그대로 architecture truth로 승격하지 않는다.

특히 AI package의 source dependency 방향은 기존 architecture contract와 일치해야 한다.

- `review_ai`는 `reliability`와 `runtime_ai`를 사용할 수 있다.
- `reliability`는 `review_ai` 또는 `runtime_ai`에 의존하지 않는다.
- `runtime_ai`는 `review_ai` 또는 `reliability`에 의존하지 않는다.

현재 code를 통과시키기 위해 모든 관찰된 import를 permission으로 복사하지 않는다. Canonical contract가 금지 방향만 정의한다면 Tach도 그 경계를 직접 표현하는 최소 rule을 우선한다.

현재 설정은 `reliability`와 `runtime_ai`의 네 금지 방향을 `cannot_depend_on`으로 표현한다. `depends_on`은 생략하고 `forbid_circular_dependencies = false`를 명시해 기존 계약 밖의 allowlist와 global no-cycle policy를 도입하지 않는다.

전체 domain dependency를 exhaustive `depends_on` allowlist로 관리하려면 그 graph가 먼저 repository architecture로 명시되어야 한다. 이 방식을 채택할 때는 사용되지 않는 permission이 남아 drift를 숨기지 않도록 `exact = true`도 함께 사용한다.

Global circular dependency prohibition도 architecture policy다. Tach가 기능을 제공한다는 이유만으로 자동 활성화하지 않고, repository가 no-cycle invariant를 명시적으로 채택한 경우에만 `forbid_circular_dependencies`로 투영한다.

## Type-Only Imports

이 repository에는 `TYPE_CHECKING` 아래의 cross-domain import가 존재한다. 기본 역할 분리에서는 Tach가 runtime-oriented dependency graph를 검사하도록 `ignore_type_checking_imports = true`를 사용한다.

기존 `tests/review_ai/test_dependency_boundaries.py`는 AST를 사용해 Reliability와 AI package 사이의 source-level forbidden import를 검사하며 `TYPE_CHECKING` 내부 import도 포함한다. Tach를 도입한다고 이 guard를 제거하거나 약화하지 않는다.

이 역할을 변경하려면 먼저 두 검증이 보장하는 범위가 동등하거나 더 강해지는지 확인하고 관련 architecture contract, test와 이 guide를 함께 갱신한다.

## Local And CI Validation

Tach가 활성화된 revision의 기본 local check entrypoint는 다음 형태다.

```bash
uv run --no-sync tach check
```

실제 command와 dependency 상태는 `pyproject.toml`, `uv.lock`과 `tach.toml`을 기준으로 확인한다. 일반적인 Tach command 설명은 upstream 문서를 따른다.

Python source, Tach configuration 또는 dependency state가 boundary 의미를 바꿀 수 있다면 PR CI에서 Tach 검증을 우회해서는 안 된다. Exact selector와 command routing은 [CI](../ci.md)의 ownership에 따라 `.github/workflows/**`, classifier와 관련 regression test가 소유한다.

`architecture` selector는 `src/**/*.py`, `tach.toml`, Python runtime/dependency state와 해당 CI/test 변경에서 dependency boundary step을 선택한다. `tach.toml` 단독 변경도 Python/uv setup과 locked dependency sync를 거친다. 이 step은 `tach check`, temporary project의 negative-path regression과 기존 AST guard를 함께 실행한다.

`tests/scripts/test_tach.py`는 네 금지 방향, 허용된 advisory/root import, type-only 제외와 implicit root 거부를 검사한다. Tach의 pytest 선택 기능(`--tach`)은 repository test selection에 도입하지 않는다.

Local Git hook에 Tach feedback을 추가할 때는 Tach 자체 hook installer보다 repository-owned `lefthook.yml`을 사용한다. Hook은 CI의 대체물이 아니라 빠른 local feedback 경로다.

Boundary rule을 새로 도입하거나 의미를 바꿀 때는 passing `tach check`만으로 설정 효과를 주장하지 않는다. 대표적인 금지 dependency가 실제로 실패하는지 deterministic test 또는 되돌릴 수 있는 negative control로 확인한다.

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
