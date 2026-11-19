---
type: plan
title: "Harness Skill Context Review Bundle"
description: "7개 프로젝트 스킬의 컨텍스트 주입·문서 라우팅을 보존하면서 과잉 지시를 검토하고 개별 작업을 인계한다."
---

# Harness Skill Context Review Bundle

> [!IMPORTANT]
> **상태: 검토·작업 준비.** 이 번들은 구현 변경이나 삭제 승인이 아니다. 각 스킬의 기능을 실제로 확인한 후 최소 변경을 결정한다.

## Goal and Decision Boundary

스킬을 통한 **필요한 컨텍스트의 주입**, canonical 문서의 **조건부 라우팅**, **Progressive Disclosure**를 유지한다. 모델이 자체적으로 수행할 수 있는 일반 절차, 중복 계약, 불필요한 강제 단계가 실제로 존재하는지 검토한다. 토큰 절감이나 스킬 수 감소만을 목표로 삼지 않는다.

- **보존 우선:** 프로젝트 고유 계약, 문서 선택 기능, 안전·권한 경계, 명시적 사용자 범위.
- **검토 후보:** 일반론 반복, 다른 owner와의 중복, 실행할 수 없는 보편적 절차, 불필요한 reference·argument·출력 형식.
- **아직 미결정:** 각 스킬의 유지·축소·통합·삭제. 실제 활성화·동작 비교 전에는 삭제를 확정하지 않는다.
- **이번 PR 범위:** Inbox 분석 및 작업 인계 자료만. `.rulesync/skills/**`, route index, canonical docs, OpenSpec, source·tests는 변경하지 않는다.

## Skill Work Units

각 디렉터리의 `README.md`에 **관찰 근거 → 보존 기능 → 검토 항목 → 다음 작업 → 검증 조건**을 기록한다. 하나의 공통 결론을 일곱 스킬에 기계적으로 적용하지 않는다.

| Skill | Review focus |
| --- | --- |
| [Development Context](prj-load-context-development/README.md) | 문서 라우팅과 독립 리뷰 절차의 책임 분리 |
| [Review Context](prj-load-context-review/README.md) | 프로젝트 고유 reviewer gate와 일반 절차 분리 |
| [Research Workspace](prj-research-workspace/README.md) | 선택적 근거·템플릿 주입과 범용 workflow 비용 |
| [Code Review](prj-review-code/README.md) | 구현·테스트 리뷰의 실질적 고유성 및 reference 비용 |
| [Spec-Driven TDD RPI](prj-spec-driven-tdd-rpi/README.md) | OpenSpec 전용 controller와 중복 orchestration |
| [Testing Context](prj-testing-context/README.md) | 최소 조건부 문서 선택의 가치 |
| [Git/GitHub Context](prj-vcs-git-github/README.md) | operation별 정책 라우팅의 가치 |

## Execution Handoff

1. 우선 현재 branch의 실제 Skill, reference, route index, 정본 문서 및 실행 환경을 다시 확인한다. 이 번들의 판단은 **`main` `fe67f9eb6b76f4f4f3215c355dbdff91f689b7f7`** 정적 검토를 출발점으로 한다.
2. 스킬마다 실제 사용 시나리오 2개 이상(정상 선택과 near-miss)을 지정해 라우팅 대상과 loaded context를 기록한다. 더 작은 후보에서 기능과 정확성이 유지되는지 비교한다.
3. 일반적 모델 추론으로 대체할 수 있는 설명과 **반드시 주입해야 하는 프로젝트 고유 조건**을 구분한다. 하나의 ownership에만 규칙을 남긴다.
4. 개선은 스킬별로 작은 coherent change와 검증을 반복하되, 별도 결정이 필요한 삭제·통합은 증거와 영향을 보고한 후 수행한다. 필요한 경우 route metadata, 상호 참조 및 문서 링크까지 함께 동기화한다.
5. 각 작업 완료 시 적용 전후 선택·로딩, 필수 경계 보존, 달라진 동작 및 수행하지 못한 검증을 남긴다. Review 의견을 무조건 수용하지 않는다.

## Acceptance and Limitations

- 스킬이 컨텍스트를 주입하거나 문서를 라우팅한다는 이유만으로 중복·불필요로 판정하지 않는다.
- 모든 삭제·통합은 **대체 경로가 현재 repository route와 target runtime에서 실제 선택 가능한지** 확인한 뒤 결정한다.
- 코드·문서 변경과 독립 리뷰에 관한 권한·안전 기준은 해당 canonical owner에 남긴다.
- 현재 문서는 source 구조에 근거한 작업 가설이다. 토큰 절감율, 실제 routing success, 사용자 결과 품질은 측정되지 않았다.

## Evidence Pointers

- [Project route](../../../.agents/route/ROUTE.md) · [Skill index](../../../.agents/route/skills.jsonl)
- [Repository entry](../../../CHATBOT.md) · [Project instructions](../../../AGENTS.md)
- [OpenSpec schema](../../../openspec/schemas/spec-driven-tdd/schema.yaml)
- [Inbox policy](../../AGENTS.md)

**다음 실행 주체:** 로컬 작업 에이전트. 이 문서를 계획/검토 기준으로 사용하되, 각 스킬별 원문과 현재 상태를 직접 검증해 결과를 채택한다.
