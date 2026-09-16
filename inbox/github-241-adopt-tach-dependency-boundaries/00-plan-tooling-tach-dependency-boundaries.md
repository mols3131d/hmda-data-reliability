---
type: plan
title: "Adopt Tach Dependency Boundaries"
description: "Tach 도입 범위, 검증 기준과 로컬 구현 핸드오프를 정리합니다."
tags:
  - python
  - tooling
  - architecture
---

# Adopt Tach Dependency Boundaries

Tach를 개발 도구로 도입해 `src/hmda_reliability`의 Python dependency boundary를 실행 가능한 검증으로 만든다. 이 변경은 새로운 architecture graph를 설계하는 작업이 아니라, 이미 문서화된 dependency constraint를 현재 source와 대조해 Tach rule로 투영하고 이후 drift를 차단하는 작업이다.

## Scope

- Tach를 dev dependency로 추가하고 `uv.lock`은 로컬 `uv` workflow로 갱신한다.
- `tach.toml`에서 `src` source root와 현재 top-level Python package를 module boundary로 정의한다. Package root의 Python surface도 검사 범위에서 빠지지 않게 하고 coverage에 영향을 주는 Tach default를 명시적으로 결정한다.
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)와 domain guide에 이미 명시된 dependency constraint를 Tach rule로 보존한다. 현재 import graph는 검증 대상과 구현 근거로 사용하되 새로운 architecture truth로 승격하지 않는다.
  - `review_ai`는 `reliability`, `runtime_ai`를 사용할 수 있다.
  - `reliability`는 `review_ai` 또는 `runtime_ai`에 의존하지 않는다.
  - `runtime_ai`는 `review_ai` 또는 `reliability`에 의존하지 않는다.
- 현재 canonical contract가 전체 domain allowlist를 소유하지 않으므로, 이번 PR에서 관찰된 모든 import를 exhaustive `depends_on` permission으로 고정하지 않는다. Full allowlist가 필요해지면 먼저 architecture owner에서 의도를 명시하고 `exact = true`와 함께 도입한다.
- Tach는 runtime-oriented dependency graph를 검사하도록 `ignore_type_checking_imports = true`를 사용하고, `tests/review_ai/test_dependency_boundaries.py`는 `TYPE_CHECKING`을 포함한 source-level AI forbidden-import guard로 유지한다.
- Global no-cycle도 새 architecture invariant이므로 이번 PR의 기본 requirement로 만들지 않는다. Repository가 해당 invariant를 별도로 채택하면 `forbid_circular_dependencies`로 투영한다.
- `tach check`가 Python source, `tach.toml`과 Tach dependency state 변경에서 CI 검증으로 실행되게 한다. 특히 `tach.toml`만 변경돼도 필요한 Python/uv 준비와 dependency sync를 거쳐 check가 실행되어야 한다.
- 기존 Lefthook에 local feedback을 추가한다면 Tach 자체 hook installer 대신 repository-owned `lefthook.yml`을 사용한다.
- Active repository tooling을 소유하는 `DEVELOPMENT.md`에 Tach와 실행 entrypoint를 반영한다.
- [`docs/development/tooling/tach.md`](../../docs/development/tooling/tach.md)는 이 repository의 Tach 역할, ownership, coverage와 검증 경계를 소유한다. 일반 CLI reference와 troubleshooting은 upstream 문서에 맡긴다.

## Boundaries

- 이번 PR에서 새로운 architecture layer, package, full dependency graph 또는 global no-cycle policy를 만들지 않는다.
- Tach public interface, domain config, deprecation rule 같은 확장 기능은 현재 dependency boundary를 검증하는 데 필요하지 않으면 도입하지 않는다.
- Tach 도입을 이유로 unrelated import cleanup이나 대규모 refactor를 수행하지 않는다.
- 현재 코드가 canonical architecture contract를 위반한다면 config로 허용해 숨기지 않는다. 수정 범위가 커지면 별도 scope decision으로 남긴다.
- `uv.lock`을 수동 편집하지 않는다.

## Implementation Direction

