---
type: research
title: "Zizmor Adoption Research"
description: "GitHub Actions 보안 검증에 zizmor를 도입할 가치와 이 PR에서 채택할 최소 범위를 조사한다."
tags:
  - ci
  - github-actions
  - security
  - zizmor
---

# Zizmor Adoption Research

> [!NOTE]
> `zizmor` 도입을 권장한다. 현재 validation stack에는 GitHub Actions의 trigger, expression injection, action pinning, token permission과 supply-chain 패턴을 전용으로 검사하는 계층이 없으며, `zizmor`는 이 공백을 낮은 실행 비용의 정적 검사로 채운다. 이 PR에서는 **workflow/action 정의가 바뀔 때 실행되는 offline blocking gate**를 최소 범위로 채택하고, 기존 workflow에서 드러나는 baseline finding을 실제 scan으로 확정한 뒤 필요한 remediation 또는 명시적 예외만 함께 처리하는 방향이 적절하다.

## Question

`hmda-data-reliability`의 현재 CI 구조와 validation stack에서 `zizmor`를 도입할 가치가 있는가? 도입한다면 이 PR의 완료 범위를 어디까지로 제한해야 하는가?

## Scope

- `main`에서 분기한 `agent/chore/adopt-zizmor`의 기준 revision `5532dca2fd93696d40ba870471fa2359c5662335`
- 현재 GitHub Actions workflow와 change classifier
- repository CI 원칙, bootstrap/tooling 경계와 Lefthook 역할
- `zizmor` v1.30.1의 공식 설치·usage·audit 계약
- merge admission에 필요한 최소 integration 범위

### Out of Scope

- Python/application security 전반을 다루는 범용 SAST 도입
- GitHub Advanced Security 또는 SARIF/code scanning 체계 확장
- repository settings의 Actions 정책 변경
- online audit를 merge gate로 강제하는 설계

## Findings

### Zizmor는 현재 validation stack과 겹치지 않는 GitHub Actions 전용 보안 계층이다

현재 repository는 Ruff, ty, Tach, pytest, schema/format validator와 `CI Lite`의 change-impact routing을 사용하지만 GitHub Actions의 보안 의미론을 전용으로 검사하는 도구는 없다. Repository 검색에서도 `zizmor` 사용 흔적은 확인되지 않았다.

`zizmor`는 workflow/action 정의를 정적으로 분석하며 `dangerous-triggers`, `template-injection`, `excessive-permissions`, `unpinned-uses`, `artipacked`, `cache-poisoning`, `adhoc-packages` 등 GitHub Actions 특화 audit을 제공한다. 다수 핵심 audit은 offline으로 동작한다.

이 역할은 Ruff/ty/Tach/pytest와 대체 관계가 아니다. Semgrep 같은 범용 pattern engine으로 일부 규칙을 재구현할 수는 있지만, GitHub Actions 보안 자체가 목적이면 workflow 의미론과 remediation 지식을 이미 가진 전용 analyzer를 사용하는 편이 단순하고 유지 비용이 낮다.

#### Evidence

