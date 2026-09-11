---
type: research
title: OpenSpec CI Admission Reinforcement Research
description: OpenSpec 규격·변경·설정 변경에 대한 CI Lite 병합 차단 검증과 변경 감지 체계 도입 방안을 조사한다.
tags:
  - ci
  - openspec
  - admission-boundary
---

# OpenSpec CI Admission Reinforcement Research

> [!NOTE]
> **핵심 결론:** 현재 CI Lite([.github/workflows/ci-lite.yml](.github/workflows/ci-lite.yml))는 [openspec/](openspec/README.md) 트리의 어떤 파일이 변경되어도 검증을 수행하지 않는 완전한 admission gap 상태입니다. OpenSpec의 전체 검증(`openspec validate --all --strict`)은 약 1.0초 내외로 극히 경량이며 20개 규격·변경 전수의 정합성을 안전하게 보호하므로, [.github/workflows/classify_changes.sh](.github/workflows/classify_changes.sh)에 `openspec=true` 분류 플래그를 신설하고 CI Lite에 차단 게이트를 즉시 배치하는 것이 최선입니다. 실행 도구는 기존 Biome/Tombi와 동일하게 [scripts/bootstrap.py](scripts/bootstrap.py)의 Node 도구 관리 및 [scripts/_commands.py](scripts/_commands.py) 래퍼 패턴으로 일관되게 관리하는 것을 권장합니다.

## Question

OpenSpec 규격(`openspec/specs/**`), 작업 변경(`openspec/changes/**`), 워크플로 스키마(`openspec/schemas/**`), 프로젝트 설정([openspec/config.yaml](openspec/config.yaml))이 변경되었을 때, `main` 브랜치로의 strict admission을 보장하려면 CI Lite([.github/workflows/ci-lite.yml](.github/workflows/ci-lite.yml))와 로컬 개발 환경([lefthook.yml](lefthook.yml))에 어떤 검증 파이프라인 및 변경 감지(change classification) 구조를 도입해야 하는가?

## Scope

- [openspec/](openspec/README.md) 디렉터리 내 canonical specs, active changes, archived changes, schemas, config 변경의 감지 및 검증
- [.github/workflows/classify_changes.sh](.github/workflows/classify_changes.sh)의 변경 감지 플래그 및 타깃 라우팅 로직
- [.github/workflows/ci-lite.yml](.github/workflows/ci-lite.yml)의 CI 병합 차단 게이트(admission gate) 단계 설계
- 로컬 Git Hook([lefthook.yml](lefthook.yml)) 및 부트스트랩 스크립트([scripts/bootstrap.py](scripts/bootstrap.py)) 연계 방안
- 분류기 회귀 테스트([tests/test_ci_classifier.py](tests/test_ci_classifier.py))의 검증 범위

### Out of Scope

- OpenSpec CLI(`@fission-ai/openspec`) 내부 검증 알고리즘 또는 패키지 소스 코드 자체의 수정
- `openspec/schemas/spec-driven-tdd/` 내 템플릿 및 instruction 규칙의 의미론적 재설계
- Python 애플리케이션 소스 코드 및 도메인 비즈니스 로직 수정

## Findings

### Current CI Admission Completely Bypasses OpenSpec Tree

현재 CI Lite는 OpenSpec 트리의 변경 사항을 사실상 검증하지 않고 통과시키는 치명적인 검증 공백을 가지고 있습니다.

