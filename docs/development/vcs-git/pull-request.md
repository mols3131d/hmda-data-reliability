---
title: "Pull Requests"
description: "Branch 변경을 검토하고 repository에 반영할지 결정하기 위한 Pull Request scope, description, validation, review와 lifecycle 기준을 정의합니다."
categories:
  - software-engineering
tags:
  - ci
  - git
  - github
  - github-actions
  - testing
---

# Pull Requests

Pull Request는 branch의 변경을 검토하고 repository에 반영할지 결정하는 경계다.

## Scope

하나의 Pull Request는 하나의 변경 목적을 가진다. 같은 목적의 변경은 함께 다루고, 독립적인 새 목적은 별도의 branch와 Pull Request로 분리한다.

변경 단위와 branch naming은 [Branches](branch.md)를 따른다.

## Description

본문에는 **현재 변경을 판단하는 데 필요한 정보만** 남긴다. Section 구성, optional section과 validation 표시 형식은 [Pull Request Template](../../../.github/templates/pull-request.md)을 따른다.

- `Summary`는 변경 이유와 기대 결과를 먼저 설명한다.
- `Changes`는 시행착오나 파일 목록이 아니라 최종 동작, 계약 또는 구조의 변화를 기록한다.
- `Validation`은 실제 수행한 검증과 evidence를 연결하고, 실패하거나 확인하지 못한 결과를 숨기지 않는다.

다음 정보는 PR description에 복제하지 않는다.

- Agent의 작업 과정, 상세 reasoning, RPI 단계별 진행 기록과 시행착오
- commit별 변경 내역
- 판단에 필요한 추가 맥락 없이 GitHub UI나 CI가 이미 충분히 제공하는 정보
- OpenSpec change, inbox artifact 또는 canonical document가 소유하는 요구사항과 acceptance criteria

관련 OpenSpec change, inbox artifact 또는 canonical document가 있으면 `References`로 연결한다. 과정 자체를 보존할 가치가 있으면 owning artifact에 기록하고 PR에서는 최종 결과나 필요한 reference만 남긴다.

Optional metadata의 사용 조건과 형식은 [GitHub Templates](../../../.github/templates/README.md)에 위임한다.

## Review And Validation

Validation과 review 범위는 변경의 위험과 영향에 비례한다. 수행한 검증과 수행하지 못한 검증을 구분하고, 기존 review의 근거를 바꾸는 수정은 다시 검토한다.

### Review Readiness

Review readiness는 현재 변경과 validation evidence가 인간 review에 들어갈 만큼 current한지를 판단하는 lifecycle gate다. Correctness approval이나 merge readiness를 의미하지 않는다.

판정할 때 다음 조건을 현재 repository policy와 evidence에 대조한다.

- **Scope:** Pull Request가 하나의 coherent change purpose를 유지하고, 알려진 미완료 작업이나 의도하지 않은 scope drift가 없다.
- **Description:** 현재 Pull Request template과 policy를 충족하고, description의 scope와 claims가 실제 변경을 반영하며 실패하거나 수행하지 못한 validation을 숨기지 않는다.
- **Validation:** 변경 위험과 영향에 필요한 validation이 현재 base와 head의 조합 또는 이에 대응하는 prospective merge revision을 기준으로 수행되었다. 필요한 validation의 failure가 남아 있거나 stale하면 준비되지 않은 상태다.
- **Prior feedback:** 현재 revision에도 적용되는 blocking feedback이 남아 있지 않다. 실제 변경이나 명시적 scope decision으로 해결된 feedback은 UI thread가 unresolved라는 이유만으로 blocker로 취급하지 않는다.

Assessment는 다음 세 상태 중 하나다.

- `ready`: 판단에 필요한 evidence가 충분하고 readiness condition을 모두 충족한다.
- `not_ready`: 판단에 필요한 evidence는 충분하지만 하나 이상의 readiness condition을 충족하지 않는다.
- `blocked`: 필요한 scope, revision, validation 또는 mutable state evidence를 확인할 수 없어 readiness 자체를 신뢰성 있게 판단할 수 없다.

Assessment에는 판단에 사용한 base와 head revision 또는 동등한 prospective merge revision을 식별할 수 있는 state basis를 남긴다. Base, head 또는 validation/review evidence의 근거가 달라지면 이전 assessment는 stale하며 다시 판정한다.

Automation 통과만으로 correctness나 review completeness를 주장하지 않는다. `ready`는 인간 review 진입에 대한 evidence-backed assessment일 뿐 Ready for review 상태 변경, approval 또는 merge 권한을 부여하지 않는다.

Pull Request review의 기록 형식과 finding 기준은 [Pull Request Reviews](pull-request-review.md)를 따른다.

필요한 review와 required check가 완료되고 중요한 conflict가 해결된 뒤 merge한다.

## Lifecycle

```mermaid
flowchart TB
    draft["Draft PR"] --> current["Changes + validation current"]
    current --> review["Human Review"]
    review --> outcome{"Review outcome"}
    outcome -->|changes requested| current
    outcome -->|accepted + checks complete| merge(["Merge"])
    outcome -->|explicit close| close(["Close"])
```

수정 요청이 있으면 변경과 validation을 갱신한 뒤 인간 검토를 반복한다. 동일한 변경 목적은 기존 Draft PR을 이어가고, 목적이나 접근 방식이 달라지면 새 branch와 Pull Request를 사용한다.

## Agent Instructions

- Repository content 변경은 Draft Pull Request로 전달한다.
- Agent는 현재 변경과 evidence를 [Review Readiness](#review-readiness) 계약에 대조해 readiness를 판정하고 보고할 수 있다.
- `ready` assessment는 GitHub state 변경 권한이 아니다. 인간의 명시적 요청 없이 Ready 전환, 승인, merge, close 또는 auto-merge를 수행하지 않는다.
- 인간의 판단 없이 review thread를 해결 처리하지 않는다.
- 실패하거나 수행하지 못한 validation을 숨기지 않으며, 불명확한 응답을 승인으로 해석하지 않는다.

## Related

- [Branches](branch.md): Pull Request가 소유하는 변경 목적과 branch 기준
- [Commits](commit.md): Pull Request history를 구성하는 commit 기준
- [Pull Request Reviews](pull-request-review.md): Pull Request review 기준과 기록 방식
- [Pull Request Template](../../../.github/templates/pull-request.md): PR body의 section 구성과 작성 형식
- [GitHub Templates](../../../.github/templates/README.md): 공통 metadata 규칙