- [`DEVELOPMENT.md`](../../../DEVELOPMENT.md): 현재 repository tooling과 validation stack
- [`docs/development/ci.md`](../../../docs/development/ci.md): merge admission, 최소 권한, third-party action을 trust boundary로 취급하는 CI 계약
- [`zizmor` Audit Rules](https://docs.zizmor.sh/audits/): Actions 전용 audit 목록과 각 audit의 offline 지원 여부
- [`zizmor` Usage](https://docs.zizmor.sh/usage/): workflow/action 정의만 분석하는 정적 분석 도구라는 범위와 한계

### 현재 CI는 보안 기본기가 좋지만 zizmor가 보호할 회귀 표면이 실제로 존재한다

현재 `CI Lite`는 `pull_request` trigger, top-level `permissions: contents: read`, `timeout-minutes`, concurrency cancellation을 사용한다. Checkout은 `persist-credentials: false`이고 `rvben/rumdl`, `astral-sh/setup-uv`는 full commit SHA로 고정되어 있다. 이는 repository의 최소 권한과 trust-boundary 원칙에 부합한다.

반면 `actions/checkout@v6.0.2`와 `actions/setup-python@v6.2.0`은 tag reference를 사용한다. `zizmor` v1.20.0 이후 `unpinned-uses` 기본 정책은 GitHub 공식 `actions/*`를 포함한 모든 action에 full SHA pinning을 요구하므로 두 참조는 기본 설정에서 finding이 될 것으로 예상된다. GitHub 공식 보안 문서도 full-length commit SHA가 action을 immutable release로 사용하는 유일한 방식이라고 설명한다.

현재 tag가 가리키는 commit은 다음과 같이 확인했다.

| Action | Current ref | Verified tag target |
| --- | --- | --- |
| `actions/checkout` | `v6.0.2` | `de0fac2e4500dabe0009e67214ff5f5447ce83dd` |
| `actions/setup-python` | `v6.2.0` | `a309ff8b426b58ec0e2a45f0f869d46889d02405` |

따라서 zizmor 도입은 현재 취약한 workflow를 새로 구조화하는 작업이라기보다, 이미 갖춘 안전한 패턴이 이후 변경에서 퇴행하지 않도록 deterministic하게 고정하는 성격이 강하다.

#### Evidence

- [`.github/workflows/ci-lite.yml`](../../../.github/workflows/ci-lite.yml): trigger, permissions, action references와 credential 설정
- [`unpinned-uses`](https://docs.zizmor.sh/audits/#unpinned-uses): v1.20.0 이후 모든 action에 적용되는 기본 hash-pinning 정책
- [GitHub Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use): full-length SHA pinning 권고와 immutable reference 설명
- [`actions/checkout` v6.0.2 tag ref](https://api.github.com/repos/actions/checkout/git/ref/tags/v6.0.2)
- [`actions/setup-python` v6.2.0 tag ref](https://api.github.com/repos/actions/setup-python/git/ref/tags/v6.2.0)

### `adhoc-packages` 예상 finding은 기존 tooling 계약과 충돌하므로 실제 scan 뒤 별도로 판정해야 한다

`CI Lite`에는 다음 lockless install이 있다.

```bash
npm install --prefix .local/tooling --no-save --package-lock=false @biomejs/biome@2 tombi@1
```

`zizmor`의 `adhoc-packages`는 managed/locked manifest 밖에서 실행하는 `npm install`을 탐지하며, 공식 remediation은 lockfile을 생성하는 manifest에 package를 두고 lockfile-aware install을 사용하는 것이다.

그러나 이 repository에서는 이 패턴이 CI에만 우연히 존재하는 것이 아니다. `scripts/bootstrap.py`가 Biome과 Tombi를 `.local/tooling`에 repository-local tool로 설치하며 `--no-save --package-lock=false`를 명시적으로 사용하고, `docs/development/tooling/bootstrap.md`도 이 local Node tool 복원 경계를 문서화한다. 따라서 zizmor finding이 실제로 발생하더라도 곧바로 package manifest/lockfile을 추가하면 기존 tooling ownership을 불필요하게 재설계할 수 있다.

이 항목은 실제 `zizmor` 결과를 확인한 뒤 다음 두 선택지 중 더 작은 coherent change를 택해야 한다.

| Option | 장점 | 비용/위험 | 현재 판단 |
| --- | --- | --- | --- |
| Node tooling을 lockfile 기반으로 재설계 | `adhoc-packages` 원인을 구조적으로 제거 | bootstrap/tooling 계약과 dependency 관리 범위까지 넓어짐 | 이 PR의 기본값으로는 과함 |
| 해당 intentional install에 `adhoc-packages`만 좁게 ignore | zizmor gate를 유지하면서 기존 tooling 계약 보존 | 예외 근거가 코드에 남고 향후 재검토 필요 | 실제 finding이면 우선 검토 |

`zizmor`는 `# zizmor: ignore[adhoc-packages]` 같은 one-off inline ignore를 공식 지원한다. 예외가 필요하다면 rule 전체를 끄거나 broad config를 추가하기보다 finding span에 가장 좁게 남기는 편이 repository의 evidence-first 원칙과 맞다.

#### Evidence

- [`.github/workflows/ci-lite.yml`](../../../.github/workflows/ci-lite.yml): structured-data tooling install step
- [`scripts/bootstrap.py`](../../../scripts/bootstrap.py): `NODE_TOOL_PACKAGES`, `_install_node_tools()`와 lockless local install 계약
- [`docs/development/tooling/bootstrap.md`](../../../docs/development/tooling/bootstrap.md): `.local/tooling` 기반 repository-local Node tool 경계
- [`adhoc-packages`](https://docs.zizmor.sh/audits/#adhoc-packages): direct package install의 위험과 lockfile 기반 remediation
- [`zizmor` ignore controls](https://docs.zizmor.sh/usage/#ignoring-results): 좁은 inline ignore와 config ignore 지원

### Merge gate는 online audit보다 offline deterministic audit가 적절하다

`zizmor`는 offline, online, online sans audits 모드를 구분한다. Online mode는 GitHub API를 사용해 remote repository와 ref history를 조회하고, private repository에서는 token permission도 필요할 수 있다.

이 프로젝트의 PR CI는 "가장 싼 충분한 검증", least privilege, 외부 상태 의존 최소화를 명시적으로 선호한다. 따라서 merge-critical security regression은 먼저 offline audit으로 차단하는 것이 적절하다. Remote advisory, stale reference 등 online evidence가 추가로 유용해지면 scheduled/manual diagnostic으로 분리할 수 있다.

초기 gate 후보는 다음과 같다.

```bash
uvx zizmor@1.30.1 \
  --offline \
  --strict-collection \
  --collect=workflows,actions \
  .
```

`uvx tool@version`은 repository가 이미 사용하는 `uv`로 exact tool version을 요청할 수 있고, `--strict-collection`은 collected workflow/action의 parse/schema failure를 warning으로 흘리지 않고 실패시킨다. `--collect=workflows,actions`는 이번 PR의 목적을 GitHub Actions 정의에 한정한다.

#### Evidence

- [`docs/development/ci.md`](../../../docs/development/ci.md): 가장 싼 충분한 검증, least privilege, 외부 trust boundary 원칙
- [`zizmor` Usage](https://docs.zizmor.sh/usage/): operating mode, collection mode와 `--strict-collection`
- [`zizmor` Installation](https://docs.zizmor.sh/installation/): PyPI/uv/`uvx` 지원
- [`uv` tool version documentation](https://docs.astral.sh/uv/concepts/tools/#tool-versions): `uvx <tool>@<version>` exact-version 실행

### 이 PR의 완료 범위는 도구 추가가 아니라 admission contract까지 닫혀야 한다

`zizmor` 명령을 문서에 추가하거나 수동 실행 가능하게 만드는 것만으로는 도입이 완료되지 않는다. 이 repository에서 CI의 목적은 `main` admission에 필요한 자동 근거를 제공하는 것이므로, GitHub Actions 보안 regression을 알게 됐을 때 병합을 거부할 것이라면 PR CI의 blocking evidence가 되어야 한다.

현재 `classify_changes.sh`는 `.github/workflows/*` 변경을 이미 별도 위험 표면으로 취급해 classifier test와 Tach 관련 검증 범위를 넓힌다. zizmor도 같은 impact-routing 구조를 재사용하되, GitHub Actions 정의가 변경될 때만 실행하도록 별도 scope를 두는 편이 책임이 명확하다.

Workflow뿐 아니라 future local action 정의도 검사하려면 selector가 `action.yml`/`action.yaml` 변경을 놓치지 않아야 한다. 반대로 unrelated Python/Markdown PR마다 zizmor를 실행할 이유는 없다.

도입 완료 조건은 다음처럼 잡는 것이 적절하다.

1. `zizmor` exact version과 실행 command가 CI에 명시된다.
1. workflow/action 정의 변경이 zizmor blocking check를 반드시 선택한다.
1. 영향 범위를 판별할 수 없을 때 검사가 조용히 빠지지 않는다.
1. 현재 baseline finding을 실제 scan으로 확인하고, genuine finding은 remediation하며 intentional exception은 근거가 드러나는 가장 좁은 ignore로 처리한다.
1. workflow selector 동작은 기존 classifier test 계약 안에서 검증한다.
1. 최종 prospective merge revision에서 `CI Lite`가 통과한다.

## Options

| Criterion | Conditional offline gate | Every-PR offline gate | Online gate |
| --- | --- | --- | --- |
| Merge-critical Actions regression 방지 | 충족 | 충족 | 충족 |
| Unrelated change 비용 | 가장 낮음 | 불필요한 반복 | 가장 높음 |
| 외부 API/token 의존 | 없음 | 없음 | 있음 |
| 기존 CI 원칙과 정합성 | 가장 높음 | 보통 | 낮음 |
| 초기 운영 복잡도 | 낮음 | 낮음 | 중간 이상 |

**Recommended:** workflow/action 정의 변경에만 실행되는 conditional offline gate.

## Implications

- 구현 단계에서는 먼저 `zizmor` v1.30.1을 현재 workflow에 실제 실행해 baseline을 확정해야 한다. 이 보고서의 `unpinned-uses`와 `adhoc-packages` 항목은 공식 rule과 현재 YAML을 대조한 예상 finding이며 실제 tool output으로 가장하지 않는다.
- `actions/checkout`과 `actions/setup-python` tag reference는 실제 scan 결과와 무관하게 GitHub 공식 보안 guidance에도 부합하도록 full SHA pinning을 우선 remediation 대상으로 삼을 근거가 충분하다.
- `adhoc-packages`는 existing bootstrap contract를 바꾸지 않는 것이 기본값이다. 실제 finding이 확인되면 먼저 좁은 ignore가 정당한지 검토하고, lockfile 도입은 별도 tooling redesign 가치가 입증될 때만 범위를 넓힌다.
- 별도 `zizmor.yml`, SARIF upload, GHAS integration, scheduled online audit는 현재 완료 조건에 필요하지 않다.

## Open Questions

- 실제 `zizmor` v1.30.1 offline scan에서 현재 `ci-lite.yml`에 어떤 finding과 severity가 출력되는가?
  - 구현 환경에서 exact command를 실행해 이 보고서의 예상 baseline을 검증해야 한다.
- `adhoc-packages`가 현재 `npm install`에 실제로 발생한다면, inline ignore가 해당 step의 의도와 위험을 충분히 설명하는가?
  - finding span과 repository tooling contract를 함께 보고 최종 처리 방식을 결정한다.
