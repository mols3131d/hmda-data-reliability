---
title: "Continuous Integration"
description: "main 입장 경계에서 CI가 제공해야 하는 검증 증거, change-impact 선택과 local validation의 책임 경계를 정의합니다."
categories:
  - software-engineering
tags:
  - ci
  - github-actions
  - testing
---

# Continuous Integration

CI는 repository hygiene를 모두 반복하는 곳이 아니라, 변경을 `main`에 받아들여도 되는지 판단하기 위한 **merge admission evidence**를 제공한다.

이 문서는 CI가 지켜야 하는 안정적인 정책과 책임 경계를 소유한다. Exact command, job, path classification 같은 구현 detail은 [`.github/workflows/`](../../.github/workflows/)가 소유한다.

## Core Rules

- **Strict admission:** CI가 소유하는 merge-critical failure는 merge 전에 blocking evidence로 탐지할 수 있어야 한다. 검사가 비싸다는 이유만으로 post-merge로 미루지 않는다.
- **Cheapest sufficient evidence:** 필요한 주장을 증명할 수 있는 가장 싼 충분한 evidence를 사용한다. 더 비싼 검증은 낮은 비용의 evidence로 중요한 위험을 닫을 수 없을 때만 추가한다.
- **Risk-proportional verification:** low-risk 또는 non-semantic 변경은 unrelated expensive check 비용을 지불하지 않는다.
- **Fail-safe routing:** 영향 범위를 충분히 결정할 수 없으면 검증을 넓히거나 selector를 실패시킨다. 불완전한 검증 집합을 정상 결과로 취급하지 않는다.

CI가 모든 correctness risk를 혼자 소유하지는 않는다. Human review, release control, runtime monitoring이 소유하는 위험은 해당 경계에 남긴다. 다만 다른 단계가 있다는 이유로 CI가 소유하는 merge-critical evidence를 생략하지 않는다.

## Evidence Levels

Evidence는 필요한 주장에 맞는 가장 낮은 tier부터 선택한다.

| Tier | 확인하는 것 | 대표 evidence |
| --- | --- | --- |
| Static | 표현과 구조가 계약을 만족하는가 | syntax, schema, frontmatter, parseability |
| Deterministic | 재현 가능한 동작과 invariant가 유지되는가 | script, generator, contract/regression test |
| Projection / Integration | 변환·연결 경계가 의도대로 유지되는가 | generated projection, adapter, integration boundary |
| Semantic | 결정론적 assertion만으로 닫기 어려운 의미적 동작이 유지되는가 | routing, instruction following, adversarial case |
| Live runtime | 실제 provider·tool·runtime에서 동작하는가 | provider invocation, runtime parity, latency/cost |

낮은 tier는 높은 tier의 주장을 대신하지 않는다. 반대로 static 또는 deterministic evidence로 충분하면 semantic/model/runtime 검증을 추가하지 않는다. Runtime behavior에 대한 주장은 matching revision의 runtime evidence가 있을 때만 인정한다.

Stochastic 결과는 한 번의 성공이나 실패를 deterministic evidence처럼 해석하지 않는다. Merge admission에 사용하려면 필요한 baseline, threshold, sample 또는 retry 해석 기준을 먼저 정의한다.

## Responsibility Boundaries

| Surface | 역할 | 대표 작업 |
| --- | --- | --- |
| Lefthook pre-commit | 빠른 local hygiene | staged formatting, safe autofix |
| Lefthook pre-push | relevant local correctness | affected lint, format check, test |
| PR CI | merge admission evidence | merge-critical correctness, contract, required validation |
| Main / post-merge | admission과 별개의 broader confidence | broader regression, diagnostics |
| Scheduled / manual | 고비용 또는 특수 evidence | stress, exhaustive eval, external integration |
| Maintenance | derived state의 write-back | formatting, regeneration, synchronization, indexing |

Local validation과 CI는 서로를 그대로 복제하지 않는다. Lefthook의 운영 baseline은 [Lefthook](tooling/lefthook.md), test 설계와 실행 기준은 [Testing Guide](testing.md)와 [Test Design](test-design.md)가 소유한다.

Formatting이나 local hygiene 자체는 기본적으로 merge evidence가 아니다. 다만 representation이 parseability, correctness 또는 명시적 contract에 영향을 주면 blocking evidence가 될 수 있다. Maintenance automation도 자동화되어 있다는 이유만으로 merge gate가 되지 않는다.

## Change Impact

CI는 변경된 path와 의미를 기준으로 필요한 검증만 선택한다.

- source, test, configuration 또는 contract 변경은 해당 영향 범위를 검증한다.
- shared surface처럼 영향 범위가 넓은 변경은 검증 범위도 넓힌다.
- path classification은 비용을 줄이는 최적화 수단이지 validation requirement를 약화시키는 근거가 아니다.
- merge-critical verification이 silent skip되지 않도록 routing을 fail-safe하게 설계한다.
- routing logic이 복잡해지면 routing 자체도 deterministic validation 대상으로 취급한다.
- exact glob과 routing table은 workflow implementation에 두고 이 문서에 복제하지 않는다.

## Inbox Boundary

[`inbox/AGENTS.md`](../../inbox/AGENTS.md)에서 non-canonical working artifact로 정의된 일반 Inbox artifact는 원칙적으로 merge admission evidence의 대상이 아니다. 조사, review, checkpoint, handoff, 임시 evidence의 formatting이나 문서 hygiene만을 이유로 unrelated CI를 실행하지 않는다.

다만 Inbox workflow와 contract를 정의하는 repository infrastructure는 일반 repository 변경과 동일하게 검증한다. `inbox/AGENTS.md`, `inbox/_guidelines/**`, `inbox/_templates/**`처럼 반복해서 다른 작업의 동작을 지배하는 surface가 여기에 해당한다.

Inbox의 content, structure와 lifecycle 자체는 계속 `inbox/AGENTS.md`가 소유한다.

## Safety and Authority

CI는 repository의 owning source와 contract를 검증하며 새로운 authority를 만들지 않는다. CI 결과와 automation output은 repository가 정한 canonical owner를 대체하지 않는다.

- blocking CI는 가능한 범위에서 최소 권한과 read-only repository access를 우선한다.
- secret이 필요한 검증은 untrusted Pull Request와의 trust boundary를 명확히 한다.
- admission에 필요하지 않은 secret-bearing 실행은 PR에 두지 않는다.
- third-party action, downloaded tool, external API와 write-capable automation은 trust boundary로 취급한다.
- maintenance와 write-back automation은 merge admission과 분리하고 canonical source를 덮어쓰거나 commit loop를 만들지 않도록 한다.

## Change Checklist

CI를 변경하기 전에 다음 순서로 판단한다.

1. 이 실패가 `main`에 들어가면 실제로 unacceptable한가?
1. 그렇다면 가장 싼 충분한 evidence는 무엇인가?
1. 어떤 변경에만 이 evidence가 필요한가?
1. 영향 범위를 모를 때 안전하게 넓어지는가?
1. 어느 validation surface가 이 evidence를 소유해야 하는가?
1. Lefthook이나 다른 validation과 불필요하게 중복되지 않는가?

새 검사는 merge 판단을 실제로 개선하고 장기 유지 비용보다 가치가 클 때만 추가한다. Existing provider, repository-native checker와 test를 우선하고 새로운 CI machinery는 현재 evidence로 필요성이 입증될 때만 도입한다.
