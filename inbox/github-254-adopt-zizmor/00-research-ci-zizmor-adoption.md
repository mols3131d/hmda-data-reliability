---
type: research
title: "Zizmor Adoption Research"
description: "GitHub Actions 보안 검증에 zizmor를 도입할 가치, 최소 admission 범위와 구현 경계를 심층 조사한다."
tags:
  - ci
  - github-actions
  - security
  - zizmor
---

# Zizmor Adoption Research

> [!NOTE]
> `zizmor` 도입을 권장한다. 현재 repository에는 GitHub Actions의 trigger, expression injection, action pinning, token permission과 supply-chain 패턴을 전용으로 검사하는 merge-blocking 계층이 없다. PR #254에서는 **workflow 또는 local action 정의가 바뀔 때만 실행되는, config-free offline `regular` persona blocking gate**를 채택하는 것이 가장 작고 강한 변경이다.

## Question

`hmda-data-reliability`의 현재 CI와 tooling 구조에서 `zizmor`를 도입할 가치가 있는가? 도입한다면 어떤 실행 방식, impact routing, baseline remediation과 예외 정책을 사용해야 최소 비용으로 `main` admission을 보호할 수 있는가?

## Scope

- PR #254의 base `5532dca2fd93696d40ba870471fa2359c5662335`와 현재 `CI Lite`
- `.github/workflows/ci-lite.yml`, `.github/workflows/classify_changes.sh`, `tests/scripts/test_ci_classifier.py`
- repository CI, bootstrap/tooling과 Lefthook 계약
- `zizmor` v1.30.1의 설치, input collection, persona, configuration, audit와 GitHub Actions integration 계약
- 현재 workflow에 대한 baseline finding의 source-level 확인
- 동시에 열려 있는 PR #253이 이 계획의 target path에 미치는 통합 위험

### Out of Scope

- Python/application 보안을 다루는 범용 SAST 도입
- GitHub Advanced Security, SARIF upload 또는 repository ruleset 변경
- online audit를 PR merge gate로 강제하는 것
- 기존 Node tooling을 zizmor 도입만을 이유로 lockfile 체계로 재설계하는 것
- Lefthook 또는 IDE에 zizmor를 필수 설치하는 것

## Findings

### Zizmor는 현재 validation stack과 겹치지 않는 GitHub Actions 전용 보안 계층이다

현재 repository는 Ruff, ty, Tach, pytest, schema/format validator와 change-impact routing을 사용하지만 GitHub Actions의 보안 의미론을 전용으로 검사하지 않는다. `zizmor`는 workflow와 action 정의를 이해하고 `dangerous-triggers`, `template-injection`, `excessive-permissions`, `unpinned-uses`, `artipacked`, `cache-poisoning`, `adhoc-packages` 등 Actions 특화 audit을 제공한다.

이 역할은 Ruff, ty, Tach, pytest와 대체 관계가 아니다. 범용 pattern engine으로 일부 규칙을 복제할 수는 있지만 GitHub Actions 보안이 목적일 때는 upstream이 workflow 의미론과 remediation을 소유하는 전용 analyzer가 더 좁고 유지 비용이 낮다.

#### Evidence

