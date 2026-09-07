---
title: "Continuous Integration"
description: "CI의 목적, 판단 원칙, 운영 패턴과 필수 경계를 정의합니다."
categories:
  - software-engineering
tags:
  - ci
  - github-actions
  - testing
---

# Continuous Integration

CI는 변경을 `main`에 받아들여도 되는지 판단할 **신뢰할 수 있는 자동 검증 근거**를 제공한다.

목표는 검사를 많이 돌리는 것이 아니다. **필요한 신뢰를 가장 낮은 운영 비용으로 확보하는 것**이다.

이 문서는 CI의 목적과 원칙, 반복해서 쓰는 패턴, 반드시 지켜야 할 경계를 정의한다. 정확한 trigger, job, command와 path 분류는 [`.github/workflows/`](../../.github/workflows/)가 소유한다.

## Goal

CI는 다음 상태를 지향한다.

- `main`에 들어가면 안 되는 문제는 병합 전에 발견한다.
- 병합 판단에 필요하지 않은 검사와 유지보수로 작업을 지연시키지 않는다.
- 사람과 agent가 불필요한 수동 수정, 재실행과 반복 작업을 하지 않게 한다.

## Principles

1. **운영 편의를 우선한다.** 기술적 우아함과 운영 편의를 함께 추구하되, 둘이 충돌하면 정확성과 안전성을 지키는 범위에서 운영 편의를 우선한다.
1. **기여 환경의 차이를 고려한다.** 사람과 agent는 사용할 수 있는 local runtime, shell, Git hook과 repository API가 다를 수 있다. 사용할 수 있는 기능은 적극 활용하되, 필수 기여 경로가 특정 local capability에만 의존하지 않게 한다.
1. **병합 판단에 필요한 것만 막는다.** 어떤 실패를 알게 됐을 때 변경을 받아들이지 않을 것이라면 병합 전에 막는다. 그렇지 않다면 자동화할 수 있다는 이유만으로 병합을 막지 않는다.
1. **가장 싼 충분한 검증을 사용한다.** 같은 신뢰를 얻을 수 있다면 더 좁고, 빠르고, 결정론적인 검증을 우선한다. 비용을 줄여도 병합 기준은 낮추지 않는다.
1. **위험과 영향 범위에 맞춰 검증한다.** 모든 변경에 모든 검사를 돌리지 않는다. 영향이 넓으면 검증도 넓히고, 영향 범위를 확신할 수 없으면 안전하게 넓히거나 실패시킨다.
1. **검증보다 강한 주장을 하지 않는다.** 정적 검사나 단위 테스트만으로 실제 실행 환경까지 검증했다고 보지 않는다. 필요한 주장에 맞는 근거를 사용한다.
1. **검증과 변경 권한을 구분한다.** CI는 저장소의 소스와 계약을 검증한다. 자동화가 소스를 수정한다면 수정 주체, 실행 조건과 검토 경계가 명확해야 한다.

## Patterns

### Evidence Levels

필요한 주장을 증명할 수 있는 가장 낮은 수준부터 선택한다.

| Level | Purpose | Examples |
| --- | --- | --- |
| Static | 표현과 구조가 유효한지 확인 | 문법, schema, frontmatter, parseability |
| Deterministic | 재현 가능한 규칙이 유지되는지 확인 | script, generator, contract/regression test |
| Transformation | 생성·변환 경계가 의도대로 유지되는지 확인 | projection, adapter, round-trip check |
| Semantic | 결정론적 assertion만으로 확인하기 어려운 동작 검증 | routing, instruction following, adversarial case |
| Live runtime | 실제 provider·tool 환경의 동작 확인 | live invocation, integration, latency/cost |

낮은 수준으로 충분하면 더 비싼 검증을 추가하지 않는다. 확률적인 결과를 병합 판단에 쓰려면 threshold, baseline, sample 또는 retry 기준을 먼저 정한다.

### Change Impact

- 변경된 소스, 테스트, 설정과 계약의 영향 범위를 우선 검증한다.
- 공용 영역처럼 영향이 넓은 변경은 검증 범위도 넓힌다.
- 영향 범위를 안전하게 좁힐 수 있으면 전체 검증보다 우선한다.
- 영향 범위를 확신할 수 없으면 검증을 넓히거나 selector를 실패시킨다.
- 중요한 검증이 path 분류 때문에 조용히 빠지지 않게 한다.
- 정확한 glob과 routing table은 workflow에 둔다.

### Validation Surfaces

각 단계는 같은 검사를 반복하지 않고 자기 역할에 집중한다.

| Surface | Role |
| --- | --- |
| pre-commit | 빠른 formatting과 안전한 자동 수정 |
| pre-push | push 전에 관련 lint, format check와 test 확인 |
| PR CI | 병합 여부를 판단하는 필수 검증 |
| main / post-merge | 더 넓은 회귀 검사와 진단 |
| scheduled / manual | 비싸거나 특수한 검증 |
| maintenance | formatting, regeneration, synchronization 같은 자동 반영 |

Local hook은 빠른 피드백과 자동 수정을 위한 장치다. 우회되거나 환경이 다를 수 있으므로 병합에 꼭 필요한 검증은 CI가 다시 확인한다.

Lefthook의 세부 동작은 [Lefthook](tooling/lefthook.md), test 실행 기준은 [Testing Guide](testing.md)와 [Test Design](test-design.md)를 따른다.

### Contributor Environments

기여 환경에 따라 사용할 수 있는 실행 기능이 다를 수 있다.

