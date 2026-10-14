---
title: "Continuous Integration"
description: "CI를 추가·변경하거나 병합 검증을 판단할 때 목적, 원칙, 운영 패턴, 권한·신뢰 경계와 검증별 계약을 확인하는 진입점입니다."
categories:
  - software-engineering
tags:
  - ci
  - github-actions
  - testing
---

# Continuous Integration

CI는 `main`에 변경을 받아들일지 판단하는 **신뢰할 수 있는 자동 검증 근거**를 제공한다. 목표는 **필요한 신뢰를 가장 낮은 운영 비용으로 확보하는 것**이다.

CI를 추가하거나 바꾸고, 병합 검증을 판단할 때 여기서 시작한다. 공통 지침은 이 README를, 검증별 조건과 필수 결과는 아래 계약을 따른다. 현재 실행 동작과 로컬 명령은 [Testing Guide](../testing.md#pull-request-ci)에서 확인한다.

## Read Next

| Question | Contract |
| --- | --- |
| 병합 전 필수 검증과 대상 상태는? | [Admission Boundary](admission.md) |
| 검증 선택과 불확실한 영향 범위의 처리는? | [Change Impact](change-impact.md) |
| Markdown의 포맷 수정과 차단 lint 범위는? | [Markdown Validation](markdown-validation.md) |
| Inbox CI 제외 범위는? | [Inbox Exclusion](markdown-validation.md#inbox-exclusion) |

## Goal

- `main`에 부적합한 문제는 병합 전에 발견한다.
- 불필요한 검사와 유지보수로 작업을 지연시키지 않는다.
- 사람과 agent의 불필요한 수동 수정, 재실행과 반복 작업을 줄인다.

## Principles

1. **운영 편의:** 기술적 우아함과 운영 편의를 함께 추구한다. 둘이 충돌하면 정확성과 안전성을 지키는 범위에서 운영 편의를 우선한다.
1. **기여 환경:** 로컬 runtime, shell, Git hook과 repository API는 환경마다 다를 수 있다. 가능한 기능은 활용하되 필수 기여 경로를 특정 로컬 기능에만 의존시키지 않는다.
1. **차단 기준:** 변경을 거절할 근거가 되는 실패만 병합 전에 차단한다. 자동화 가능성만으로 차단 조건을 늘리지 않는다.
1. **검증 비용:** 같은 신뢰를 얻는다면 더 좁고 빠른 결정론적 검증을 우선한다. 비용 때문에 병합 기준을 낮추지 않는다.
1. **검증 범위:** 모든 변경에 모든 검사를 돌리지 않는다. 위험과 영향에 맞게 선택한다. 영향이 넓으면 검증도 넓히고, 불확실하면 안전하게 넓히거나 검증 선택을 실패시킨다.
1. **근거 수준:** 정적 검사나 단위 테스트로 실제 실행 환경까지 검증했다고 주장하지 않는다. 주장에 맞는 근거를 사용한다.
1. **변경 권한:** CI는 소스와 계약을 검증한다. 자동 수정의 주체, 실행 조건과 검토 경계는 별도로 명시한다.

## Patterns

### Evidence Levels

필요한 주장을 증명할 수 있는 가장 낮은 검증 수준부터 선택한다.

| Level | Purpose | Examples |
| --- | --- | --- |
| Static | 표현과 구조의 유효성 | 문법, schema, frontmatter, parseability |
| Deterministic | 재현 가능한 규칙 유지 | script, generator, contract/regression test |
| Transformation | 의도한 생성 및 변환 경계 유지 | projection, adapter, round-trip check |
| Semantic | 결정론적 assertion만으로 확인하기 어려운 동작 | routing, instruction following, adversarial case |
| Live runtime | 실제 provider와 tool 환경의 동작 | live invocation, integration, latency/cost |

낮은 수준으로 충분하면 더 비싼 검증을 추가하지 않는다. 확률적 결과를 병합 판단에 쓰려면 threshold, baseline, sample 또는 retry 기준을 먼저 정한다.

### Change Impact

위험과 영향에 맞는 가장 좁은 충분한 검증을 선택한다. **비용을 줄이는 것과 필수 검증을 생략하는 것은 다르다.**

검증 선택, 불확실성 처리와 CI 자체 변경 검증은 [Change Impact](change-impact.md)를 따른다. 정확한 경로별 선택과 현재 테스트 실행은 [Testing Guide](../testing.md#pull-request-ci)와 구현에서 확인한다.

### Validation Surfaces

불필요한 검사 중복을 줄이고 단계별 역할에 집중한다.

| Surface | Role |
| --- | --- |
| pre-commit | 빠른 포맷 수정과 안전한 자동 수정 |
| pre-push | push 전에 관련 lint, 포맷 검사와 테스트 확인 |
| PR CI | 병합 여부를 판단하는 필수 검증 |
| main / post-merge | 더 넓은 회귀 검사와 진단 |
| scheduled / manual | 비싸거나 특수한 검증 |
| maintenance | 포맷 수정, 재생성과 동기화의 자동 반영 |

로컬 hook은 빠른 피드백과 자동 수정용이다. 우회되거나 환경이 다를 수 있으므로 **병합 필수 검증은 CI가 다시 확인한다.**

Hook 동작은 [Lefthook](../tooling/lefthook.md), 테스트 실행 기준은 [Testing Guide](../testing.md)와 [Test Design](../test-design.md)를 따른다.

### Contributor Environments

| Environment | Workflow |
| --- | --- |
| 로컬 runtime과 shell 사용 가능 | 변경 범위에 맞는 테스트, formatter와 hook으로 빠르게 수정하고 검증한다. |
| 로컬 runtime 사용 불가 | 필수 병합 판단과 복구 경로를 보장한다. CI와 저장소 측 자동화가 검증 근거와 실행 가능한 실패 정보를 제공한다. |

**결과와 계약은 공통으로, 실행 경로는 환경에 맞게 유지한다.** 일부 환경에 기능이 없다는 이유로 다른 환경의 빠른 피드백을 없애지 않는다.

### Autofix and Maintenance

반복적인 문제의 안전한 수정은 수동 작업보다 자동화를 우선한다.

- Commit 전 안전한 수정은 pre-commit 등 이른 단계에서 자동 수행한다.
- PR CI는 formatter와 generator로 차이를 확인할 수 있다.
- 로컬 runtime이 있으면 이른 자동 수정을 우선한다. 없으면 저장소 측 자동화나 구체적인 수정 근거 제공을 검토한다.
- 자동 반영은 검토 가능성을 유지하며 전체 운영 비용을 줄일 때 사용할 수 있다.
- 쓰기 권한, commit loop, race와 검토 혼란의 부담이 커지면 로컬 자동 수정이나 별도 maintenance로 분리한다.
- 단순 포맷 수정 때문에 불필요한 수동 수정과 재실행을 기본값으로 삼지 않는다. 표현 형식이 정확성, 호환성 또는 명시적 계약에 영향을 줄 때만 병합을 막는다.

Markdown의 포맷 수정, lint와 branch 반영(write-back)은 [Markdown Validation](markdown-validation.md)을 따른다. 자동화 권한은 [Safety and Authority](#safety-and-authority)를 따른다.

### CI Change Checklist

CI를 추가하거나 바꿀 때 순서대로 판단한다.

1. 이 실패는 병합을 막을 근거인가?
1. 가장 싼 충분한 검증은 무엇인가?
1. 어떤 변경에 필요한가?
1. 기여 환경마다 실행 가능한 수정과 검증 경로가 있는가?
1. 이른 단계의 안전한 자동 수정으로 반복을 줄일 수 있는가?
1. 영향 범위를 모르면 안전하게 검증을 넓히는가?
1. 검사 중복이나 새 운영 부담은 없는가?

## Safety and Authority

CI와 자동화에 권한을 주거나 외부 도구와 API를 연결할 때 적용한다.

- CI는 최소 권한만 사용하며, 읽기로 충분하면 쓰기 권한을 주지 않는다.
- Secret이 필요한 검증은 신뢰할 수 없는 PR과 분리한다.
- Third-party action, 외부 도구와 API, 쓰기 권한이 있는 자동화는 신뢰 경계로 취급한다.
- 생성 파일, index, 포맷 수정 결과와 maintenance commit은 별도 규정이 없으면 파생 상태다.
- 자동화 결과는 canonical source를 대신하지 않는다.

> [!IMPORTANT]
> 이 정책은 일반적인 branch write-back 승인이 아니다. Markdown의 반영 범위는 [Markdown Validation](markdown-validation.md), 실제 권한과 step 조건은 [workflow](../../../.github/workflows/ci-lite.yml)에서 확인한다.

## Ownership

| Source | Responsibility |
| --- | --- |
| 이 README | 목적, 원칙, 패턴, 공통 권한과 신뢰 경계, 탐색 안내 |
| Read Next의 문서 | 검증별 계약 |
| [`.github/workflows/`](../../../.github/workflows/) | 정확한 trigger, job, setup과 step 조건 |
| [`scripts/ci/`](../../../scripts/ci/) | 변경 경로별 검증 선택, step 명령과 분기, 변경 파일 수집 |
| [Testing Guide](../testing.md) | 테스트 실행 방법과 현재 CI 테스트 동작의 사용자 안내 |
| [Lefthook](../tooling/lefthook.md) | pre-commit과 pre-push 기준 |

패턴과 계약은 구현 및 운영 경험에 맞춰 바꿀 수 있지만 이 번들의 목적과 원칙을 따른다. **실제 통과 여부는 해당 revision의 실행 결과로 확인한다.** 계약이나 테스트가 있다는 사실만으로 통과했다고 보지 않는다.
