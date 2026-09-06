---
title: "Continuous Integration"
description: "integration boundary에서 CI가 제공하는 admission evidence의 목적, 원칙, 재사용 패턴과 준수 계약을 정의합니다."
categories:
  - software-engineering
tags:
  - ci
  - github-actions
  - testing
---

# Continuous Integration

CI는 제안된 repository state를 integration boundary에 받아들여도 되는지 판단할 수 있는 **신뢰 가능한 자동화 근거**를 제공한다.

이 문서는 CI의 안정적인 목적과 판단 기준, 반복해서 사용하는 설계 패턴과 지켜야 하는 경계를 소유한다. Exact command, job, path classification 같은 구현 detail은 [`.github/workflows/`](../../.github/workflows/)가 소유한다. Goal과 Principles는 쉽게 바꾸지 않는 방향과 판단 기준이며, Patterns와 Contracts는 환경과 경험에 따라 바꿀 수 있지만 상위 목적과 원칙에 계속 부합해야 한다.

## Goal

CI의 목적은 변경을 integration boundary에 받아들일 수 있는지 판단하는 데 필요한 evidence를 자동으로 제공하는 것이다.

필요한 위험은 merge 전에 발견하되, admission 판단을 바꾸지 않는 검증이나 maintenance 때문에 사람과 agent가 반복 작업, 수동 수정, 불필요한 대기와 재실행 비용을 지불하지 않는 상태를 지향한다. CI는 검사를 많이 수행하는 것이 아니라 **필요한 신뢰를 가장 낮은 운영 비용으로 제공하는 것**을 목표로 한다.

## Principles

1. **Operational convenience over technical elegance:** 기술적 우아함과 운영 편의성을 함께 최대화한다. 둘이 충돌하면 correctness, safety와 admission contract를 보존하는 범위에서 운영 편의성을 우선한다. 기술적 순수성이나 구조적 미학만을 위해 반복 작업, 수동 개입, context switching, 재실행 또는 복구 비용을 늘리지 않는다.
1. **Admission evidence over ceremony:** CI job이나 test가 실행됐다는 사실 자체를 목표로 삼지 않는다. 어떤 변경을 받아들여도 되는지 판단하는 데 필요한 evidence가 있는지를 본다.
1. **Consequence determines strictness:** 어떤 실패를 알게 됐을 때 현재 변경을 받아들이지 않을 것이라면 그 실패는 merge-critical이다. 반대로 발견해도 admission 결정이 바뀌지 않는 정보는 자동화할 수 있다는 이유만으로 merge를 막지 않는다.
1. **Cheapest sufficient evidence:** 필요한 주장을 증명할 수 있는 가장 낮은 비용과 범위의 신뢰 가능한 evidence를 사용한다. 비용을 줄일 때는 admission standard가 아니라 실행 범위와 방식만 최적화한다.
1. **Verification follows risk and impact:** 검증 범위는 file type이나 workflow 관습이 아니라 실제 위험과 영향 범위를 따른다. Low-risk 또는 non-semantic 변경은 unrelated expensive check 비용을 지불하지 않고, 영향 범위를 충분히 알 수 없으면 검증을 넓히거나 안전하게 실패시킨다.
1. **Claims must match evidence:** 검증 결과가 실제로 증명하는 것보다 강한 주장을 하지 않는다. Static 또는 deterministic evidence가 runtime behavior를 대신하지 않으며, matching runtime evidence가 필요한 주장은 해당 revision의 runtime evidence로 확인한다.
1. **Authority remains explicit:** CI는 repository의 owning source와 contract를 검증하며 새로운 authority를 조용히 만들지 않는다. Automation이 source를 수정하거나 derived state를 갱신한다면 mutation의 owner, trigger와 review boundary가 명확해야 한다.

## Patterns

### Evidence Selection

Evidence는 필요한 주장에 맞는 가장 낮은 tier부터 선택한다.

