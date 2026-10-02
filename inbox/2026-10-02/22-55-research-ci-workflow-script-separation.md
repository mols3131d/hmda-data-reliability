---
type: research
title: CI Workflow Script Separation
description: CI workflow의 inline shell과 path 분류 로직을 독립 스크립트로 옮길 때 디버깅 가능성, 계약 검증, 운영 비용이 어떻게 달라지는지 판단한다.
tags:
  - ci
  - github-actions
  - testing
---

# CI Workflow Script Separation

> [!NOTE]
> 반복되는 다단계 로직은 독립된 저장소 스크립트로 옮기고 workflow에는 trigger, 권한, job 순서와 짧은 명령만 남기는 편이 낫다. 다만 이번 PR에서 본 실패는 inline shell이 직접 원인이 아니며, 입력 lock schema와 route generator 계약의 불일치였다. 파일 분리는 실패 메시지와 회귀 검증을 개선하지만 그 계약 불일치를 자동으로 해결하지는 않는다.

## Question

GitHub Actions workflow 안에 여러 shell 스크립트와 분기 로직을 둘 때 발생하는 복잡성 및 디버깅 문제를 줄이기 위해, 로직을 독립 파일로 분리하는 것이 유리한가? 분리한다면 어떤 범위와 검증 경계를 유지해야 하는가?

## Scope

- `.github/workflows/ci-lite.yml`의 현재 step 구성, workflow 전용 inline shell, `.github/workflows/classify_changes.sh`의 change-impact 분류를 조사했다.
- 관련 테스트인 `tests/scripts/test_ci_classifier.py`와 repository CI policy의 Markdown·Inbox·route 검증 계약을 대조했다.
- PR #251 최신 CI 실패 기록에서 workflow 구조와 실제 실패 원인을 분리해 분석했다.

### Out of Scope

- CI workflow나 스크립트 구현 변경, 실패 수정, 새 branch에서의 구현 계획 확정.
- GitHub Actions provider 교체, 새 CI framework 도입, branch protection 변경.

## Findings

### Workflow complexity is concentrated in two different surfaces

`ci-lite.yml`은 이미 job의 step별 책임을 분리하고 있지만 일부 step 안에 Bash 배열, 변경 파일 수집, 조건부 후속 검사, 결과 요약 작성과 테스트 target 구성 로직이 들어 있다. 별도로 `classify_changes.sh`는 변경 경로를 검사 범위와 target으로 매핑하는 상당한 로직을 보유한다. 그러므로 “workflow 안에 모든 로직이 있다”기보다는, provider orchestration과 일반-purpose 분류 로직이 workflow YAML 및 workflow 경로의 Bash 파일에 나뉘어 있다.

Classifier는 `--stdin` 입력과 출력 계약을 제공하고 `tests/scripts/test_ci_classifier.py`에서 직접 실행해 검증한다. 특히 workflow 변경이 classifier 테스트를 선택하는지, 미지 경로가 넓은 검사로 fail-safe 되는지, route-only 변경이 필요한 route validation만 선택하는지 검증하는 구조가 이미 있다. Inline step의 내용은 그에 상응하는 독립 테스트 surface가 약하다.

#### Workflow Evidence

- [CI Lite workflow](../../.github/workflows/ci-lite.yml)
  - Markdown 수집·format diff 요약, 변경 JSON/TOML/Python 파일 수집, lint/type check, 테스트 target 인자 구성은 inline shell을 사용한다.
  - workflow는 PR trigger, 최소 권한, concurrency, step 조건 및 검증 도구 실행을 소유한다.
- [Change classifier](../../.github/workflows/classify_changes.sh)
  - 경로별 영향 범위, 테스트/type targets와 fail-safe fallback을 계산한다.
- [Classifier tests](../../tests/scripts/test_ci_classifier.py)
  - classifier를 stdin으로 구동해 출력 계약과 영향 라우팅을 결정론적으로 검증한다.

### The observed CI failure was a contract mismatch, not an inline-shell defect