1. **설정/스키마 파일 완전 무시:** [.github/workflows/classify_changes.sh](.github/workflows/classify_changes.sh)에는 `*.yaml` 또는 `openspec/` 트리에 대한 분류 규칙이 없습니다. [openspec/config.yaml](openspec/config.yaml)이나 [openspec/schemas/spec-driven-tdd/schema.yaml](openspec/schemas/spec-driven-tdd/schema.yaml)이 단독 수정될 경우 모든 분류 플래그(`json`, `markdown`, `python`, `tests` 등)가 `false`로 출력되어 CI 전체 작업이 아무런 검사 없이 1초 만에 통과합니다.
1. **마크다운 산출물의 검증 누락:** `openspec/**/*.md` (규격 문서 및 변경 제안서 등)가 변경되면 `markdown=true` 플래그는 켜지지만, [.github/workflows/ci-lite.yml](.github/workflows/ci-lite.yml#L45-L65)에서 실행되는 것은 오직 `rumdl fmt` 제안(diff summary, non-blocking)뿐입니다. `rumdl check`는 `docs/*` 경로에만 제한 적용되므로 OpenSpec 마크다운에 대해서는 어떠한 blocking 검증도 실행되지 않습니다.
1. **로컬 훅 공백:** [lefthook.yml](lefthook.yml)의 `pre-commit`과 `pre-push`에도 OpenSpec 검증 명령이 전혀 등록되어 있지 않아 개발자나 에이전트가 로컬에서 사전 피드백을 받을 수 없습니다.

결과적으로 깨진 규격, 문법 오류, 필수 아티팩트(proposal/design/tasks) 누락, 스키마 불일치가 발생해도 `main` 브랜치에 그대로 병합될 수 있습니다.

#### Evidence

- [.github/workflows/classify_changes.sh](.github/workflows/classify_changes.sh#L180-L195)
  - `openspec/config.yaml` 입력 시 모든 플래그가 `false`로 반환됨을 확인
  - `openspec/specs/orchestration-pipeline/spec.md` 입력 시 `markdown=true`만 켜지고 `inbox=false`, `tests=false`로 분류됨
- [.github/workflows/ci-lite.yml](.github/workflows/ci-lite.yml#L55-L65)
  - `rumdl check` 대상이 `[[ "$path" == docs/* ]]`로 하드코딩되어 `openspec/` 산출물 제외 확인
- [docs/AGENTS.md](docs/AGENTS.md#L18), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#L89)
  - 시스템 기능의 normative contract는 `docs/`가 아니라 [openspec/specs/](openspec/README.md)가 소유한다고 명시되어 있으나, 정작 CI에서는 `docs/`만 검사하고 canonical contract인 `openspec/`은 검증하지 않음

### OpenSpec CLI Validation Profile and Latency Characteristics

OpenSpec CLI의 `validate` 하위 명령은 저장소 내 규격과 변경의 정합성을 검증하는 결정론적 검사 기능을 제공하며, 실행 비용이 극히 낮습니다.

1. **전체 검증 성능:** `openspec validate --all --strict`는 현재 저장소의 18개 canonical specs와 2개 active changes(총 20개 항목)를 전수 검증하는 데 로컬 환경 기준 약 **1.0초**(사용자 CPU 0.5초)밖에 소요되지 않습니다.
1. **아카이브 검증 성능:** `openspec validate --archived`는 완료 보관된 38개 changes의 모든 task 완료 체크(`- [x]`)를 검증하며, 약 **0.95초** 만에 완료됩니다.
1. **무결성 상태:** 현재 저장소의 20개 활성 규격/변경 및 38개 아카이브는 전수 검증 시 에러 없이 `passed` 상태입니다.
1. **주의 관찰 사항:** `npm exec`를 통한 검증 시 `change/orchestration-quality-gate`의 `specs/orchestration-pipeline/spec.md` delta에서 기존 헤더(`### Requirement: Data quality gate execution`)와 중복되어 향후 아카이브 시 거부될 수 있다는 `[INFO]` 경고가 감지되었습니다. 이는 유효성 검증(`valid: true`) 자체를 실패시키지는 않지만 사전 진단 가치가 높음을 보여줍니다.

#### Evidence

- `openspec validate --all --strict` 실행 결과: `Totals: 20 passed, 0 failed (20 items)`, 소요 시간 `1.037 total`
- `openspec validate --archived` 실행 결과: `Totals: 38 passed, 0 failed (38 items)`, 소요 시간 `0.948 total`
- `npm exec --yes --package=@fission-ai/openspec@latest -- openspec validate --all --strict` 실행 결과: `Totals: 20 passed, 0 failed (20 items)`, 소요 시간 약 1.8초

### Change Impact and Fail-Safe Selection Boundary

[docs/development/ci.md](docs/development/ci.md)의 CI 설계 원칙에 비추어 볼 때, OpenSpec 검증은 fail-safe한 전체 검증(`--all --strict`)을 기본으로 두는 것이 타당합니다.

1. **상호 참조 결합도:** OpenSpec에서 `changes/**`의 delta spec은 canonical `specs/**`를 참조하며, [openspec/config.yaml](openspec/config.yaml) 및 [openspec/schemas/spec-driven-tdd/schema.yaml](openspec/schemas/spec-driven-tdd/schema.yaml)의 변경은 전체 규격과 변경의 유효성 평가에 파급됩니다.
1. **선택적 검증 대비 비용 우위:** 전체 검증이 1초 내외로 끝나므로, 변경된 단일 아이템만 복잡하게 파싱하여 `openspec validate <item>`을 호출하는 미세 최적화는 파싱 오버헤드와 참조 누락 위험만 키울 뿐 latency 절감 효과가 거의 없습니다.
1. **라우팅 규칙:**
   - `openspec/**` 경로(설정, 스키마, 규격, 변경, 아카이브)의 파일이 1개라도 수정되면 `openspec=true`를 활성화합니다.
   - 변경 파일 중 `openspec/changes/archive/**`가 포함되어 있을 경우 `openspec validate --archived`를 추가 실행하거나, `openspec=true` 시 항상 `--all --strict`와 함께 `--archived`를 실행해도 총 2초 이내로 해결됩니다.

#### Evidence

- [docs/development/ci.md](docs/development/ci.md#L30-L40)
  - "영향 범위를 확신할 수 없으면 안전하게 넓히거나 실패시킨다"
  - "중요한 검증이 path 분류 때문에 조용히 빠지지 않게 한다"
- [docs/development/ci.md](docs/development/ci.md#L90-L95)
  - "Admission Boundary: main에 들어가면 안 되는 문제는 병합 전에 차단할 수 있어야 한다"

### Tooling Invocation and Execution Architecture Options

저장소 내 Node.js 기반 도구들의 운영 패턴과 OpenSpec 실행 방식을 비교 분석했습니다.

1. **현행 도구 아키텍처:**
   - [scripts/bootstrap.py](scripts/bootstrap.py#L15-L25)는 `NODE_TOOL_PREFIX`(`.local/tooling`)에 `@biomejs/biome@2`, `tombi@1`을 무설치 모드로 설치하고, [scripts/biome.py](scripts/biome.py), [scripts/tombi.py](scripts/tombi.py) 래퍼를 통해 [scripts/_commands.py](scripts/_commands.py)의 `run_local_node_tool`을 호출합니다.
   - [docs/development/tooling/openspec.md](docs/development/tooling/openspec.md)에 따르면 OpenSpec은 bootstrap 시 `npm exec @fission-ai/openspec@latest openspec update`로 갱신하도록 되어 있습니다.
1. **CI 환경 특성:**
   - GitHub Actions의 `ubuntu-latest` 러너에는 Node.js 및 npm이 기본 탑재되어 있습니다.
   - [.github/workflows/ci-lite.yml](.github/workflows/ci-lite.yml#L70-L75)은 이미 `npm install --prefix .local/tooling --no-save --package-lock=false @biomejs/biome@2 tombi@1`을 수행하는 패턴을 확립하고 있습니다.

## Options

| 평가 기준 | Option 1: CI 인라인 npm exec / npx 호출 | Option 2: .local/tooling 통합 및 Python 래퍼 스크립트 제공 | Option 3: 전용 셸 명령 및 CI 독립 도구 셋업 |
| --- | --- | --- | --- |
| **실행 메커니즘** | CI step에서 `npx --yes @fission-ai/openspec@1 validate --all --strict` 직접 실행 | [scripts/bootstrap.py](scripts/bootstrap.py)의 `NODE_TOOL_PACKAGES`에 추가하고 `scripts/openspec.py` 래퍼 작성 | CI에 별도 `actions/setup-node` 추가 및 글로벌 설치 |
| **저장소 도구 일관성** | ⚠️ 낮음 (Biome/Tombi 패턴과 불일치) | ✅ 높음 (기존 Biome/Tombi와 완벽히 동일한 패턴) | ❌ 낮음 (불필요한 별도 action 도입) |
| **로컬 환경 연계성 (Lefthook)** | ⚠️ 개발자 환경마다 글로벌 `openspec` 설치 여부에 의존 | ✅ 높음 (`python scripts/openspec.py`로 Windows/Linux 동일하게 즉시 실행 가능) | ⚠️ 로컬 설치 가이드 별도 요구 |
| **구현 및 유지보수 비용** | ✅ 매우 낮음 (CI workflow 한 줄 추가) | 🟡 보통 (스크립트 1개 추가 및 bootstrap 설정 2줄 추가) | ❌ 보통 이상 (CI 워크플로 복잡도 증가) |
| **실행 지연 시간 (Latency)** | 약 1.5~2.0초 (매번 npx 임시 해석) | 약 1.0초 (.local/tooling 설치 후 로컬 바이너리 직접 실행) | 약 10~15초 (Node 셋업 오버헤드) |

### Option Comparison Analysis

- **Option 1 (인라인 npm exec/npx):** 가장 빠르게 도입할 수 있으나, 로컬 개발자나 [lefthook.yml](lefthook.yml)에서 동일한 방식으로 검증을 호출하기 어렵고, 저장소 도구 래퍼 패턴과 파편화됩니다.
- **Option 2 (.local/tooling + scripts/openspec.py, 권장):** [scripts/biome.py](scripts/biome.py) 및 [scripts/tombi.py](scripts/tombi.py)와 완전히 일치하는 구조입니다. 로컬에서는 `uv run --no-sync python scripts/bootstrap.py setup`을 통해 `.local/tooling`에 함께 설치되며, [lefthook.yml](lefthook.yml)의 `pre-push`에서도 `uv run --no-sync python scripts/openspec.py validate --all --strict`를 일관되게 호출할 수 있습니다. CI Lite에서도 [scripts/biome.py](scripts/biome.py)처럼 안정적으로 호출됩니다.
- **Option 3 (글로벌 셋업):** 불필요한 GitHub Action 추가로 CI 실행 시간을 늘리므로 배제합니다.

## Implications

1. **CI Admission 차단력 확보:**
   - [openspec/](openspec/README.md) 트리의 모든 변경에 대해 규격 형식, 스키마 적합성, delta 유효성, 태스크 형식이 엄격하게 검증되어 `main` 브랜치로의 canonical contract 훼손이 원천 차단됩니다.
1. **CI 분류기 및 테스트 보강:**
   - [.github/workflows/classify_changes.sh](.github/workflows/classify_changes.sh)에 `openspec` 감지 로직 추가.
   - [tests/test_ci_classifier.py](tests/test_ci_classifier.py)에 OpenSpec 파일 변경 시 `openspec=true` 반환을 검증하는 결정론적 단위 테스트 추가.
1. **로컬 개발자 피드백 루프 완성:**
   - [lefthook.yml](lefthook.yml)의 `pre-push` 단계에 OpenSpec 검증을 추가함으로써 push 전에 에이전트와 사람이 규격 오류를 조기 발견할 수 있습니다.
1. **CI 워크플로 영향:**
   - OpenSpec 변경이 없는 일반 Python/문서 PR은 `openspec=false`로 유지되어 추가 latency가 0초입니다.
   - OpenSpec 변경이 있는 PR의 경우에도 검증 실행 시간은 약 1~2초 수준에 불과하여 CI 전체 수행 시간(10분 타임아웃 중 1분 미만)에 미치는 영향이 극히 미미합니다.

## Open Questions

- **아카이브 검증 분리 여부:**
  - `openspec validate --archived`는 모든 과거 38개 아카이브를 검사하므로, `openspec=true`일 때 항상 실행할 것인지, 아니면 `openspec/changes/archive/**`에 변경이 감지될 때만 실행할 것인지 결정할 수 있습니다. (전체 실행 시간이 0.95초이므로 단순성을 위해 함께 실행하거나, 아카이브 전용 변경 시에만 트리거하는 경량 조건문 추가 가능)
- **OpenSpec 버전 고정 범위:**
  - 현재 `scripts/bootstrap.py`는 `@latest`를 참조하고 있으나, CI 재현성과 공급망 안정성을 위해 [scripts/bootstrap.py](scripts/bootstrap.py) 및 CI 설치 단계에서 `@fission-ai/openspec@^1.12.0` 또는 `@1`과 같이 메이저/마이너 버전을 고정할지 검토가 필요합니다.
