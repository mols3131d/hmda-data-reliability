---
type: brief
title: "Safe Agent Asset Rebuild and Toolchain Refresh"
description: "Rulesync·Skills CLI·OpenSpec의 공유 출력물 재구축과 최신 버전 갱신, 스크립트·task 최적화를 위한 로컬 에이전트 인계입니다."
tags:
  - agent-assets
  - bootstrap
  - tooling
---

# Safe Agent Asset Rebuild and Toolchain Refresh

## Purpose

현재 선언에서 제거된 오래된 Agent Asset 출력물을 안전하게 정리하고 Rulesync, Skills CLI, OpenSpec의 관리 범위를 지켜 재구축한다. **Rulesync가 공유 대상의 다른 도구 설치물까지 지우는 접근**도 실험하되, 모든 대상이 복원된다는 가정부터 하지 않는다. 실제 삭제·복원 동작을 비교해 가장 단순하고 재현 가능한 방법을 선택하고, 관련 스크립트와 task 진입점을 최적화한다.

이번 작업에 **Rulesync, Skills CLI, OpenSpec의 최신 정식 버전 확인 및 갱신**을 포함한다. 버전 갱신과 외부 자산 source revision 갱신은 구분하며, 예상치 못한 의존 자산 갱신을 섞지 않는다.

이 문서는 로컬 에이전트가 수행할 구현 인계다. 작성 시점에 CLI 갱신, 삭제 및 재설치 실험은 실행하지 않았다.

## Current Evidence

- `scripts/rulesync.py`는 설치·생성 후 stale projection을 수동 확인하라는 안내를 출력한다. CLI가 제거된 자산을 자동 정리하는지는 실제 적용 버전에서 검증해야 한다.
- `scripts/agent_assets.py`는 Rulesync → Skills CLI → `.agents/route` 생성 순서로 동작한다. OpenSpec은 여기서 실행되지 않는다.
- `scripts/bootstrap.py`는 `setup`과 `update`에서만 OpenSpec integration을 갱신하고 `session`에서는 갱신하지 않는다.
- `skills-lock.json`은 현재 `langfuse`만 선언한다. 다른 경로에 있는 Skill을 Skills CLI가 모두 복원할 수 있다는 보장은 없다.
- `.rulesync/README.md`, `docs/development/tooling/rulesync.md`는 `.agents/skills`, `.claude/skills` 등의 공유 네임스페이스와 OpenSpec/Skills CLI 설치물 충돌을 명시한다.
- `.vscode/tasks.json`에는 `Bootstrap: Session`, `Bootstrap: Update`, `Format` task가 있다. reset 전용 task는 없다.
- `.rulesync/**`, `rulesync.jsonc`, `rulesync.lock`, `openspec/**`, `.agents/route/**` 등 원본·정본·파생 출력의 Git 추적/생성 경계를 혼동해서는 안 된다.

관련 정본: `docs/development/ai-agent/README.md`, `docs/development/tooling/{rulesync,bootstrap,openspec}.md`, `DEVELOPMENT.md`, `docs/development/vcs-git/`.

## Local Experiments

반드시 먼저 **격리된 임시 clone/worktree 또는 작은 fixture**에서 실행한다. 작업자의 실제 설치물이나 repository 원본을 대상으로 위험한 삭제를 실험하지 않는다.

1. **Baseline과 버전 확인**: 현재 세 CLI의 실제 버전·최신 안정 릴리스·공식 옵션을 확인한다. `@latest` 표기만으로 최신 버전이 설치됐다고 가정하지 않는다. 버전·차이·호환성 위험을 기록한다.
1. **Native cleanup 후보**: 현재 Rulesync 버전에서 `generate --delete`, `--dry-run`, `--json` 등 지원 여부와 정확한 삭제 대상을 검증한다. 지원하지 않는 조합이나 확실하지 않은 출력은 사용하지 않는다. 기존 overwrite 방식, 별도 namespace/부분 정리 방식과 결과를 비교한다.
1. **공유 namespace 충돌**: Rulesync가 제거한 Skill, Skills CLI 설치 Skill, OpenSpec 설치 Skill, 동일 이름 충돌, 사용자 수동 파일, Git 추적 파일, symlink가 공존하는 fixture에서 손실·잔존 여부를 살핀다. 소유자/복원 출처가 확인되지 않는 자산은 자동으로 지우지 않는다.
1. **복원 순서**: Rulesync 생성 → Skills CLI 복원 → OpenSpec integration 복원 → route 갱신을 포함해 여러 순서를 실제 비교한다. `openspec update`가 완전히 삭제된 설치물까지 복원하는지 별도 검증한다. `init`이 필요하다면 기존 프로젝트 상태·부작용을 확인하며 자동 초기화를 강요하지 않는다.
1. **부분 실패와 재실행**: 각 단계 실패 후 남는 상태, 다음 실행으로 수렴하는지, 중복 실행 시 불필요한 변경이 없는지 확인한다. 실패를 성공으로 보고하거나 route만 최신인 불완전 상태를 성공으로 취급하지 않는다.
1. **명령 인터페이스**: `scripts/agent_assets.py`, `scripts/rulesync.py`, `scripts/bootstrap.py`, `.vscode/tasks.json` 및 실제 호출자(CI·문서·hook)를 비교한다. `reset`을 어디에 둘지, 미리보기와 명시적 승인 방식을 어떻게 제공할지, 기존 명령을 유지·통합·제거할지를 실험 결과로 결정한다.

