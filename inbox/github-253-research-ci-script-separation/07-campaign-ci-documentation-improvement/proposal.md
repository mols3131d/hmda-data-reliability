---
type: proposal
title: "CI Documentation Contract Bundle"
description: "CI 문서를 책임별 번들과 운영 계약으로 정리할지 판단하기 위한 구조, 대안, 비용과 미결정 사항을 제안합니다."
tags:
  - ci
  - documentation
  - contract
---

# CI Documentation Contract Bundle

> [!NOTE]
> **검토용 제안이며 채택 여부는 미정이다.** 이 문서는 기존 정책을 변경하거나 구현을 승인하지 않는다. 지금은 제안서만 보존하며, 진행·부분 채택·보류·기각을 나중에 결정할 수 있다.

## Decision

검토할 제안은 [CI 문서](https://github.com/mols3131d/hmda-data-reliability/blob/cf9c1384bdd9c8c8cedc01c001f0806095ff766e/docs/development/ci.md)를 작은 문서 번들로 전환하고, CI가 보장해야 할 결과를 책임별 운영 계약으로 기술하는 것이다. **Workflow step 하나당 문서 하나가 아니라, 독립적으로 판단하고 유지할 검증 책임 하나당 문서 하나**를 기본으로 제안한다.

권장안은 아래의 작은 번들이지만, 현행 문서도 충분히 짧으므로 즉시 전환할 필요가 있다고 단정하지 않는다. 판단할 핵심은 파일 길이가 아니라 원칙·계약·실행 방법의 구분이 실제 탐색과 변경 비용을 줄이는지다.

## Current Context

2026-10-04에 확인한 문서 구조를 근거로 한다. 제안 채택 시에는 그 시점의 문서와 구현을 다시 확인한다.

- [CI 문서](https://github.com/mols3131d/hmda-data-reliability/blob/cf9c1384bdd9c8c8cedc01c001f0806095ff766e/docs/development/ci.md)는 약 158줄이며 목적, 원칙, 운영 패턴과 필수 계약을 함께 소유한다. 계약에는 병합 경계, Markdown·Inbox 검증 범위와 권한이 포함돼 있다.
- [Testing Guide](../../../docs/development/testing.md#pull-request-ci)는 현재 CI의 Python·의존성·테스트 선택 동작과 local 실행 방법을 설명한다.
- 정확한 실행 조건과 명령은 [workflow](../../../.github/workflows/ci-lite.yml)와 [CI 스크립트](../../../scripts/ci/)가 소유하고, [CI 계약 테스트](../../../tests/scripts/ci/)는 선택과 실행의 회귀를 검증한다.
- [문서 원칙](../../../docs/documentation/principles.md)은 하나의 의미에 하나의 정본을 요구한다. [문서 소유권](../../../docs/AGENTS.md)과 [OpenSpec 안내](../../../openspec/README.md)는 제품 capability의 canonical Spec과 개발 가이드를 구분한다.

현재 구조가 잘못됐다는 주장은 아니다. 개선 후보는 CI 변경을 검토할 때 **무엇을 보장해야 하는지**, **왜 필요한지**, **현재 어떻게 실행하는지**를 여러 성격의 설명에서 재구성해야 하는 비용이다.

## Goals and Boundaries

채택한다면 다음 결과를 목표로 한다.

- CI 정책 변경과 구현 변경을 구별해 검토할 수 있다.
- 필요한 검증 책임과 정상·실패·제외·복합 변경 시나리오를 좁은 문서에서 찾을 수 있다.
- 각 계약에서 구현과 테스트를 찾아갈 수 있으며, 문서 존재나 테스트 정의를 실제 통과 근거로 오해하지 않는다.
- 기존 병합 기준, 영향 범위의 안전한 fallback과 권한 경계를 유지한다.

이번 제안은 CI 동작 변경, 새로운 검사 추가, workflow 재설계, branch protection 변경 또는 OpenSpec capability 신설을 포함하지 않는다. 검토 중 발견하는 구현 결함이나 정책 공백도 문서 정리라는 이유로 함께 수정하지 않는다.

## Options

| Option | Approach | Benefit | Cost and Limitation |
| --- | --- | --- | --- |
| A | 현재 단일 문서를 유지하고 제목과 구분만 개선 | 이동·링크 관리 비용이 가장 작고 한 번에 읽기 쉽다 | 책임별 계약과 현재 동작 설명의 분산은 남을 수 있다 |
| B | 원칙과 계약을 두 문서로만 분리 | 적은 파일로 규범과 설명을 구분한다 | 계약이 커지면 주제별 탐색 부담이 다시 생긴다 |
| C | 진입점과 책임별 문서로 작은 번들 구성 | 필요한 계약만 읽고 독립적으로 검토·유지하기 쉽다 | 링크 이동, 정본 정리와 여러 파일 탐색 비용이 생긴다 |

**C를 우선 검토하되, 실질적인 탐색 이점이 부족하면 B 또는 A를 선택한다.** 파일 수 증가 자체를 개선으로 보지 않으며 workflow step별 세분화는 권장하지 않는다.

## Proposed Bundle

아래 경로와 이름은 제안이며 확정된 산출물이 아니다.

```text
docs/development/ci/
  README.md
  principles.md
  admission.md
  change-impact.md
  content-validation.md
  python-validation.md
```

| Document | Responsibility |
| --- | --- |
| README | 범위, 읽을 문서 선택, 정책·구현·테스트의 소유권을 안내한다. 긴 정책이나 현재 통과 상태를 복제하지 않는다 |
| Principles | 비용·위험·근거 수준, 기여 환경과 자동 수정의 판단 원칙 및 운영 패턴을 소유한다 |
| Admission | 병합 전 필요한 근거, prospective merge, workflow 생성, 필수 실패 전파와 권한의 공통 계약을 소유한다 |
| Change Impact | 변경 조합, 영향받는 consumer, 불확실한 경로의 fallback과 CI 자체 검증 선택을 소유한다 |
| Content Validation | Markdown·Inbox·OpenSpec·structured metadata의 적용 범위와 차단·정보성 결과를 소유한다 |
| Python Validation | lock·package build·lint·type·dependency boundary·테스트 검증의 책임과 근거 한계를 소유한다 |

각 계약은 공통 병합 원칙을 다시 정의하지 않고 Admission을 참조한다. Content Validation 안에서 독립적인 탐색·변경 필요가 생기면 추가 분리를 검토하되, 처음부터 모든 파일 형식이나 도구마다 문서를 만들지 않는다.

## Contract Format

스펙형 작성은 새로운 parser나 전용 framework가 아니라 **검토 가능한 요구사항과 시나리오를 쓰는 방식**을 뜻한다. 계약 문서에는 필요한 항목만 둔다.

| Section | Question |
| --- | --- |
| Scope | 어떤 변경과 위험에 적용되며 무엇을 다루지 않는가? |
| Requirements | CI가 반드시 보장해야 할 관측 가능한 결과는 무엇인가? |
| Scenarios | 정상·실패·제외·복합 변경에서 어떤 결과가 기대되는가? |
| Failure Policy | 무엇이 병합을 막고 무엇이 정보성 결과인가? |
| Evidence Boundary | 무엇을 증명하며 무엇은 증명하지 못하는가? |
| References | 구현과 관련 회귀 테스트는 어디에 있는가? |

실제 작성 시 결과를 명확한 요구사항으로 표현하되, 정확한 glob, 환경 변수명, 도구 버전, 명령 인자와 routing table은 구현에 남긴다. 특정 값 자체가 정책상 필수인 경우에만 계약에 포함하고 소유권을 명시한다. 기존 계약의 의미는 보존하며, 구현된 동작을 무조건 새로운 정책으로 승격하지 않는다.

예를 들어 영향 범위 계약은 다음과 같이 구성할 수 있다. 아래는 작성 형태를 보여주는 제안이며 새 요구사항의 채택이 아니다.

- **Requirement:** CI 자체 변경은 관련 계약을 검증하고, 별도의 source·dependency 변경이 요구하는 검증을 누락하지 않는다.
- **Scenario:** CI 스크립트만 바뀌면 CI 계약을 검증하며 무관한 domain 검증까지 확대하지 않는다.
- **Scenario:** 의존성과 CI component 테스트가 함께 바뀌면 전체 unit 검사 외에 필요한 non-unit 계약 검사를 유지한다.
- **Scenario:** 의존성과 unit 전용 모듈이 함께 바뀌면 필요한 unit 검증은 수행하되 빈 non-unit 실행으로 오실패하지 않는다.
- **Evidence Boundary:** 선택값과 호출 계약의 회귀 테스트는 실제 도구·domain runtime의 통과를 대신하지 않는다.

이 예시는 [classifier](../../../scripts/ci/classify_changes.sh), [pytest 실행 스크립트](../../../scripts/ci/pytest.sh), [선택 계약 테스트](../../../tests/scripts/ci/test_ci_classifier.py), [실행 계약 테스트](../../../tests/scripts/ci/test_ci_pytest.py)로 연결할 수 있다. 문서 하나와 테스트 파일 하나의 고정된 일대일 대응은 요구하지 않는다.

## Ownership

제안하는 문서는 **개발 운영 계약**이다. 제품 capability의 canonical OpenSpec과 별도의 경쟁 정본을 만들지 않는다. CI를 OpenSpec capability로 관리하려면 이 제안과 별도로 목적·범위·기존 소유권을 검토하고 승인해야 한다.

- 번들 안의 계약 문서는 CI가 보장해야 하는 결과를 소유한다.
- Workflow와 스크립트는 정확한 실행 구현을 계속 소유한다.
- Testing Guide는 test 선택·실행 방법과 필요한 짧은 설명을 유지하고 규범적인 CI 내용은 계약 문서로 연결한다.
- Test는 expected behavior를 검증하며, 실제 통과 주장은 동일 revision의 실행 근거로 확인한다.
- 이 Inbox 제안서는 어떤 정본도 override하지 않는다.

## Risks and Costs

| Risk | Response to Consider |
| --- | --- |
| 작은 문서를 너무 잘게 나눠 탐색 비용 증가 | 독립적인 판단·변경 책임이 없는 파일은 합치고 진입점에서 선택을 돕는다 |
| CI 계약과 Testing Guide에 같은 정책이 남음 | 옮긴 의미의 owner를 하나로 정하고 다른 위치는 짧은 설명과 링크로 바꾼다 |
| 실행 세부사항을 문서에 복제해 drift 발생 | 결과와 불변 조건을 문서에 두고 구체적 command와 mapping은 구현으로 연결한다 |
| 현재 구현을 계약으로 고정하며 의도치 않은 정책 변경 | 기존 정책·관측된 구현·제안된 요구사항을 구분하고 충돌은 별도 판단으로 남긴다 |
| 문서 이동으로 기존 링크·생성 index·경로 기반 테스트가 깨짐 | 승인된 이동 범위에 참조 갱신, native index 재생성과 관련 경로 테스트 검증을 포함한다 |
| 스펙형 문서를 실제 검증 완료 근거로 오해 | 각 계약의 근거 한계를 명시하고 통과 상태를 durable 계약에 기록하지 않는다 |

실제 읽기 시간 단축이나 유지보수 비용 감소는 아직 측정하지 않았다. 권장안은 구조에 대한 판단이며 효과가 입증됐다는 주장은 아니다.

## Conditional Adoption

진행을 결정하는 경우에만 다음 순서를 검토한다.

1. A·B·C 중 범위와 운영 계약의 소유권을 확정한다.
1. 기존 문단을 분류해 원칙·계약·실행 방법의 대응을 확인하고 의미 변경 없이 옮길 최소 범위를 정한다.
1. 대표 계약 하나로 형식을 확인한 뒤 같은 판단 기준으로 나머지를 정리한다.
1. 기존 참조와 generated index를 갱신하고, 문서 경로를 사용하는 관련 테스트를 최소 범위에서 맞춘다.
1. 문서의 의미 보존·소유권·탐색성을 검토하고 Markdown·링크·frontmatter·index 및 필요한 테스트를 검증한다.

채택된 변경의 완료 기준 후보는 다음과 같다.

- 기존 필수 계약이 누락되거나 약화되지 않고, 새 동작 요구사항이 암묵적으로 추가되지 않는다.
- 각 계약의 owner가 하나이며 원칙, 실행 방법과 제품 capability Spec의 경계를 구분할 수 있다.
- 필요한 계약에서 구현과 테스트로 이동할 수 있고, 실패·제외·복합 변경 시나리오가 읽힌다.
- 기존 링크, generated index와 관련 경로 테스트가 새 배치와 일치한다.
- Workflow·스크립트의 CI 동작은 이 문서 정리 때문에 바뀌지 않는다.

## Open Decisions

- 실제로 번들화할지, 원칙과 계약만 분리할지, 현행 구조를 유지할지
- 처음부터 여섯 문서로 나눌지, 대표 계약을 본 뒤 더 작은 구조로 시작할지
- 기존 CI 문서의 이동과 Testing Guide의 정본 정리를 같은 변경에 포함할지
- 스펙형 형식만 사용할지, 추적 필요가 확인된 요구사항에 한해 식별자를 부여할지

지금 필요한 것은 시행 승인이 아니라 이 선택지의 검토다. 결정 전에는 제안서 외의 문서·CI·테스트·OpenSpec을 변경하지 않는다.