1. 로컬에서 `uv add --dev tach`로 dependency와 lockfile을 갱신한다. 준비 시점 기준 최신 upstream release는 `v0.35.1`(2026-09-14)이지만, 구현 시점의 current release와 Python 3.13 호환성을 다시 확인한다.
1. `src/hmda_reliability`의 top-level Python package와 package-root Python file을 확인하고, 모든 in-scope source가 Tach 검사에서 빠지지 않도록 module coverage와 `root_module` 동작을 결정한다.
1. `docs/ARCHITECTURE.md`, `docs/domains/**`와 applicable OpenSpec Spec에서 실제 dependency constraint를 추출하고 현재 import graph와 대조한다. 현재 graph에만 존재하는 edge는 자동으로 permission으로 채택하지 않는다.
1. `tach init` 또는 공식 configuration contract를 참고해 `tach.toml`을 만들고, 생성 결과를 그대로 수용하지 말고 repository boundary에 맞춰 정리한다. `ignore_type_checking_imports = true`를 명시하고 기존 AST dependency guard를 유지한다.
1. Canonical contract가 금지하는 dependency 방향을 Tach가 직접 거부하도록 최소 rule을 구성한다. 이번 PR에서는 full graph allowlist나 global cycle prohibition을 새 policy로 도입하지 않는다.
1. `uv run --no-sync tach check`가 clean 상태에서 통과하도록 한다. 대표적인 forbidden runtime import가 실패하는지도 temporary negative control 또는 deterministic test로 확인한 뒤 원상복구한다.
1. CI classifier에서 architecture check를 명시적으로 선택할 수 있게 하고, 최소한 `tach.toml` 단독 변경과 `src/**/*.py`, `pyproject.toml`, `uv.lock` 변경이 check 실행 경로를 활성화하는지 회귀 테스트로 고정한다. `tach.toml` 경로는 uv setup/sync가 생략되지 않아야 한다.
1. Lefthook에 추가한다면 Python source, `tach.toml`, dependency/config 변경에서만 실행되는 whole-repository check로 유지한다.
1. `DEVELOPMENT.md`의 active tooling 목록과 Quick Commands에 Tach entrypoint를 반영한다.
1. `docs/development/tooling/tach.md`를 실제 구현 상태와 맞추고 docs index generator를 실행해 generated index를 갱신한다.

## Acceptance

- `uv run --no-sync tach check`가 통과한다.
- `src/hmda_reliability`의 in-scope Python surface가 implicit root ignore 또는 unchecked 설정 때문에 조용히 검사에서 빠지지 않는다.
- Tach는 canonical AI dependency restriction을 runtime import 수준에서 거부하고, 기존 AST test는 `TYPE_CHECKING`을 포함한 source-level forbidden import를 계속 검증한다.
- `ignore_type_checking_imports = true`가 `tach.toml`에 명시된다.
- Canonical architecture가 소유하지 않는 현재 import edge를 단순히 관찰됐다는 이유로 persistent permission으로 추가하지 않는다.
- Full `depends_on` allowlist를 도입하지 않는다. 향후 별도 architecture decision으로 도입한다면 `exact = true`를 함께 사용한다.
- Global `forbid_circular_dependencies`는 이번 PR에서 새로운 architecture invariant로 도입하지 않는다.
- 대표적인 forbidden runtime dependency가 `tach check`에서 실제 실패하는 negative-path evidence가 있다.
- `tach.toml` 단독 변경과 `src/**/*.py`, `pyproject.toml`, `uv.lock` 변경이 CI architecture check를 활성화하며, classifier regression test가 이를 검증한다.
- `uv lock --check`가 통과한다.
- 변경한 TOML은 repository formatter/linter를 통과한다.
- CI classifier 변경 시 `tests/scripts/test_ci_classifier.py`가 통과한다.
- `lefthook.yml`을 변경하면 `uvx lefthook@2.1.10 validate`가 통과한다.
- 문서 변경은 repository Markdown 규칙을 통과한다.
- `DEVELOPMENT.md`의 active tooling 목록과 Quick Commands가 실제 도입 상태와 일치한다.
- `docs/development/tooling/tach.md`가 repository-specific Tach 운영 기준을 설명하고 일반 upstream reference를 중복하지 않는다.
- `uv run python scripts/generate_docs_indexes.py --check`가 통과한다.
- PR description의 Validation에는 실제 수행한 검증만 기록한다.

## Local Agent Handoff

브랜치 `chore/adopt-tach-dependency-boundaries`에서 위 범위만 구현한다. 먼저 canonical architecture constraint와 현재 import graph를 대조하고 package-root coverage를 결정한다. Tach는 runtime-oriented dependency guard로 두고 `TYPE_CHECKING`은 기존 AST test가 계속 검사한다. 이번 PR에서 full current graph allowlist나 global no-cycle policy를 새로 만들지 않는다. 이어 dependency 추가, minimal `tach.toml`, `tach.toml` 단독 변경도 빠지지 않는 CI 연동과 classifier regression test, `DEVELOPMENT.md` 및 `docs/development/tooling/tach.md`를 실제 구현 상태와 맞춘다. `uv.lock`은 반드시 `uv`로 갱신하고 docs index는 generator로 갱신한다. 완료 후 positive `tach check`, representative negative-path proof와 영향받은 repository validation을 실행해 Draft PR 본문을 실제 결과로 갱신한다. Scope가 architecture refactor로 커지면 임의로 확장하지 말고 PR에 blocker로 남긴다.