관찰된 PR #251 CI에서 Markdown 단계는 Inbox를 포함한 변경 Markdown 전체에 `rumdl fmt`를 실행했다. 두 `.local/artifacts` 링크 진단과 오래된 상대 경로·fragment 진단은 format 단계의 출력으로 나타났지만, 이 workflow 단계는 Markdown lint를 `docs/**`에만 적용하며 formatting-only diff는 non-blocking으로 요약한다. 로그상 job은 이후 단계로 계속 진행했다.

실패한 route validation은 `skills-lock.json`을 route generator에 전달했고, generator는 각 Skills CLI 항목에서 `ref`와 `skillPath`를 요구했다. 당시 `langfuse` 항목에는 그 값이 없어 `incomplete Skills CLI lock entry`로 실패했다. 이 실패를 고치는 방법은 lock 생성 형식과 소비자의 계약을 일치시키는 것이다. route command를 별도 파일로 옮겨도 입력 검증 규칙은 그대로라면 같은 실패가 발생한다.

다만 별도 route command가 검증 대상을 명확히 분리하고, malformed lock의 source-aware 진단이나 정확한 생성기 계약 테스트를 제공하도록 개선된다면 발견과 수정은 쉬워질 수 있다. 이는 구현 범위가 명시되어야 하는 별도 개선이지, 단순 파일 이동의 결과는 아니다.

#### Failure Evidence

- [CI Lite workflow](../../.github/workflows/ci-lite.yml)
  - Markdown 단계의 `rumdl check` 대상은 `docs/*`이며, formatting drift는 diff summary로만 남긴다.
  - route step은 `scripts/generate_agent_routes.py --check`를 실행한다.
- [Route generator](../../scripts/generate_agent_routes.py)
  - `skills_cli_dependency_sources()`는 `sourceType`, source, `ref`, `skillPath`를 입력 계약으로 요구한다.