| Tier | 확인하는 것 | 대표 evidence |
| --- | --- | --- |
| Static | 표현과 구조가 계약을 만족하는가 | syntax, schema, frontmatter, parseability |
| Deterministic | 재현 가능한 동작과 invariant가 유지되는가 | script, generator, contract/regression test |
| Harness / Projection | harness나 변환 경계가 의도대로 유지되는가 | generated projection, adapter fidelity, round-trip check |
| Semantic | 결정론적 assertion만으로 닫기 어려운 의미적 동작이 유지되는가 | routing, instruction following, adversarial case |
| Live runtime | 실제 provider·tool·runtime에서 동작하는가 | provider invocation, runtime parity, latency/cost |

낮은 tier는 높은 tier의 주장을 대신하지 않는다. 반대로 static 또는 deterministic evidence로 충분하면 semantic/model/runtime 검증을 추가하지 않는다. Stochastic 결과를 admission에 사용하려면 baseline, threshold, sample 또는 retry 해석 기준을 먼저 정의한다.

### Change Impact Selection

CI는 변경된 path와 의미를 기준으로 필요한 검증만 선택한다.

- source, test, configuration 또는 contract 변경은 해당 영향 범위를 검증한다.
- shared surface처럼 영향 범위가 넓은 변경은 검증 범위도 넓힌다.
- affected scope를 안정적으로 좁힐 수 있으면 exhaustive scope보다 우선한다.
- impact routing은 비용을 줄이는 최적화 수단이지 validation requirement를 약화시키는 근거가 아니다.
- merge-critical verification이 silent skip되지 않도록 routing을 fail-safe하게 설계한다.
- routing logic이 복잡해지면 routing 자체도 deterministic validation 대상으로 취급한다.
- exact glob과 routing table은 workflow implementation에 두고 이 문서에 복제하지 않는다.

### Validation Surfaces

각 validation surface는 서로를 그대로 복제하지 않고 가장 낮은 마찰로 자기 책임을 수행한다.

| Surface | 역할 | 대표 작업 |
| --- | --- | --- |
| Lefthook pre-commit | 빠른 local hygiene | staged formatting, safe deterministic autofix |
| Lefthook pre-push | relevant local correctness | affected lint, format check, test |
| PR CI | merge admission evidence | merge-critical correctness, contract, required validation |
| Main / post-merge | admission과 별개의 broader confidence | broader regression, diagnostics |
| Scheduled / manual | 고비용 또는 특수 evidence | stress, exhaustive eval, external integration |
| Maintenance | derived state의 write-back | formatting, regeneration, synchronization, indexing |

Local hook은 빠른 feedback과 자동 수정을 위한 convenience boundary이며 merge admission evidence 자체가 아니다. Hook은 우회되거나 실행 환경이 달라질 수 있으므로 merge-critical contract는 CI가 독립적으로 검증한다. Lefthook의 운영 baseline은 [Lefthook](tooling/lefthook.md), test 설계와 실행 기준은 [Testing Guide](testing.md)와 [Test Design](test-design.md)가 소유한다.

### Autofix And Maintenance

빠르고 결정론적이며 안전하게 고칠 수 있는 반복 작업은 사람이 수동으로 반복하지 않도록 자동화하는 것을 우선한다.

- Developer-owned change를 commit 전에 고칠 수 있으면 pre-commit처럼 낮은 마찰의 local surface를 우선한다.
- PR CI는 disposable workspace에서 formatter나 generator를 실행해 drift를 검출할 수 있다.
- Write-back이 안전하고 결정론적이며 review 가능한 상태를 유지하면서 end-to-end 운영 비용을 실제로 줄인다면 자동 mutation을 사용할 수 있다.
- Write-back을 admission gate와 결합하면 권한, trust boundary, commit loop, race 또는 review ambiguity가 더 커지는 경우에는 maintenance workflow나 더 이른 local autofix로 분리한다.
- Pure style이나 formatting만으로 manual fix round-trip을 만드는 것은 기본값이 아니다. Representation이 parseability, correctness, compatibility 또는 명시적 repository contract에 영향을 줄 때만 blocking evidence로 다룬다.

### CI Change Review

CI 변경은 다음 순서로 판단한다.

