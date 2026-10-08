---
type: plan
title: "Zizmor Adoption Plan"
description: "PR #254에서 GitHub Actions 보안 회귀를 conditional offline zizmor gate로 차단하기 위한 구현 범위, 순서와 검증 기준을 정의한다."
tags:
  - ci
  - github-actions
  - security
  - zizmor
---

# Zizmor Adoption Plan

PR #254의 완료 목표는 `zizmor`를 단순히 실행 가능하게 만드는 것이 아니라, GitHub Actions workflow와 local action 정의의 보안 회귀가 `main`에 들어가기 전에 deterministic하게 차단되는 admission contract를 만드는 것이다. 구현은 현재 CI 구조를 재사용하고 새로운 security platform이나 dependency 관리 체계를 만들지 않는다.

## Context

- Admission branch는 `main`이다.
- 현재 required PR workflow는 `.github/workflows/ci-lite.yml`의 `CI Lite`다.
- 현재 impact router는 `.github/workflows/classify_changes.sh`, regression test는 `tests/scripts/test_ci_classifier.py`다.
- 현재 repository에는 workflow 한 개가 있고 local `action.yml`/`action.yaml`은 없다.
- `astral-sh/setup-uv`가 이미 CI에 SHA-pinned action으로 존재하므로 zizmor는 `uvx`로 격리 실행할 수 있다.
- zizmor v1.30.1을 adoption baseline으로 사용한다.
- 조사 근거와 trade-off는 [`00-research-ci-zizmor-adoption.md`](00-research-ci-zizmor-adoption.md)가 소유한다.
- Draft PR #253은 CI router와 test 구조를 `scripts/ci/` 중심으로 바꾸고 있다. 구현 시작 전에 `main`이 바뀌었으면 이 계획의 목적과 acceptance는 유지하되 target path를 새 authority에 맞춰 다시 계산한다.

## Goals and Non-Goals

### Goals

1. Workflow 또는 local action 정의에 actionable zizmor finding이 있으면 PR admission을 실패시킨다.
1. Workflow/action parse failure가 warning으로 숨지 않게 한다.
1. Security-relevant change에만 zizmor를 실행해 unrelated PR 비용을 늘리지 않는다.
1. Scan은 token과 write permission 없이 offline으로 실행한다.
1. 기존 workflow baseline을 clean 또는 근거 있는 최소 exception 상태로 만든다.
1. Impact routing과 workflow wiring을 deterministic tests로 보호한다.

### Non-Goals

- GitHub Advanced Security, SARIF upload, code-scanning ruleset 도입
- online audit 또는 GitHub API token 사용
- `zizmorcore/zizmor-action` 추가
- `zizmor.yml`/`zizmor.yaml` configuration 추가
- severity threshold로 finding을 추가 필터링
- Lefthook/IDE integration 강제
- Node tooling lockfile 구조 재설계
- 범용 SAST 또는 Semgrep 정책 확장

## Decisions

### Execution Contract

CI의 zizmor step은 다음 의미를 그대로 보존한다.

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

- `ZIZMOR_VERSION`은 workflow가 소유하고 `1.30.1`로 명시한다.
- `--offline`은 token 존재 여부와 무관하게 network/API audit을 금지한다.
- `--strict-collection`은 collected input parse failure를 blocking failure로 만든다.
- `--collect=workflows,actions`는 이번 contract의 input 종류를 workflow와 action definition으로 한정한다.
- `--persona=regular`은 actionable/minimal-false-positive default policy를 의도적으로 명시한다.
- `--no-config`는 별도 config file이 audit을 조용히 약화시키지 못하게 한다.
- `--format=github`는 annotation을 제공하고 finding exit code를 유지한다.
- `--min-severity`와 `--no-exit-codes`는 사용하지 않는다.

### Dependency Boundary

`zizmor`는 project dependency로 추가하지 않는다.

