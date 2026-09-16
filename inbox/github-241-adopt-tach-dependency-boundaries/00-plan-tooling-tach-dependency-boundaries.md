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

Tach를 개발 도구로 도입해 `src/hmda_reliability`의 Python 모듈 의존성 경계를 실행 가능한 검증으로 만든다. 이 변경은 기존 architecture contract를 새로 설계하는 작업이 아니라, 이미 문서화된 domain dependency를 현재 import graph에 맞춰 명시하고 이후 drift를 차단하는 작업이다.

## Scope

- Tach를 dev dependency로 추가하고 `uv.lock`은 로컬 `uv` workflow로 갱신한다.
- `tach.toml`에서 `src` source root와 현재 top-level domain package를 module boundary로 정의한다. Package root의 Python surface도 검사 범위에서 빠지지 않게 하고 `root_module` 동작을 명시적으로 결정해 기본 ignore에 의한 사각지대를 남기지 않는다.
- 현재 import graph를 기준으로 허용 dependency를 선언하고 cycle을 금지한다.
- [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md)의 명시적 AI 경계를 검증 가능한 dependency rule로 보존한다.
  - `review_ai`는 `reliability`, `runtime_ai`를 사용할 수 있다.
  - `reliability`는 AI package를 import하지 않는다.
  - `runtime_ai`는 `review_ai` 또는 `reliability` semantics에 의존하지 않는다.
- `tach check`가 `src/**/*.py` 또는 Tach configuration 변경에서 CI 검증으로 실행되게 한다. `tach.toml`만 변경돼도 필요한 Python/uv 준비와 dependency sync를 거쳐 check가 실행되어야 한다.
- Existing Lefthook에 local feedback을 추가한다면 Tach 자체 hook installer 대신 repository-owned `lefthook.yml`을 사용한다.
- Active repository tooling 목록을 소유하는 `DEVELOPMENT.md`에 Tach를 반영한다. 별도 tooling guide는 project-specific usage가 반복해서 필요할 때만 추가한다.

## Boundaries

- 이번 PR에서 새로운 architecture layer나 package를 만들지 않는다.
- Tach public interface, domain config, deprecation rule 같은 확장 기능은 현재 dependency boundary를 검증하는 데 필요하지 않으면 도입하지 않는다.
- Tach 도입을 이유로 unrelated import cleanup이나 대규모 refactor를 수행하지 않는다.
- 현재 코드가 canonical architecture contract를 위반한다면 config로 허용해 숨기지 않는다. 다만 수정 범위가 커지면 별도 scope decision으로 남긴다.
- `uv.lock`을 수동 편집하지 않는다.

## Implementation Direction

1. 로컬에서 `uv add --dev tach`로 dependency와 lockfile을 갱신한다. 준비 시점 기준 최신 upstream release는 `v0.35.1`(2026-09-14)이지만, 구현 시점의 current release와 Python 3.13 호환성을 다시 확인한다.
1. `src/hmda_reliability`의 top-level package와 package-root Python file을 확인하고, 모든 in-scope source가 Tach 검사에서 빠지지 않도록 module coverage와 `root_module` 동작을 먼저 결정한다.
1. `tach init` 또는 공식 configuration contract를 참고해 `tach.toml`을 만들고, 생성 결과를 그대로 수용하지 말고 repository domain boundary에 맞춰 정리한다.
1. 실제 import graph를 확인해 top-level package 간 `depends_on`을 선언한다. 현재 import를 architecture truth로 승격하지 말고 `docs/ARCHITECTURE.md`와 충돌 여부를 함께 확인한다.
1. `uv run --no-sync tach check`가 clean 상태에서 통과하도록 한다.
1. CI classifier에서 architecture check를 명시적으로 선택할 수 있게 하고, 최소한 `tach.toml` 단독 변경과 `src/**/*.py` 변경이 check 실행 경로를 활성화하는지 회귀 테스트로 고정한다. `tach.toml` 경로는 uv setup/sync가 생략되지 않아야 한다.
1. Lefthook에 추가한다면 `src/**/*.py`, `tach.toml`, dependency/config 변경에서만 실행되는 whole-repository check로 유지한다.
1. `DEVELOPMENT.md`의 active tooling 목록을 갱신하고, 그 밖의 project-specific 문서는 실제 반복 사용에 필요한 최소 범위만 추가한다. 일반 Tach 사용법은 upstream 문서에 맡긴다.

## Acceptance

- `uv run --no-sync tach check`가 통과한다.
- `src/hmda_reliability`의 in-scope Python surface가 implicit root ignore 또는 unchecked 설정 때문에 조용히 검사에서 빠지지 않는다.
- `tach.toml` 단독 변경과 `src/**/*.py` 변경이 CI architecture check를 활성화하며, classifier regression test가 이를 검증한다.
- `uv lock --check`가 통과한다.
- 변경한 TOML은 repository formatter/linter를 통과한다.
- CI classifier 변경 시 `tests/scripts/test_ci_classifier.py`가 통과한다.
- `lefthook.yml`을 변경하면 `uvx lefthook@2.1.10 validate`가 통과한다.
- 문서 변경은 repository Markdown 규칙을 통과한다.
- `DEVELOPMENT.md`의 active tooling 목록이 실제 도입 상태와 일치한다.
- PR description의 Validation에는 실제 수행한 검증만 기록한다.

## Local Agent Handoff

브랜치 `chore/adopt-tach-dependency-boundaries`에서 위 범위만 구현한다. 먼저 현재 import graph와 `docs/ARCHITECTURE.md`의 dependency constraint를 대조하고 package-root Python file까지 포함한 Tach coverage를 결정한 뒤 config를 작성한다. 이어 dependency 추가, `tach.toml` 단독 변경도 빠지지 않는 CI 연동과 classifier regression test, 필요한 최소 문서 갱신 순서로 진행한다. `uv.lock`은 반드시 `uv`로 갱신하고, 완료 후 `tach check`와 영향받은 repository validation을 실행해 Draft PR 본문을 실제 결과로 갱신한다. Scope가 architecture refactor로 커지면 임의로 확장하지 말고 PR에 blocker로 남긴다.