1. 이 실패를 알게 되면 현재 변경을 integration boundary에 받아들이지 않을 것인가?
1. 그렇다면 그 판단을 증명하는 가장 싼 충분한 evidence는 무엇인가?
1. 어떤 변경에만 이 evidence가 필요한가?
1. 더 이른 surface에서 안전하게 자동 수정하거나 검증해 운영 마찰을 줄일 수 있는가?
1. 영향 범위를 모를 때 안전하게 넓어지는가?
1. 어느 validation surface가 이 evidence를 소유해야 하는가?
1. 기존 validation과 불필요하게 중복되거나 새로운 maintenance burden을 만들지 않는가?

새 검사는 merge 판단을 실제로 개선하고 장기 운영 비용보다 가치가 클 때만 추가한다. Existing provider, repository-native checker와 test를 우선하고 새로운 CI machinery는 현재 evidence로 필요성이 입증될 때만 도입한다.

## Contracts

### Admission Boundary

- 이 repository의 integration boundary는 `main`이다.
- CI가 소유하는 merge-critical failure는 merge 전에 blocking evidence로 탐지할 수 있어야 한다. 검사가 비싸다는 이유만으로 post-merge로 미루지 않는다.
- PR admission evidence는 isolated PR head보다 `main`에 들어갈 prospective merge state를 기준으로 한다.
- Required PR workflow는 `main` 대상 Pull Request마다 생성되어야 한다. Change-impact 최적화는 workflow 자체를 없애기보다 내부 validation selection에 적용한다.
- 영향 범위를 충분히 결정할 수 없으면 검증을 넓히거나 selector를 실패시킨다. 불완전한 검증 집합을 정상 결과로 취급하지 않는다.
- Human review, release control 또는 runtime monitoring이 별도 위험을 소유할 수 있지만, 그 존재를 이유로 CI가 소유하는 merge-critical evidence를 생략하지 않는다.

### Inbox Boundary

[`inbox/AGENTS.md`](../../inbox/AGENTS.md)에서 non-canonical working artifact로 정의된 일반 Inbox artifact는 원칙적으로 merge admission evidence의 대상이 아니다. 조사, review, checkpoint, handoff, 임시 evidence의 formatting이나 문서 hygiene만을 이유로 unrelated CI를 실행하거나 merge를 막지 않는다.

다만 Inbox workflow와 contract를 정의하는 repository infrastructure는 일반 repository 변경과 동일하게 검증한다. `inbox/AGENTS.md`, `inbox/_guidelines/**`, `inbox/_templates/**`처럼 반복해서 다른 작업의 동작을 지배하는 surface가 여기에 해당한다. Inbox의 content, structure와 lifecycle 자체는 계속 `inbox/AGENTS.md`가 소유한다.

### Safety And Authority

- Blocking CI는 필요한 동작을 수행할 수 있는 최소 권한을 사용한다. Read-only access가 충분하면 write 권한을 부여하지 않는다.
- Secret이 필요한 검증은 untrusted Pull Request와의 trust boundary를 명확히 한다. Admission에 필요하지 않은 secret-bearing 실행은 PR에 두지 않는다.
- Third-party action, downloaded tool, external API와 write-capable automation은 trust boundary로 취급한다.
- Generated file, index, projection, formatting result와 maintenance commit은 repository가 달리 정하지 않는 한 derived state다.
- Automation output은 canonical owner를 대체하지 않는다. Write-back은 source authority와 reviewability를 보존해야 한다.

### Ownership

- 이 문서는 CI의 Goal, Principles, reusable Patterns와 Contracts를 소유한다.
- [`.github/workflows/`](../../.github/workflows/)는 exact trigger, job, command, selector와 path mapping을 소유한다.
- [Testing Guide](testing.md)는 사람이 local terminal에서 test를 선택하고 실행하는 방법과 현재 CI test behavior의 사용자-facing 설명을 소유한다.
- [Lefthook](tooling/lefthook.md)은 pre-commit과 pre-push의 local validation baseline을 소유한다.

구현이나 운영 경험 때문에 Pattern 또는 Contract를 바꿀 수는 있지만 Goal과 Principles에 정합해야 한다. 정합되지 않는다면 하위 구현을 억지로 유지하기보다 상위 guidance의 변경이 실제로 필요한지 먼저 검토한다.
