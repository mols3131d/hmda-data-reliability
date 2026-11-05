---
type: plan
title: "Agent Skills Adoption and Tooling Command Optimization"
description: "PR #285의 세 가지 Skill 채택을 마무리하고 개발환경 부트스트랩·공통 명령을 근거 기반으로 개선하기 위한 로컬 에이전트 인계안입니다."
tags:
  - agent-assets
  - tooling
---

# Agent Skills Adoption and Tooling Command Optimization

## Goal

PR [#285](https://github.com/mols3131d/hmda-data-reliability/pull/285)에서 다음 세 Skill을 Rulesync로 채택하고, **`mols-dev-env-bootstrap-design`과 `mols-project-task-command-design`을 실제로 적용해** 프로젝트 개발환경 부트스트랩·스크립트·공통 태스크 명령을 개선한다. 변경이 정당화되지 않는 명령은 유지하고, 의미 없는 신규 wrapper나 실행기를 만들지 않는다.

| Skill | 이번 PR에서의 역할 |
| --- | --- |
| `code-flow-map` | 복잡하거나 수정 영향이 불명확한 스크립트의 호출·데이터 흐름 추적에 선택적으로 활용 |
| `mols-dev-env-bootstrap-design` | 최초 설정·세션 복원·명시적 업데이트의 재현성, 안전성, 부분 실패와 설치 부작용 검토 |
| `mols-project-task-command-design` | 개발자·에이전트·CI가 사용하는 공통 명령의 진입점, 중복 계층, 호환성, 실패 의미 개선 |

## Current State

- Owning branch: `agent/chore/update-development-tooling` (PR #285, Draft). 작업 전 원격 head와 로컬 worktree를 재확인한다.
- `rulesync.jsonc`의 `mols3131d/mols-agent-assets` source에 위 세 Skill 선언을 추가했다. **아직 설치·실제 런타임 선택이 검증된 상태는 아니다.**
- PR의 기존 변경은 upstream 도구 revision·`rulesync.lock`·`skills-lock.json`·`.agents/route/skills.jsonl` 갱신이다. 새 Skill에 맞는 managed lock과 route는 **로컬 도구로 재생성해야 한다**. 기존 PR description의 validation은 새로운 head를 검증한 결과가 아니다.

## Work

### 1. Restore and Validate Skills

1. 현재 프로젝트 하네스와 Rulesync 관리 정책, 세 `SKILL.md` 및 필요한 동반 리소스를 읽는다. 기존 `mols-agent-asset-find`를 자산 도입 절차에 활용한다.
2. `scripts/agent_assets.py`, `scripts/rulesync.py` 등의 **프로젝트 기본 경로**로 선언·잠금·프로젝션·챗봇 라우팅을 동기화한다. `rulesync.lock`, `skills-lock.json` 및 생성된 라우트를 수동 편집하지 않는다. 필요 없는 외부 source의 revision 전진이나 무관한 파일 변경은 포함하지 않는다.
3. 세 Skill의 package resources, Rulesync resolved revision, 대상별 실제 Skill 발견·선택 가능 여부를 확인한다. `code-flow-map`의 template 같은 동반 파일 누락에도 유의한다.

### 2. Improve Bootstrap and Task Commands

**`mols-dev-env-bootstrap-design`**과 **`mols-project-task-command-design`**의 방법론을 이번 작업에 적용하고, 필요한 코드 수정은 프로젝트의 구현·테스트 절차로 수행한다.

- 현재 공통 진입점과 호출자를 먼저 조사한다: `scripts/bootstrap.py`, `scripts/_commands.py`, `scripts/agent_assets.py`, `scripts/rulesync.py`, 관련 `scripts/` 유틸리티, `DEVELOPMENT.md`, `docs/development/tooling/`, `pyproject.toml`, `lefthook.yml`, CI workflow 및 테스트. 관련이 없는 스크립트까지 일괄 리팩터링하지 않는다.
- **Bootstrap:** 기존 `setup / session / update`의 역할과 lock 처리, missing-tool 진단, idempotence, 부분 실패 후 복구, 글로벌·사용자·공유 캐시 부작용, 설치 승인 경계를 검토한다. `session`이 무의식적으로 도구를 업데이트하거나 `update`가 초기 설정을 대신하도록 계약을 혼동하지 않는다.
- **Task/command:** 실제 호출 그래프를 기준으로 명령별 `유지 / native 직접 호출 / 통합 / 분리 / 제거`를 판단한다. 중복 wrapper와 의미 없는 옵션은 줄이되 안정된 명령 이름의 가치와 CI·hook·문서 소비자를 보존한다. 별도 task runner는 명확한 이득이 증명될 때만 고려한다.
- 변경 전후로 인수 전달, working directory, PATH/env, 플랫폼 차이, 종료 코드, 실패·재시도 의미, lock/cache, 파일·Git·호스트에 대한 부작용을 비교한다. 필요 시 `code-flow-map`으로 위험한 호출 경로만 추적한다.
- **검증 가능한 개선만 구현한다.** 사용성이나 복잡도 개선이 성립하지 않는 코드는 그대로 두고, 변경한 명령의 테스트와 해당 owning 문서만 갱신한다. 제품 도메인 코드, OpenSpec 계약, CI admission 정책의 재설계는 이 PR의 기본 범위가 아니다.

## Acceptance and Handoff

- 세 Skill이 declarative source, generated lock, route와 대상 runtime에서 일관되게 확인된다. 단순 source 등재와 실제 설치·실행은 구분해 보고한다.
- 바뀐 명령은 관련 테스트 및 안전한 실제 호출로 검증한다. `scripts/rulesync.py validate`, `python -m scripts.agent_routes --check`, 관련 `tests/scripts/` 및 프로젝트의 정해진 검증 경로를 활용하되 실제로 수행한 결과만 기록한다.
- 설치·업데이트를 위해 홈 디렉터리, 전역 환경, 공유 캐시, Git hook 또는 외부 서비스에 영향이 생긴다면 영향과 권한을 확인하고 필요한 승인을 먼저 받는다. 위험한 명령을 검증 목적으로 무작정 실행하지 않는다.
- PR #285의 Summary·Changes·Validation을 **최종 변경 head의 실제 증거**로 갱신한다. 미검증 항목은 명시하고 Draft 상태를 유지한다. 임의의 merge, force-push, history rewrite, 다른 계정 사용을 하지 않는다.

다음 행동: 로컬 branch와 원격 PR head의 정합성을 확인한 뒤 **Skill 동기화 → 호출·부트스트랩 문제 조사 → 근거 있는 최소 개선 → 테스트·PR description 갱신** 순서로 수행한다.