- `pyproject.toml`과 `uv.lock`을 변경하지 않는다.
- `uvx`가 exact zizmor version을 isolated tool로 실행한다.
- Existing `Set up uv` step을 재사용한다.
- `zizmor`-only 변경에서도 `Set up uv`가 선택되도록 조건을 확장한다.
- zizmor 실행만을 위해 `uv sync --locked`를 요구하지 않는다.

### Baseline Policy

구현 첫 단계에서 current prospective state에 exact command를 실행한다.

- `actions/checkout@v6.0.2`는 `de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2`로 pin한다.
- `actions/setup-python@v6.2.0`은 `a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0`로 pin한다.
- `adhoc-packages`가 current Biome/Tombi install에서 발생하면 기존 bootstrap contract를 다시 확인한 뒤 해당 finding span에만 inline ignore를 허용한다.
- 실제 baseline에서 예상하지 못한 finding은 먼저 genuine/false-positive/intentional legacy 상태를 판정한다. Broad disable이나 severity lowering으로 green을 만들지 않는다.
- Remediation이 Node dependency architecture, unrelated workflow redesign 또는 repository settings 변경을 요구하면 scope를 임의 확대하지 않고 blocker/후속 결정으로 분리한다.

## Failure to Evidence

| Failure class | Cheapest sufficient evidence | Admission |
| --- | --- | --- |
| Dangerous trigger, template injection, excessive permission, credential persistence 등 actionable Actions security finding | zizmor offline `regular` audit | Blocking |
| Mutable third-party `uses:` reference | `unpinned-uses` | Blocking |
| Workflow/action parse 실패 | `--strict-collection` | Blocking |
| Intentional existing lockless Node tool install | 좁은 inline ignore + repository tooling contract | Accepted exception only after baseline confirmation |
| Workflow/action 변경이 zizmor를 선택하지 않음 | classifier regression test | Blocking |
| `zizmor` selector는 true지만 uv setup 또는 audit step이 실행되지 않음 | workflow wiring test | Blocking |
| Unrelated Python/Markdown change가 zizmor를 실행함 | negative selector test | Correctness/cost regression; blocking classifier test |
| Online advisory 또는 remote ref freshness | 이번 PR에서 evidence 없음 | Non-admission / out of scope |

## CI Architecture

기존 `CI Lite` job 안에 별도 blocking step 하나만 추가한다. 새 workflow/job을 만들 이유가 없다.

```text
pull_request -> CI Lite
             -> Classify changes
                 -> zizmor=false: 기존 검증만 진행
                 -> zizmor=true
                    -> Set up uv
                    -> Audit GitHub Actions with zizmor
                    -> finding/parse error: fail
                    -> clean/ignored known exception: continue
```

### Permissions and Secrets

- 기존 `permissions: contents: read`를 확대하지 않는다.
- zizmor step에 `GH_TOKEN`, `GITHUB_TOKEN`, `ZIZMOR_GITHUB_TOKEN`을 전달하지 않는다.
- `security-events: write`를 추가하지 않는다.
- Repository write permission이나 artifact upload를 추가하지 않는다.

### Evidence Boundary

이 step은 prospective checkout의 workflow/action 정의에 대해 zizmor v1.30.1 offline `regular` audits가 clean함을 증명한다. 다음을 증명하지 않는다.

- GitHub API를 이용하는 online audit 결과
- third-party action repository 자체의 전체 supply-chain 안전성
- workflow가 실제 runner에서 성공한다는 runtime evidence
- application source의 일반 security correctness

## Impact Routing

Classifier에 `zizmor=false` boolean output을 추가한다. 다음 changed path를 만나면 `true`로 만든다.

```text
.github/workflows/*.yml
.github/workflows/*.yaml
action.yml
action.yaml
*/action.yml
*/action.yaml
```

