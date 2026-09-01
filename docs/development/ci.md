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

CI는 repository hygiene를 전부 반복하는 곳이 아니라, 변경을 `main`에 받아들여도 되는지 판단하기 위한 **merge admission evidence**를 제공한다.

현재 workflow의 exact command, job, path classification과 implementation detail은 [`.github/workflows/`](../../.github/workflows/)가 소유한다. 이 문서는 CI 구현이 지켜야 하는 안정적인 정책과 책임 경계만 소유한다.

## Admission Boundary

`main`에 들어가면 안 되는 실패는 merge 전에 자동으로 탐지할 수 있어야 한다. 검증은 변경 위험과 영향 범위에 비례하며, 가능한 한 가장 싼 충분한 evidence를 사용한다.

- correctness, repository contract, required validation처럼 merge 여부를 바꾸는 실패를 우선한다.
- CI 최적화는 검증의 실행 범위와 비용을 줄이는 것이며 admission standard 자체를 낮추는 것이 아니다. `main`에서 허용할 수 없는 실패라면 검사가 비싸다는 이유만으로 post-merge로 이동하지 않는다.
- formatting이나 local hygiene 자체를 CI의 목적처럼 취급하지 않는다. 다만 representation이 parseability, correctness 또는 명시적 contract에 영향을 주면 merge evidence가 될 수 있다.
- low-risk 또는 non-semantic 변경은 unrelated expensive check 비용을 지불하지 않는다.
- 영향 범위를 확신할 수 없으면 관련 검증을 생략하지 않고 더 넓게 실행한다.

## Evidence Selection

필요한 주장을 증명할 수 있는 가장 낮은 비용의 evidence를 우선한다. 더 높은 단계의 evidence는 낮은 단계로 증명할 수 없는 중요한 위험이 있을 때만 사용한다.

| Tier | Proves | Examples |
| --- | --- | --- |
| Static | 표현과 구조가 계약을 만족하는지 | syntax, schema, frontmatter, parseability |
| Deterministic | 재현 가능한 동작과 invariant가 유지되는지 | script, generator, contract/regression test |
| Projection / integration | 변환·연결 경계가 의도대로 유지되는지 | generated projection, adapter, integration boundary |
| Semantic | 결정론적 assertion만으로 닫기 어려운 의미적 동작이 유지되는지 | routing, instruction following, adversarial case |
| Live runtime | 실제 provider·tool·runtime에서 동작하는지 | provider invocation, runtime parity, latency/cost |

낮은 tier의 evidence가 높은 tier의 주장을 대신하지 않는다. 반대로 static 또는 deterministic evidence로 충분한데 semantic/model/runtime 검증을 추가하지 않는다. Runtime behavior에 대한 주장은 matching revision의 runtime evidence가 있을 때만 인정한다.

## Validation Layers

| Layer | Responsibility | Typical work |
| --- | --- | --- |
| Editor / formatter | 작성 편의 | format-on-save, 즉시 정리 |
| Lefthook pre-commit | 빠른 local hygiene | staged formatting, safe autofix |
| Lefthook pre-push | relevant local correctness | affected lint, format check, test |
| CI pull request | merge admission evidence | merge-critical correctness, contract, required validation |
| CI main / post-merge | admission과 별개의 broader confidence | broader regression, diagnostics |
| Scheduled / manual | 고비용 또는 특수 evidence | stress, exhaustive eval, external integration |
| Maintenance | derived state의 write-back | formatting, regeneration, synchronization, indexing |

Local validation과 CI는 서로를 그대로 복제하지 않는다. Lefthook의 운영 baseline은 [Lefthook](tooling/lefthook.md), test 설계와 실행 기준은 [Testing Guide](testing.md)와 [Test Design](test-design.md)가 소유한다.

Post-merge나 scheduled 검증이 유용하더라도 merge-critical failure를 그쪽으로 밀어내는 근거가 되지 않는다. Maintenance automation은 자동화되어 있다는 이유만으로 merge gate가 되지 않는다.

## Change Impact

CI는 변경된 path와 의미를 기준으로 필요한 검증만 선택한다.

- source, test, configuration 또는 contract 변경은 그 영향 범위를 검증한다.
- shared surface나 영향 범위가 넓은 변경은 더 넓은 validation을 실행할 수 있다.
- path classification은 최적화 수단이지 validation requirement를 약화시키는 근거가 아니다.
- classification이 알려진 merge-critical 검증을 silent skip하지 않도록 fail-safe하게 설계한다.
- 영향 범위를 충분히 결정할 수 없으면 validation을 넓히거나 selector를 실패시키며, 비어 있거나 불완전한 검증 집합을 정상 결과로 취급하지 않는다.
- merge-critical verification을 선택하는 routing logic이 복잡해지면 routing 자체도 deterministic validation 대상으로 취급한다.
- exact glob과 routing table은 workflow implementation에 두고 이 문서에 복제하지 않는다.

## Non-Canonical Working Artifacts

[`inbox/AGENTS.md`](../../inbox/AGENTS.md)에서 non-canonical working artifact로 정의된 일반 Inbox artifact는 원칙적으로 merge admission evidence의 대상이 아니다. 조사, review, checkpoint, handoff, 임시 evidence 같은 working artifact의 formatting이나 문서 hygiene만을 이유로 unrelated CI를 실행하지 않는다.

다만 Inbox의 workflow, contract 또는 reusable authoring surface 자체를 정의하는 repository infrastructure는 일반 repository 변경과 동일하게 검증한다. 예를 들어 `inbox/AGENTS.md`, `inbox/_guidelines/**`, `inbox/_templates/**`처럼 반복해서 다른 작업의 동작을 지배하는 surface는 단순 working artifact로 취급하지 않는다.

이 경계는 Inbox의 의미를 재정의하지 않는다. Inbox의 content, structure와 lifecycle은 `inbox/AGENTS.md`가 계속 소유한다.

## Safety And Authority

CI는 repository의 owning source와 contract를 검증하며 새로운 authority를 만들지 않는다. Generated output, index, projection, eval result와 maintenance output은 repository가 별도로 authority를 부여하지 않는 한 derived state로 취급한다.

- blocking CI는 practical한 최소 권한과 read-only repository access를 우선한다.
- secret이 필요한 검증은 untrusted Pull Request와의 trust boundary를 명확히 하고, admission에 필요하지 않은 secret-bearing 실행을 PR에 두지 않는다.
- third-party action, downloaded tool, external API와 generated commit은 trust boundary로 취급한다.
- expensive job은 필요한 경우 timeout, bounded sample/retry와 superseded run cancellation으로 비용과 실패 범위를 제한한다.
- maintenance나 write-back automation은 merge admission과 분리하고, canonical source를 덮어쓰거나 commit loop를 만들지 않도록 한다.

## Change Rule

CI를 변경할 때는 "무엇을 더 검사할까"보다 먼저 다음을 확인한다.

1. 이 실패가 `main`에 들어가면 실제로 unacceptable한가?
1. 그렇다면 가장 싼 충분한 evidence는 무엇인가?
1. 어떤 변경에만 이 evidence가 필요한가?
1. 영향 범위를 모르겠을 때 안전하게 넓어지는가?
1. 어느 validation layer와 실행 시점이 이 evidence를 소유해야 하는가?
1. Lefthook이나 다른 validation과 불필요하게 중복되지 않는가?

새 검사는 merge 판단을 실제로 개선하고 장기 유지 비용보다 가치가 클 때만 추가한다. Existing provider, repository-native checker와 test를 우선하고, cache, matrix, 별도 router나 새 framework는 현재 evidence로 필요성이 입증될 때만 도입한다.