- [`DEVELOPMENT.md`](../../DEVELOPMENT.md): 현재 repository tooling과 validation stack
- [`docs/development/ci.md`](../../docs/development/ci.md): merge admission, least privilege와 external trust boundary 계약
- [`zizmor` Audit Rules](https://docs.zizmor.sh/audits/): Actions 특화 audit과 offline 지원 범위

### v1.30.1은 현재 채택할 수 있는 안정 release이며 `uvx`가 repository 구조에 가장 잘 맞는다

2026-10-05 조사 시점의 최신 안정 release는 `v1.30.1`이고 GitHub release는 immutable release로 표시된다. `v1.27.0`의 GitHub credential logging 결함은 `v1.28.0`에서 수정됐으며 upstream release note는 다른 버전은 영향받지 않았다고 명시한다.

공식 설치 문서는 PyPI와 `uvx zizmor`를 지원한다. 공식 GitHub Actions manual integration도 `setup-uv` 이후 `uvx "zizmor@${ZIZMOR_VERSION}"` 실행을 예시로 사용한다. 현재 `CI Lite`가 이미 SHA-pinned `astral-sh/setup-uv`를 사용하므로 별도의 `zizmorcore/zizmor-action` trust boundary나 project dependency를 추가할 필요가 없다.

GitHub release binary를 직접 내려받아 checksum과 platform compatibility를 별도로 관리하는 방식은 upstream 문서도 일반 사용자에게 권장하지 않는다. 이 repository에서는 exact PyPI version을 `uvx`로 요청하는 쪽이 더 작다.

#### Evidence

- [`zizmor` v1.30.1 release](https://github.com/zizmorcore/zizmor/releases/tag/v1.30.1)
- [`zizmor` Release Notes](https://docs.zizmor.sh/release-notes/)
- [`zizmor` Installation](https://docs.zizmor.sh/installation/)
- [`zizmor` GitHub Actions integration](https://docs.zizmor.sh/integrations/#github-actions)

### Merge gate는 offline `regular` persona와 GitHub annotations 조합이 적절하다

PR admission에는 다음 성질이 필요하다.

- network/API 상태와 GitHub token 없이 정적 보안 finding을 판정한다.
- malformed workflow/action이 warning으로 흘러가지 않는다.
- GitHub Actions 정의만 검사해 scope를 명확히 한다.
- finding이 있으면 step 자체가 non-zero로 실패한다.
- GitHub UI에는 annotation을 제공하되 `security-events: write` 권한을 추가하지 않는다.

이를 만족하는 후보 command는 다음과 같다.

```bash
uvx "zizmor@${ZIZMOR_VERSION}" \
  --offline \
  --strict-collection \
  --collect=workflows,actions \
  --persona=regular \
  --no-config \
  --format=github \
  .
```

`--offline`은 token이 환경에 존재해도 online audit으로 확장되지 않게 한다. `--strict-collection`은 collected input의 parse 실패를 차단한다. `--collect=workflows,actions`는 Dependabot/pre-commit 같은 인접 surface를 이번 admission contract에 끌어들이지 않는다.

`regular`은 upstream 기본 persona이며 false positive에 민감한 actionable finding 집합을 목표로 한다. 따라서 초기 도입에서 `--min-severity`로 low finding을 추가로 버리지 않는다. 특히 이번 baseline에서 중요한 `adhoc-packages`는 v1.30.1 source 기준 `Low` severity, `High` confidence이므로 severity filter는 의도적으로 보호 범위를 약화시킨다.

`--format=github`는 annotations를 만들면서 일반 exit-code semantics를 유지한다. 반대로 SARIF 출력은 finding이 있어도 audit 자체는 exit 0이므로 별도 code-scanning ruleset 없이 현재 blocking contract에 맞지 않는다.

#### Evidence

- [`zizmor` Usage](https://docs.zizmor.sh/usage/): collection, strict collection, operating mode, persona와 exit-code 계약
- [`zizmor` GitHub Actions integration](https://docs.zizmor.sh/integrations/#github-actions): annotations와 SARIF의 차이
- [`finding.rs` at v1.30.1](https://github.com/zizmorcore/zizmor/blob/v1.30.1/crates/zizmor/src/finding.rs): `Regular` persona가 기본값이며 actionable/minimal-false-positive 용도임을 명시

### 초기 gate는 configuration file 없이 고정하는 편이 안전하다

`zizmor.yml`은 audit 전체 disable, ignore와 severity remap을 지원한다. 유용한 확장점이지만 도입 시점부터 config를 만들면 merge gate를 약화시키는 별도 policy surface가 생긴다. 현재 필요한 예외는 최대 한 곳의 기존 npm install이고, broad configuration이 필요하다는 근거는 없다.

따라서 초기 gate는 `--no-config`로 local/global config discovery를 명시적으로 차단한다. 실제 baseline에서 정당한 legacy exception이 확인될 때만 finding span에 인접한 inline `# zizmor: ignore[...]`를 사용한다. Rule 전체 disable이나 repository-wide ignore는 기본값으로 만들지 않는다.

#### Evidence

- [`zizmor` Configuration](https://docs.zizmor.sh/configuration/): `--no-config`, rule disable/ignore/remap 계약과 broad disable 경고
- [`zizmor` Usage — ignoring results](https://docs.zizmor.sh/usage/#ignoring-results): inline ignore 지원

### 현재 workflow의 action tag 두 곳은 `unpinned-uses` remediation 대상이다

현재 `CI Lite`의 `rvben/rumdl`과 `astral-sh/setup-uv`는 full SHA로 고정돼 있지만 다음 두 action은 mutable tag reference다.

| Action | Current ref | Verified tag target |
| --- | --- | --- |
| `actions/checkout` | `v6.0.2` | `de0fac2e4500dabe0009e67214ff5f5447ce83dd` |
| `actions/setup-python` | `v6.2.0` | `a309ff8b426b58ec0e2a45f0f869d46889d02405` |

`zizmor`의 current hash-pin policy와 GitHub secure-use guidance 모두 full commit SHA를 선호한다. 구현에서는 위 검증된 tag target으로 변경하고 기존 repository style처럼 `# v6.0.2`, `# v6.2.0` comment를 유지하는 것이 명확하다.

#### Evidence

- [`.github/workflows/ci-lite.yml`](../../.github/workflows/ci-lite.yml)
- [`unpinned-uses` source at v1.30.1](https://github.com/zizmorcore/zizmor/blob/v1.30.1/crates/zizmor/src/audit/unpinned_uses.rs)
- [GitHub Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [`actions/checkout` v6.0.2 tag ref](https://api.github.com/repos/actions/checkout/git/ref/tags/v6.0.2)
- [`actions/setup-python` v6.2.0 tag ref](https://api.github.com/repos/actions/setup-python/git/ref/tags/v6.2.0)

### 현재 lockless npm install은 v1.30.1 `adhoc-packages` 판정 조건에 들어간다

`CI Lite`에는 다음 step이 있다.

```bash
npm install --prefix .local/tooling --no-save --package-lock=false @biomejs/biome@2 tombi@1
```

v1.30.1 `adhoc-packages` source는 `npm install` 계열에서 package argument가 존재하면 finding을 만든다. 같은 source는 `npx`를 현재 검사하지 않으므로 `npm exec --yes --package @fission-ai/openspec@1.12.0`은 이 audit의 대상이 아니다. 즉 실제 CLI를 아직 실행하지 못했더라도 현재 structured-data install은 rule 구현 조건에 들어간다는 점은 source-level로 확인했다.

다만 이 install은 우연한 CI 편의가 아니다. [`scripts/bootstrap.py`](../../scripts/bootstrap.py)와 [`docs/development/tooling/bootstrap.md`](../../docs/development/tooling/bootstrap.md)가 Biome/Tombi를 `.local/tooling`에 lockless repository-local tool로 복원하는 현재 계약을 소유한다. zizmor 도입만을 위해 `package.json`/lockfile 체계를 새로 만드는 것은 scope 확장이다.

따라서 실제 baseline scan에서 이 finding이 확인되면 우선순위는 다음과 같다.

1. finding이 예상한 exact install인지 확인한다.
1. 기존 bootstrap contract가 여전히 의도된 것인지 재확인한다.
1. 의도된 예외라면 해당 `run:` finding span에 `adhoc-packages` inline ignore와 짧은 rationale만 남긴다.
1. 새로운 package-management 설계가 필요하다고 판단되면 이 PR에서 임의 확장하지 않고 별도 결정으로 분리한다.

#### Evidence

- [`adhoc_packages.rs` at v1.30.1](https://github.com/zizmorcore/zizmor/blob/v1.30.1/crates/zizmor/src/audit/adhoc_packages.rs)
- [`zizmor` `adhoc-packages` documentation](https://docs.zizmor.sh/audits/#adhoc-packages)
- [`scripts/bootstrap.py`](../../scripts/bootstrap.py)
- [`docs/development/tooling/bootstrap.md`](../../docs/development/tooling/bootstrap.md)

### Impact routing은 workflow와 local action definition을 선택하고 전체 current surface를 scan해야 한다

현재 repository에는 `.github/workflows/ci-lite.yml` 하나가 있고 `action.yml`/`action.yaml` local action은 없다. 그러나 gate의 의미는 현재 한 파일을 검사하는 것이 아니라 GitHub Actions 정의의 보안 회귀를 차단하는 것이다.

따라서 classifier의 새 `zizmor` output은 다음 변경을 선택하는 것이 적절하다.

- `.github/workflows/*.yml`
- `.github/workflows/*.yaml`
- repository root 또는 nested directory의 `action.yml`
- repository root 또는 nested directory의 `action.yaml`

선택된 경우에는 changed file 하나만 zizmor에 넘기지 않고 `--collect=workflows,actions .`로 prospective merge의 **전체 current workflow/action surface**를 검사한다. 이렇게 하면 삭제/rename이나 shared security assumption 변화에도 남아 있는 정의가 함께 검증된다. 반대로 unrelated Python/Markdown 변경은 zizmor 비용을 지불하지 않는다.

Classifier 자체의 변경은 zizmor 실행 대상이 아니어도 된다. 대신 selector와 workflow wiring을 deterministic test로 고정해 classifier 수정이 zizmor coverage를 조용히 제거하지 못하게 해야 한다.

### Existing `setup-uv`를 재사용하되 action-only 변경에서도 빠지지 않아야 한다

현재 workflow 변경은 기존 `tests`/`tach` selector 때문에 `Set up uv`가 실행되지만 future `action.yml`만 추가되는 변경은 기존 selector만으로 uv 준비가 보장되지 않는다. `zizmor` output을 `Set up uv` step 조건에 추가해야 한다.

zizmor는 project Python dependency가 아니므로 `uv sync --locked`, `pyproject.toml` 또는 `uv.lock` 변경은 필요하지 않다. 이 구분은 작은 validation tool을 application/dev dependency graph에 불필요하게 넣지 않는다.

### Lefthook, online audits와 별도 zizmor Action은 초기 도입에 필요하지 않다

Lefthook은 local runtime을 사용할 수 있는 기여자에게 빠른 feedback을 제공하지만 merge-critical 검증은 CI가 다시 소유한다. GitHub Actions 변경 빈도가 낮고 zizmor는 PyPI tool resolution이 필요하므로 매 pre-push에 강제할 실익이 아직 없다.

Online audits는 GitHub API/token과 외부 상태를 추가하며 이번 merge-critical baseline에 필요한 증거보다 비싸다. 별도 `zizmorcore/zizmor-action`도 기능상 필요하지 않고 새 third-party action trust boundary를 만든다. 초기 PR에서는 모두 제외한다.

### Concurrent PR #253은 계획의 path-level freshness risk다

현재 authoritative `main`에는 classifier가 `.github/workflows/classify_changes.sh`에 있다. 동시에 열린 Draft PR #253은 CI shell logic을 `scripts/ci/`로 이동하고 CI contract tests도 재구성하고 있다. #253은 아직 `main` authority가 아니므로 PR #254의 현재 계획은 `main` 구조를 기준으로 한다.

다만 #253이 먼저 병합되면 zizmor의 목적과 acceptance는 그대로지만 구현 target path와 classifier test 위치가 stale해진다. 그 경우 literal patch를 그대로 적용하지 말고 구현 시작 전에 새 `main`의 CI owner와 tests를 다시 찾아 같은 contract를 가장 작은 형태로 투영해야 한다.

#### Evidence

- [PR #253](https://github.com/mols3131d/hmda-data-reliability/pull/253): CI script extraction과 contract-test 재구성 진행 중

### Direct baseline execution은 현재 조사 환경에서 완료하지 못했다

심층 조사 중 현재 실행 환경에서 `uvx zizmor@1.30.1 --version`을 직접 실행해 baseline 재현을 시도했다. 그러나 외부 DNS/PyPI 접근이 없어 package fetch 단계가 실패했다. 이는 zizmor finding 결과가 아니며 repository 문제의 증거로 사용하지 않는다.

따라서 실제 CLI baseline은 구현 단계의 첫 validation으로 남긴다. 이번 조사에서 확정한 것은 upstream v1.30.1 contract와 source-level matching, 현재 workflow state, action tag target과 repository-owned tooling boundary다.

## Options

| Criterion | Conditional offline gate | Every-PR offline gate | Online/SARIF gate |
| --- | --- | --- | --- |
| Actions security regression 차단 | 충족 | 충족 | 충족 가능 |
| Unrelated PR 비용 | 가장 낮음 | 불필요한 반복 | 가장 높음 |
| Token/extra permission | 없음 | 없음 | 필요할 수 있음 |
| Finding 자체로 blocking | 직접 가능 | 직접 가능 | SARIF는 별도 ruleset 필요 |
| 현재 CI 원칙과 정합성 | 가장 높음 | 보통 | 낮음 |

**Recommended:** workflow/action definition 변경에만 실행되는 config-free offline annotations gate.

## Implications

- 구현은 actual v1.30.1 baseline scan부터 시작해야 한다. 예상과 다른 material finding이 있으면 먼저 원인을 조사하고 계획을 갱신한다.
- `actions/checkout`과 `actions/setup-python`은 verified SHA로 pin한다.
- `adhoc-packages`가 예상한 Node tooling install 한 곳에만 발생한다면 기존 tooling contract를 보존하는 좁은 inline ignore를 우선한다.
- classifier에는 `zizmor` scope를 추가하고 workflow/action path를 deterministic regression test로 고정한다.
- `Set up uv`는 `zizmor`-only 변경에서도 실행돼야 하며 `uv sync`는 요구하지 않는다.
- `zizmor.yml`, severity filter, SARIF, online token, Lefthook, 새 GitHub Action은 이번 PR에 추가하지 않는다.
- Active tooling inventory는 실제 구현 완료 시 `DEVELOPMENT.md`와 맞추되 upstream 일반 사용법을 repository docs에 복제하지 않는다.

## Open Questions

- 실제 v1.30.1 offline baseline이 source-level 예상 외의 finding을 만드는가?
  - 구현 환경에서 exact command를 실행해야 확정할 수 있다.
- 구현 시작 전에 PR #253이 `main`에 병합됐는가?
  - 병합됐다면 classifier와 CI contract-test target path를 새 base에서 다시 계산한다.