Bash `case` pattern으로 구현할 때 nested path의 `/`까지 `*`가 의도대로 포함하는지 regression test로 고정한다. Path가 삭제된 경우에도 changed-path 이름만으로 selector가 true가 되어야 한다. zizmor 실행은 현재 repository 전체를 collect하므로 삭제 이후 남은 workflow/action surface를 검증한다.

### Representative Routing Cases

| Changed path | `zizmor` | Reason |
| --- | ---: | --- |
| `.github/workflows/ci-lite.yml` | `true` | Workflow definition |
| `.github/workflows/example.yaml` | `true` | YAML extension variant |
| `action.yml` | `true` | Root local action |
| `.github/actions/example/action.yaml` | `true` | Nested local action |
| `.github/workflows/classify_changes.sh` | `false` | Router implementation, not Actions definition |
| `src/hmda_reliability/example.py` | `false` | Unrelated source |
| `README.md` | `false` | Unrelated documentation |

Router implementation 변경이 zizmor를 직접 실행하지 않더라도 classifier tests가 selector contract를 검증하므로 coverage weakening은 test failure로 드러나야 한다.

## Implementation Plan

1. **Re-resolve current authority.** 구현 시작 시 PR #254 base/head와 current `main`을 확인한다. PR #253이 병합되어 CI router/test owner가 이동했으면 새 path에서 동일 contract로 계획을 재투영하고, old `.github/workflows/classify_changes.sh`를 되살리지 않는다.
1. **Run the baseline before remediation.** v1.30.1 exact offline command를 current checkout에서 실행하고 finding을 기록한다. 실행하지 못한 결과를 clean으로 간주하지 않는다.
1. **Classify baseline findings.** 예상 `unpinned-uses` 두 건과 `adhoc-packages`를 실제 output과 대조한다. 그 외 finding은 원인과 blast radius를 확인한 뒤 implementation scope를 결정한다.
1. **Pin current mutable action refs.** `actions/checkout`과 `actions/setup-python`을 위 verified SHA에 pin하고 version comment를 남긴다. `persist-credentials: false` 등 기존 안전 설정은 보존한다.
1. **Resolve the known Node-tool exception if present.** Actual `adhoc-packages` finding이 documented Biome/Tombi local install 한 곳과 일치하고 contract를 유지하기로 하면 finding span에 최소 inline ignore와 rationale을 둔다. Config file이나 rule disable은 만들지 않는다.
1. **Add impact routing.** Current classifier owner에 `zizmor` boolean을 추가하고 workflow/action definition patterns만 true로 만든다. Existing outputs와 unrelated routing behavior를 바꾸지 않는다.
1. **Wire setup and blocking audit.** `Set up uv` condition에 `zizmor`를 추가하고, 그 뒤에 exact-version offline audit step을 추가한다. 새 permission, secret, cache, matrix 또는 workflow를 만들지 않는다.
1. **Add deterministic routing/wiring tests.** Workflow `.yml/.yaml`, root/nested action definition, deletion-like nonexistent path와 unrelated negative cases를 검증한다. Workflow test는 `Set up uv`와 zizmor step이 `zizmor` output에 연결되고 command의 critical flags/version contract가 존재함을 확인한다.
1. **Update minimal tooling inventory.** 실제 도입 후 `DEVELOPMENT.md`의 active repository tooling이 zizmor를 누락하지 않게 한다. Exact version/CLI와 upstream 일반 사용법을 별도 guide에 복제하지 않는다. Existing CI policy가 이미 security trust boundary와 admission 원칙을 소유하므로 새로운 policy가 생기지 않는 한 `docs/development/ci.md`는 수정하지 않는다.
1. **Validate focused behavior.** Classifier/wiring tests, zizmor exact scan, affected Markdown/Inbox validation과 repository-native workflow checks를 실행한다. Baseline scan은 최종 prospective state에서도 다시 실행한다.
1. **Validate delivery revision.** 최종 head의 `CI Lite` 성공을 확인하고 PR description에 실제 수행한 evidence, remaining limitation과 exact base/head를 반영한다. Draft 상태는 인간이 별도로 Ready 전환을 요청하기 전까지 유지한다.

