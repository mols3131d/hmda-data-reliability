---
type: plan
title: "Harness Skill Context Review Bundle"
description: "7개 프로젝트 스킬의 컨텍스트 주입·문서 라우팅을 보존하면서 과잉 지시를 개별 검토하고 작업을 인계한다."
---

# Harness Skill Context Review Bundle

> [!IMPORTANT]
> **상태: 검토·작업 준비.** 이 문서는 구현·삭제 승인이나 정본 정책이 아니다. 각 스킬의 실제 선택과 사용을 검증한 뒤 최소 변경을 결정한다.

## Goal

7개 프로젝트 스킬에 대해 **컨텍스트 주입**, canonical 문서 **라우팅**, **Progressive Disclosure**를 지키면서 일반적 모델 추론으로 충분한 설명, 중복된 계약, 과도한 필수 절차와 reference를 구별한다. 토큰 수·스킬 수 감소 자체를 완료 조건으로 삼지 않는다.

- **보존:** project-specific context 선택, 문서·Skill·Rule 라우팅, runtime에 필요한 차이, 명시적 권한·scope·안전 경계.
- **의심 후보:** 모델에게 당연한 범용 조언, 다른 owner가 이미 소유한 계약의 장문 복제, 불필요한 매개변수·출력 양식·반복 단계, 무조건적 하위 스킬 로딩.
- **미결정:** 7개 스킬의 유지/축소/통합/삭제. 삭제는 대체 경로의 실제 discoverability와 행동을 검증한 경우에만 제안한다.
- **이번 PR:** Inbox의 검토·인계 산출물만 생성한다. 실제 source와 route index는 수정하지 않는다.

## Independent Work Units

각 하위 디렉터리의 `README.md`가 개별 작업 단위다. 우선 **Preserve**를 기준으로 현재 원문을 직접 확인한 후, **Review candidates**를 검증하고 **Tasks**를 수행한다.

| Skill | Focus |
| --- | --- |
| [Development Context](prj-load-context-development/README.md) | 개발 문서 라우팅과 독립 Review gate 중복 |
| [Review Context](prj-load-context-review/README.md) | caller-owned Review 계약과 orchestration 과잉 |
| [Research Workspace](prj-research-workspace/README.md) | Research 템플릿 선택과 범용 절차 |
| [Code Review](prj-review-code/README.md) | 구현·테스트 리뷰의 고유한 판단 및 reference |
| [Spec-Driven TDD RPI](prj-spec-driven-tdd-rpi/README.md) | OpenSpec 특수 control과 generic loop 중복 |
| [Testing Context](prj-testing-context/README.md) | 테스트용 조건부 문서 선택 |
| [Git/GitHub Context](prj-vcs-git-github/README.md) | operation별 VCS 정책 라우팅 |

## Method and Handoff

1. 기준: repository `main` `fe67f9eb6b76f4f4f3215c355dbdff91f689b7f7`에서 정적 검토했다. 로컬 작업 시작 시 **PR head, 현재 source, route index 및 runtime 지원**을 재확인한다.
2. 스킬별로 사용해야 하는 시나리오와 선택되면 안 되는 near-miss를 최소 하나씩 재현한다. 실제 선택 스킬, 추가 로드된 문서, 불필요한 로딩과 누락된 계약을 기록한다.
3. **프로젝트 고유 규칙을 더 작은 owning source에 보존**한다. 일반론/중복을 제거하되 Skill을 통한 문서 선택 기능을 불필요한 것으로 취급하지 않는다.
4. 단일 Skill별 가장 작은 coherent change와 검증을 우선한다. 이 변경이 다른 스킬, `CHATBOT.md`, `AGENTS.md`, `inbox/_guidelines/`, generated route index에 미치는 영향을 확인한다. 파생 파일은 정해진 생성 과정으로 갱신한다.
5. 각 작업의 결정과 검증 근거를 해당 디렉터리에서 갱신한다. 자동으로 모든 리뷰 제안을 수용하지 않는다. 요청되지 않은 scope expansion, merge, history rewrite는 수행하지 않는다.

## Acceptance

- 필수 컨텍스트가 올바른 요청에서 계속 주입·라우팅되고, 무관한 요청에서 불필요하게 로드되지 않는다.
- 각 스킬의 프로젝트 특화 가치와 일반적 중복을 근거로 구분한다.
- 보존되는 boundary, 제거되는 절차와 실제 검증을 명시한다.
- 성능 지표가 없으면 토큰 절감률·라우팅 정확도·동작 parity를 검증했다고 주장하지 않는다.

## References

- [Repository instructions](../../../AGENTS.md), [Chatbot entrypoint](../../../CHATBOT.md), [Routing entrypoint](../../../.agents/route/ROUTE.md)
- [Skill discovery index](../../../.agents/route/skills.jsonl), [OpenSpec implementation schema](../../../openspec/schemas/spec-driven-tdd/schema.yaml)
- [Inbox ownership](../../AGENTS.md)

**Handoff:** 각 스킬의 원문·관련 canonical guide가 진실의 원천이다. 본 번들의 후보 판단은 작업 지시나 자동 승인된 수정안이 아니며, 로컬 작업 에이전트가 근거를 재검토한 뒤 채택·기각해야 한다.
