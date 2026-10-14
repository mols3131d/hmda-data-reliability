---
type: plan
title: "CI README and Contract Bundle Plan"
description: "CI 문서를 README가 Goal·Principles·Patterns와 진입점을 소유하고 구체적인 계약은 별도 파일로 관리하는 번들로 전환할 계획입니다."
tags:
  - ci
  - documentation
  - contract
---

# CI README and Contract Bundle Plan

> [!NOTE]
> **구조 방향은 이번 요청을 따른다.** README는 진입점 기능과 Goal·Principles·Patterns를 함께 소유하고, 구체적인 계약은 별도 파일로 둔다. 이번 작업은 이 계획서 작성까지이며 실제 문서 이동·내용 변경은 수행하지 않는다.

## Direction

[기준 CI 문서](https://github.com/mols3131d/hmda-data-reliability/blob/cf9c1384bdd9c8c8cedc01c001f0806095ff766e/docs/development/ci.md)를 `docs/development/ci/` 번들로 전환한다. README를 단순 링크 목록으로 만들거나 Goal·Principles·Patterns를 다른 파일로 분리하지 않는다.

README만 읽어도 CI의 목적, 판단 기준, 운영 패턴과 다음에 읽을 계약을 알 수 있게 한다. 특정 검증의 적용 조건, 필수 결과, 제외 조건과 실패 처리는 해당 계약 파일이 소유한다. Workflow step이나 도구 하나마다 문서를 만드는 방식은 사용하지 않는다.

[앞선 제안서](proposal.md)는 이전 검토 기록으로 유지한다. 별도의 원칙 문서를 두는 당시 안이나 단일 문서 유지안이 아니라, 이번에 지정한 README 중심 구조를 이 계획의 기준으로 삼는다.

## Scope

실제 전환 시 범위는 다음과 같다.

- 기존 CI 문서의 의미를 보존하면서 README와 구체적인 계약으로 책임을 재배치한다.
- 문서 이동으로 달라지는 상대 링크, 외부 참조와 generated index를 갱신한다.
- 읽을 계약의 선택 안내, 공통 소유권과 필요한 짧은 사례를 보강한다.
- [Testing Guide](../../../docs/development/testing.md#pull-request-ci)의 실행 방법과 현재 동작 설명은 유지하고 CI 정책 참조만 새 owner로 연결한다.

CI 동작, 검사 범위, 병합 기준, 권한, workflow·script 구조와 OpenSpec capability는 변경하지 않는다. 문서 정리 중 정책 공백이나 구현과의 충돌을 발견하면 별도 판단 대상으로 기록하고, 새 규칙을 암묵적으로 추가하지 않는다.

## Target Layout

계획의 기본 배치는 다음과 같다. 파일명은 구현 시 같은 책임을 더 명확히 표현하는 이름으로 조정할 수 있으나 README의 소유 범위는 유지한다.

```text
docs/development/ci/
  README.md
  admission.md
  change-impact.md
  markdown-validation.md
  inbox-validation.md
  safety-authority.md
```

| Target | Owns | Source |
| --- | --- | --- |
| README | 번들 목적·사용 시점·읽기 안내, Goal, Principles, Patterns, 공통 Ownership | 도입부, Goal, Principles, Patterns, Contracts / Ownership |
| Admission | 통합 경계, prospective merge, required workflow 생성, 필수 검증의 병합 전 차단 | Contracts / Admission Boundary |
| Change Impact | 영향 범위 선택·제외·조합, 불확실할 때의 처리, CI 자체 변경의 필수 검증 | Patterns / Change Impact와 Admission의 영향 불확실성 규칙 |
| Markdown Validation | 변경 Markdown의 formatting·blocking lint 범위, 차이 제공과 write-back 경계 | Contracts / Markdown Boundary |
| Inbox Validation | 현재 변경 artifact의 검증, root metadata·이름 정합성, 과거 artifact와 무관한 검증 제외 | Contracts / Inbox Boundary |
| Safety and Authority | 최소 권한, secret·외부 도구의 신뢰 경계, 파생 상태와 자동화의 권한 한계 | Contracts / Safety and Authority |

기존 계약에 근거가 없는 Python·OpenSpec·도구별 계약 파일을 이번 이동만을 위해 추가하지 않는다. 이미 정해진 책임을 명확히 옮기는 것이 우선이다.

## README Design

[README 작성 정책](../../../docs/documentation/readme-authoring.md)에 따라 범위 소개와 읽기 선택을 먼저 제공하되, 사용자가 지정한 Goal·Principles·Patterns의 정본도 README에 유지한다.

권장 흐름은 다음과 같다.

1. **Introduction:** CI가 제공하는 근거와 번들의 사용 시점을 짧게 설명한다.
1. **Read Next:** 독자의 질문별로 해당 계약을 선택하는 작은 안내를 둔다. 단순 파일 목록이나 수동 목차를 복제하지 않는다.
1. **Goal:** 기존 목표를 유지한다.
1. **Principles:** 비용·위험·기여 환경·근거 수준·변경 권한의 판단 기준을 유지한다.
1. **Patterns:** 기존 운영 패턴과 CI Change Checklist를 소유한다.
1. **Ownership:** README, 개별 계약, workflow, script, Testing Guide와 Lefthook의 역할을 명시한다.

Patterns에는 Evidence Levels, Change Impact, Validation Surfaces, Contributor Environments, Autofix and Maintenance와 CI Change Checklist를 유지한다. 다만 Change Impact에 섞인 구체적인 필수 규칙은 계약 파일로 옮기고, README에는 위험에 비례해 좁히거나 넓히는 일반 패턴과 연결만 남긴다.

예를 들어 README는 "변경의 영향과 위험에 맞는 가장 좁은 충분한 검증을 선택한다"는 판단 패턴을 설명한다. Change Impact 계약은 "영향 범위를 결정할 수 없으면 검증을 넓히거나 실패시키며 불완전한 검증을 성공으로 처리하지 않는다"는 필수 결과를 소유한다. 같은 필수 문장을 양쪽에 복제하지 않는다.

계약의 적용 여부를 판단하는 데 꼭 필요한 경계는 Read Next에서 해당 owner로 바로 연결한다. 계약 원문을 읽지 않고도 세부 규칙을 모두 알 수 있는 요약본을 README에 만들지 않는다.

## Contract Design

계약 파일은 독립적으로 찾아 읽을 수 있도록 적용 범위와 필수 결과를 앞에 둔다. 모든 파일에 동일한 템플릿이나 요구사항 ID를 강제하지 않는다.

- 짧은 계약은 범위 소개, 명확한 규칙과 필요한 참조만으로 구성한다.
- 복잡한 계약은 적용·제외 조건, 실패 처리와 중요한 조합 사례를 추가한다.
- 다른 계약이 소유하는 공통 규칙은 링크로 참조한다. 예를 들어 Inbox formatting은 Markdown 계약을, Admission의 검증 선택은 Change Impact 계약을 따른다.
- 구현과 테스트 참조는 규칙을 확인하는 데 필요한 것만 연결한다. 파일별 고정 일대일 대응이나 전체 테스트 목록은 만들지 않는다.
- 정확한 glob, routing table, 명령·인자와 현재 실행 상태는 구현 또는 실행 근거에 남긴다. 기존 Markdown의 경로·도구명처럼 정책 자체를 식별하는 값은 보존한다.

Change Impact의 사례 후보는 CI만 변경한 경우, 의존성과 CI 테스트를 함께 변경한 경우, 영향 범위를 알 수 없는 경우다. 사례가 기존 계약에서 도출되는지와 [현재 실행 설명](../../../docs/development/testing.md#pull-request-ci)에 맞는지 확인한 뒤 포함한다. 관측된 구현을 그대로 새로운 필수 정책으로 승격하지 않는다.

## Migration Plan

### Map Content

1. 실행 시점의 CI 문서를 다시 읽고 기존 목표·원칙·패턴·계약을 위 배치에 대응시킨다.
1. 계약 문장별 owner를 하나로 정한다. 의미 중복과 정책·구현의 불일치는 이동 전에 구분한다.
1. README의 각 Pattern을 보존하면서 구체적인 계약만 추출한다. 일반 패턴을 없애거나 별도 원칙·패턴 파일을 만들지 않는다.

### Write Bundle

1. README에 목적·읽기 안내·Goal·Principles·Patterns·Ownership을 구성한다.
1. 별도 계약 파일로 기존 필수 규칙을 옮기고 파일 간 참조와 상대 경로를 맞춘다.
1. 이해에 필요한 짧은 사례와 조건만 보강한다. 기존 정책의 적용 범위와 차단·정보성 결과는 바꾸지 않는다.
1. 기존 단일 CI 문서는 참조 전환과 함께 제거한다. 동일한 규칙을 담은 두 정본을 병렬 유지하지 않는다.

### Update References

1. 기존 CI 문서를 실제로 참조하는 링크와 heading fragment를 찾는다. 번들 일반 참조는 README로, 특정 계약 참조는 해당 파일·heading으로 연결한다.
1. Development 진입점, Testing Guide와 관련 가이드의 링크를 갱신한다. 실행 설명이나 hook 정책을 CI 번들에 복제하지 않는다.
1. Repository-native generator로 문서 index를 재생성한다. Generated 행을 수작업으로 수정하지 않는다.
1. 테스트의 기존 문서 경로가 실제 참조인지 단순 변경 경로 예시인지 구분한다. 삭제된 경로를 예시로 사용한다는 이유만으로 테스트를 바꾸지 않으며, 실제로 깨지는 계약만 최소 범위에서 맞춘다.

## Verification

실제 문서 전환의 완료 기준은 다음과 같다.

| Check | Acceptance |
| --- | --- |
| README role | 첫 부분에서 목적·사용 시점·읽을 계약을 선택할 수 있고 Goal·Principles·Patterns의 정본이 README에 있다 |
| Meaning preservation | 기존 목표·원칙·패턴과 필수 계약이 누락·약화되지 않고 새로운 동작 요구사항이 추가되지 않는다 |
| Single owner | 구체적인 계약은 별도 파일이 소유하며 README·Testing Guide·다른 계약에 중복 정의하지 않는다 |
| Navigation | 계약 간 상대 링크와 외부 문서의 링크·fragment가 새 배치에서 유효하다 |
| Metadata and index | README metadata는 번들 전체를 설명하고 각 문서 frontmatter와 native generated index가 일치한다 |
| Behavior boundary | Workflow·script의 동작과 병합 정책은 바뀌지 않으며 필요한 경로 관련 테스트만 검증한다 |

검증은 변경 Markdown에 대한 native `rumdl check`, 상대 링크·fragment 검사, 적용되는 frontmatter·index 검사와 의미 보존 검토를 우선한다. 실제 영향을 받는 실행 계약이 있을 때만 해당 좁은 테스트를 수행하고 문서 이동 때문에 무관한 전체 테스트를 요구하지 않는다.

이 표는 이후 전환의 acceptance이며 현재 통과 상태가 아니다. 이번 계획서 자체에는 Inbox artifact 계약과 Markdown·링크 검사만 적용한다.

## Risks and Next Step

- README가 원칙·패턴과 세부 계약까지 모두 담아 원래 단일 문서로 되돌아가지 않도록, 구체적인 계약 본문은 별도 파일에만 둔다.
- 계약을 나눈 뒤 공통 규칙이 흩어지지 않도록 관련 파일끼리 참조한다. 영향 불확실성 규칙은 Change Impact가 소유하고 Admission은 이를 연결한다.
- 문서 이동과 동시에 CI 정책을 재설계하지 않는다. 새 검증 책임이나 정책 변경이 필요하면 별도 요청으로 다룬다.
- 기존 Inbox 제안과 비용 검토 기록은 수정·삭제하지 않는다. 이 계획서는 새 구조에 대한 후속 계획이며 PR의 코드 변경을 추가 승인하지 않는다.

다음 단계는 이 계획에 따른 문서 전환을 별도로 요청받은 뒤 시작한다. 현재는 새 Inbox 계획서만 작성하며 canonical 문서·CI·테스트·OpenSpec과 GitHub 상태는 그대로 둔다.