## Validation Matrix

| Surface | Validation |
| --- | --- |
| zizmor CLI contract | `uvx zizmor@1.30.1 ...` exact offline scan |
| Classifier routing | relevant classifier unit/contract tests |
| Workflow wiring | test that setup-uv and audit step are selected by `zizmor` output |
| Bash classifier | syntax check or repository-native CI contract test |
| Markdown/Inbox artifacts | repository Inbox validator and applicable Markdown validation |
| `DEVELOPMENT.md` change | repository Markdown formatting/lint behavior applicable to root Markdown |
| Prospective merge | current-head `CI Lite` |

Do not claim online audit, runtime execution of every workflow path, GHAS integration or full supply-chain verification from these checks.

## Acceptance Criteria

- `zizmor` v1.30.1 exact version is the CI-owned audit version.
- Workflow/action definition changes select a blocking zizmor step before merge.
- `.yml`, `.yaml`, root action and nested action representative paths are covered by deterministic selector tests.
- Unrelated Python/Markdown changes do not select zizmor.
- `zizmor`-only scope guarantees `setup-uv` is available without requiring project dependency sync.
- Audit command explicitly uses `--offline`, `--strict-collection`, `--collect=workflows,actions`, `--persona=regular`, `--no-config`, `--format=github`.
- Audit uses no GitHub token and requires no permission beyond existing checkout needs.
- `actions/checkout` and `actions/setup-python` are pinned to verified full SHA values with readable version comments.
- Final baseline has no unhandled `regular` persona finding.
- Any accepted `adhoc-packages` exception is inline, limited to the exact existing install and explains why the repository-owned bootstrap contract is intentionally preserved.
- No `zizmor.yml`, broad rule disable, severity threshold, SARIF, online audit, new zizmor action, Lefthook integration or new project dependency is introduced.
- Classifier/wiring tests pass and cannot silently omit the merge-critical audit for known Actions definition paths.
- `DEVELOPMENT.md` tooling inventory matches the actual post-change state without duplicating volatile command/version details.
- Final prospective merge `CI Lite` succeeds at the revision reported in the PR description.

## Risks and Open Decisions

### Actual Baseline Output

현재 조사 환경은 외부 DNS/PyPI 접근이 없어 zizmor binary를 실행하지 못했다. 구현 환경의 first baseline이 예상 밖 finding을 반환하면 그 finding이 이 plan을 바꿀 수 있는 가장 가까운 새 evidence다. Green 상태를 만들기 위해 broad ignore로 우회하지 않는다.

### PR #253 Integration Order

PR #253이 먼저 `main`에 병합되면 classifier와 contract-test 위치가 달라진다. 이 경우 stale path를 그대로 적용하는 것이 가장 큰 구현 위험이다. 구현 시작 시 live `main`을 재확인하고 current owner를 사용한다. PR #253의 기능을 PR #254에 선제적으로 복제하거나 merge하지 않는다.

### Upstream Version Drift

`1.30.1`은 이 PR의 조사·도입 baseline이다. 구현 도중 새 zizmor release가 나와도 자동으로 scope를 바꾸지 않는다. 새 버전을 채택하려면 release note와 audit behavior 변화가 이 계획에 영향을 주는지 확인한 뒤 의도적으로 결정한다.

## Handoff

PR #254에서 위 순서대로 구현한다. 먼저 current base와 CI owner를 재확인하고 actual zizmor baseline을 얻는다. 예상 baseline을 해결한 뒤 selector와 workflow wiring을 추가하고 deterministic tests로 coverage를 고정한다. 가장 중요한 경계는 **action/workflow security finding을 merge 전에 막되, 이를 위해 repository의 기존 dependency/tooling 구조나 permission surface를 불필요하게 넓히지 않는 것**이다.