- [PR #251 CI run](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37008116125)
  - `CI Lite`는 route step의 `incomplete Skills CLI lock entry: langfuse`로 종료됐다.
  - 같은 run의 Markdown format 출력에는 링크 진단이 있었으나 해당 단계는 이를 fatal check로 취급하지 않고 뒤 단계가 실행됐다.

### Selective extraction improves local verification when logic has an independent contract

복잡성의 원인은 파일 위치 자체가 아니라 숨겨진 입력·출력 계약, 복제된 로직, 그리고 검증 불가능한 조건 분기다. workflow 외부에서도 실행 가능하고 입력·출력이 명확한 로직은 독립 스크립트로 두면 같은 입력에 대한 local 재현, 단위/계약 테스트, 더 읽기 쉬운 workflow diff가 가능하다. 반대로 단순한 `tool command files...` 호출이나 Actions expression을 얇게 전달하는 wrapper까지 파일로 분리하면 파일 수와 호출 계층만 늘어난다.

분리 후보 중 change-impact 분류는 이미 독립 스크립트와 테스트가 있으므로 구조를 더 쪼개기보다 테스트와 workflow 출력 계약을 유지하는 것이 우선이다. Workflow 내 Bash는 반복되는 path collection, shell branching, summary generation, target 조립을 함수형 CLI 계약으로 분리할 때 이득이 크다. GitHub 전용 출력 파일(`GITHUB_OUTPUT`, `GITHUB_STEP_SUMMARY`), `$GITHUB_ENV`, `HEAD^1 HEAD` 비교와 workspace 상대 경로는 명시적 인자로 전달해야 local 실행 가능성과 CI 동일성을 함께 지킬 수 있다.

### Separation should preserve evidence boundaries and admission strictness

이 repository의 CI 계약은 `main` 병합 판단에 필요한 검증만 blocking하고, 불확실한 impact는 넓히거나 실패하도록 요구한다. 또한 changed Inbox artifact의 frontmatter/name contract는 blocking일 수 있지만, Inbox Markdown lint 자체는 admission 조건이 아니다. 따라서 독립 스크립트는 기존 blocking 여부를 바꾸지 않고 동일한 change set과 prospective merge tree를 대상으로 해야 한다.

새 스크립트는 동작 계약 단위로 직접 테스트하고, workflow는 해당 스크립트가 선택된 조건 및 호출 인자를 검증해야 한다. Workflow trigger, least-privilege permissions, cancellation/concurrency와 admission step ordering은 GitHub Actions 고유 책임이므로 YAML에 남겨야 한다. 모든 inline command를 하나의 범용 runner로 옮기는 것은 실패 경계를 불투명하게 만들 수 있다.

#### Policy Evidence

- [CI policy](../../docs/development/ci.md)
  - 영향 불확실 시 검증 확대 또는 fail-safe, Markdown과 Inbox의 blocking 경계를 구분한다.
- [Inbox guidance](../AGENTS.md)
  - artifact 내용·구조·lifecycle은 Inbox contract를 따르며 CI는 현재 변경 artifact만 검증한다.
- [Classifier tests](../../tests/scripts/test_ci_classifier.py)
  - workflow와 routing script 간의 동작 연결을 검증하는 기존 패턴을 제공한다.

## Options

| Criterion | Inline logic 유지 | 복잡한 step 로직만 독립화 | 모든 step을 script로 이동 |
| --- | --- | --- | --- |
| Workflow 가독성 | 복잡 분기에서 낮음 | orchestration과 세부 동작의 경계가 명확 | YAML은 얇아지나 실행 흐름이 여러 파일에 분산 |
| Local 재현 | GitHub context에 강하게 결합될 수 있음 | 입력값을 주입하면 가능 | wrapper 층까지 옮기면 호출 맥락 추적이 어려울 수 있음 |
| 테스트 용이성 | YAML parse 외에 로직 단위 검증이 어려움 | 독립 contract test 가능 | 가능하나 각 wrapper까지 테스트할 경우 중복 우려 |
| 변경 비용 | 작은 step은 가장 낮음 | 반복·분기·파일 처리를 가진 step에 적정 | 파일, 인자와 계약 유지 비용이 큼 |
| 이번 실패 해결 효과 | 해당 없음 | 진단 개선은 가능, schema 오류 자체는 별도 수정 필요 | 파일 이동만으로는 해결되지 않음 |

## Implications

새 구현 PR은 CI 전체 재구성이 아니라 `ci-lite.yml`의 가장 큰 inline shell 책임을 작은 독립 CLI로 옮기고, 기존 classifier는 유지하는 단계적 접근이 적합하다. 우선 순위 후보는 changed paths 입력 정규화/validation orchestration과 formatting diff 요약처럼 테스트 가능한 순수 로직이다. 단, 본 조사만으로 어느 step을 먼저 분리할지 확정하지 않는다. 구현 전에 각 후보의 입력, 출력, 종료 코드, 파일시스템 효과와 blocking semantics를 명시해야 한다.

Acceptance를 판단할 때는 새 스크립트 단위 테스트뿐 아니라 prospective merge 환경에서 기존 PR CI와 동일한 파일 집합·검사 결과를 선택하는지 확인해야 한다. Route lock schema 불일치는 이 CI 구조 개선 PR과 별도 원인/해결 항목으로 유지한다. Workflow 변경은 classifier contract test 및 workflow YAML/command wiring 검증을 포함해야 한다.

## Open Questions

- workflow inline code에서 현재 가장 큰 운영 비용을 만드는 책임은 무엇인가?
  - 후보별 실행 빈도, 실패 이력, 로컬 재현 곤란성, 코드 복잡성을 비교해 첫 분리 대상을 정한다.
- 향후 route lock schema mismatch는 route generator 입력 계약의 변경인지 Skills CLI lock metadata 생성/보완 문제인지?
  - 사용 중인 Skills CLI 버전의 공식 lockfile schema 또는 저장소가 고정한 자산 생성 경로와 대조한다. 이 답은 별도 수정 범위를 바꾸지만 일반 workflow 분리의 근거를 바꾸지는 않는다.
- GitHub 전용 환경 정보는 어떤 인터페이스로 주입할 것인가?
  - 스크립트가 직접 환경 변수를 읽는 것보다 changed path list, output/summary destination과 base/head를 인자로 전달하는 방법이 local testability에 유리한지 구현 설계에서 결정한다.