## Implementation Direction

- `mols-dev-env-bootstrap-design`, `mols-project-task-command-design`을 사용한다. 필요한 경우 `code-flow-map`으로 영향받는 호출 경로만 추적한다.
- Native CLI 옵션과 기존 wrapper를 우선하고 새 범용 자산 관리기, 영구 ownership DB, 과도한 설정 및 별도 task runner는 검증된 필요가 없다면 만들지 않는다.
- `setup`, `session`, `update`의 현재 계약을 보존한다. 전체 재구축/삭제는 **의도적으로 실행하는 별도 동작**이어야 하며 일상 session에 끼워 넣지 않는다.
- 세 CLI의 최신 정식 릴리스를 실제로 적용하고, repository-local 사용 방식·호환성·생성 경로를 확인한다. lock과 생성물은 해당 CLI/스크립트로 갱신하며 수동 편집하지 않는다. 도구 갱신 때문에 다른 자산의 revision이 바뀌면 원인을 분석하고 불필요한 변경을 제외한다.
- 삭제 계획은 사람이 확인할 수 있어야 한다. 승인 전에는 삭제하지 않으며 복원이 증명된 repo 범위의 대상만 실제 정리한다. 변경·소유 여부를 알 수 없으면 중단하거나 선별 보존한다.
- 필요한 `tests/scripts/` 테스트와 소유 문서를 갱신하고 명령 진입점 및 VS Code task를 사용자가 이해할 수 있는 최소 집합으로 정리한다.
- `scripts/clean.py`는 일반 cache/artifact 정리와 목적이 다르다. 자산 초기화로 의미를 확장하지 않는다.

## Completion Criteria

1. **Legacy cleanup** — 구성에서 제거된 Rulesync 출력물이 실제 대상에서 정리된다. 다른 도구 설치물은 **보존되거나, 명시적으로 복원 가능한 대상으로 판정한 후 정리·복원**된다. 사용자 파일/불명 소유 자산의 손실이 없다.
1. **Reproducible restore** — Rulesync, Skills CLI, OpenSpec의 현재 관리 대상을 초기화 후 복원하고 `.agents/route`를 정합하게 생성한다. 누락·오류는 상태와 종료 코드로 드러나며 반복 실행 후 정상 상태로 수렴한다.
1. **Latest tooling** — 세 CLI 각각에 대해 작업 시점의 최신 정식 버전을 공식 출처로 확인하고 업데이트한다. 실제 실행 버전과 호환성·lock/생성물 변경 및 검증 결과를 기록한다. 최신 버전이 불가능하면 이유와 검증된 대안을 명시해 미완료로 보고한다.
1. **Command optimization** — 실험 결과를 근거로 관련 스크립트·task를 필요한 만큼 정리한다. 정상 사용 경로와 CI·hook·문서 소비자, 종료 코드, `setup/session/update`의 부작용 계약을 보존한다.
1. **Evidence** — 삭제 미리보기, 복원, 타 도구 자산 보존, 실패 후 복구, idempotence, 세 버전·호환성, 관련 단위 테스트 및 가능한 제한된 실제 실행 결과를 남긴다. 실행하지 않은 검증은 통과로 표시하지 않는다.

## Boundaries and Handoff

- 본 PR의 **완료 목표는 실제 스크립트·task 최적화, 도구 버전 갱신, 검증까지 마치는 것**이다. 이 인계 문서 작성 자체는 완료가 아니다.
- 원본 `.rulesync/**`, OpenSpec의 project config·schema, 추적 중인 수동 자산과 `rulesync.lock`·`skills-lock.json` 같은 local-tool-managed state를 원격에서 수동 조작하지 않는다.
- HOME/전역 설치/공유 cache/기존 사용자 자산과 외부 시스템에 미치는 삭제·변경은 추가 승인이 필요하다. 테스트는 먼저 격리 환경에서 수행한다.
- 제품 코드, OpenSpec schema·spec의 설계 변경, CI admission 재설계, 무관한 의존성 업그레이드는 제외한다.
- 로컬 에이전트는 이 제안을 확정 설계로 간주하지 말고 실제 도구 동작으로 검증한 뒤 최소 변경을 선택한다. 커밋은 검토 가능한 단위로 기록하고 push 후 PR 본문과 검증 근거를 현재 HEAD에 맞춰 갱신한다. 임의 merge는 하지 않는다.