- Local runtime과 shell을 사용할 수 있으면 focused test, formatter와 hook을 적극 활용해 빠르게 수정하고 검증한다.
- Local runtime을 사용할 수 없더라도 필수 병합 판단과 복구 경로가 막히지 않아야 한다. CI와 repository-side automation은 필요한 검증 근거와 실행 가능한 실패 정보를 제공해야 한다.
- 일부 환경에 기능이 없다는 이유로 다른 환경의 빠른 local feedback을 없애지 않는다. 공통 기준은 결과와 계약이며 실행 경로는 환경에 맞게 달라질 수 있다.

### Autofix and Maintenance

반복적이고 안전하게 고칠 수 있는 문제는 사람이 직접 고치게 하지 않는 것을 우선한다.

- commit 전에 안전하게 고칠 수 있으면 pre-commit 같은 이른 단계에서 자동 수정한다.
- PR CI는 formatter나 generator를 실행해 차이를 확인할 수 있다.
- 자동 수정 경로는 local runtime이 항상 있다고 가정하지 않는다. Runtime을 사용할 수 있으면 이른 단계의 자동 수정을 우선하고, 그렇지 않은 환경에서는 repository-side 자동화나 구체적인 수정 근거를 제공하는 방법을 검토한다.
- 자동 반영이 검토 가능성을 유지하면서 전체 운영 비용을 줄인다면 사용할 수 있다.
- 쓰기 권한, commit loop, race, 검토 혼란이 더 커지면 local autofix나 별도 maintenance로 분리한다.
- 단순 formatting 때문에 불필요한 수동 수정과 재실행을 만드는 것은 기본값이 아니다. 표현 형식이 실제 correctness, compatibility 또는 명시적 계약에 영향을 줄 때만 병합을 막는다.

### CI Change Checklist

CI를 추가하거나 바꿀 때는 다음 순서로 판단한다.

1. 이 실패를 알게 되면 병합을 막을 것인가?
1. 그 판단에 필요한 가장 싼 충분한 검증은 무엇인가?
1. 어떤 변경에만 이 검증이 필요한가?
1. 기여 환경마다 실행 가능한 수정·검증 경로가 있는가?
1. 더 이른 단계에서 안전하게 자동 수정해 반복 작업을 줄일 수 있는가?
1. 영향 범위를 모를 때 안전하게 넓어지는가?
1. 기존 검증과 중복되거나 새로운 운영 부담을 만들지 않는가?

## Contracts

### Admission Boundary

- 이 저장소의 통합 경계는 `main`이다.
- `main`에 들어가면 안 되는 문제는 병합 전에 차단할 수 있어야 한다.
- 검사가 비싸다는 이유만으로 필요한 검증을 post-merge로 미루지 않는다.
- PR은 단독 head보다 `main`과 합쳐질 상태를 기준으로 검증한다.
- `main` 대상 PR에는 required workflow가 항상 생성되어야 한다. 불필요한 검증은 workflow 내부에서 선택적으로 생략한다.
- 영향 범위를 결정할 수 없으면 검증을 넓히거나 실패시킨다. 불완전한 검증을 정상 결과로 처리하지 않는다.

### Inbox Boundary

Inbox 전체를 매 PR마다 다시 검사하지 않는다. **현재 prospective change set에 포함된 Inbox artifact만** 현재 변경으로 취급한다.

- 현재 변경된 일반 Inbox Markdown에는 formatting/lint와 common artifact root의 required frontmatter·이름 정합성처럼 가볍고 결정론적인 검증만 적용한다.
- Standalone artifact와 변경된 bundle에서 도달 가능한 `README.md` root는 `type`, `title`, `description`과 artifact name의 `type` 정합성을 확인한다.
- 현재 변경에 포함되지 않은 과거·완료·보관 artifact는 scan, reformat, migration 또는 재검증하지 않는다.
- 일반 Inbox artifact 변경만으로 unrelated source test나 platform-specific runtime 검증을 실행하지 않는다.
- `inbox/AGENTS.md`, `inbox/_guidelines/**`, `inbox/_templates/**`처럼 다른 작업의 동작을 정하는 기반 문서는 일반 저장소 변경과 동일하게 검증한다.

Inbox 자체의 내용과 lifecycle은 [`inbox/AGENTS.md`](../../inbox/AGENTS.md)가 소유한다.

### Safety and Authority

- CI는 필요한 최소 권한만 사용한다. 읽기 권한으로 충분하면 쓰기 권한을 주지 않는다.
- secret이 필요한 검증은 신뢰할 수 없는 PR과 분리한다.
- third-party action, 외부 도구, 외부 API와 쓰기 권한이 있는 자동화는 trust boundary로 취급한다.
- generated file, index, formatting 결과와 maintenance commit은 저장소가 달리 정하지 않는 한 파생 상태다.
- 자동화 결과가 canonical source를 대신하지 않는다.

### Ownership

- 이 문서는 CI의 목적, 원칙, 패턴과 계약을 소유한다.
- [`.github/workflows/`](../../.github/workflows/)는 정확한 trigger, job, command, selector와 path mapping을 소유한다.
- [Testing Guide](testing.md)는 test 실행 방법과 현재 CI test 동작의 사용자-facing 설명을 소유한다.
- [Lefthook](tooling/lefthook.md)은 pre-commit과 pre-push의 기준을 소유한다.

구현이나 운영 경험에 따라 패턴과 계약은 바꿀 수 있다. 다만 변경은 항상 이 문서의 목적과 원칙에 맞아야 한다.
