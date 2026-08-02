# Pivot OpenSpec RPI Development

이 문서는 skill의 product requirements, 유지보수 결정을, roadmap을 관리한다. Runtime
행동의 Source of Truth는 `SKILL.md`와 `references/`다.

## Document Guide

- product requirement, 장기 유지보수 결정, roadmap 변화가 있을 때만 갱신한다.
- runtime 행동 규칙은 이 문서가 아니라 `SKILL.md` 또는 `references/`에 기록한다.

## Vision

### One Sentence

**AI agent가 필요한 근거를 조사하고, 명시적인 OpenSpec change에 따라 구현하며, 결과를 사람이 검토할 수 있는 증거로 입증하도록 돕는다.**

### Direction

사람은 다음 질문에 빠르게 답할 수 있다.

1. 무엇을 왜 변경했는가?
1. 어떤 근거가 변경을 정당화하는가?
1. 구현이 OpenSpec과 일치하는가?
1. 실제로 무엇을 검증했는가?
1. Review status가 `approved`, `changes_requested`, `blocked` 중 무엇인가?

## Product Requirements

### Problem and Users

RPI는 복잡하거나 불확실한 변경에서 agent가 근거를 먼저 확인하고, repository의
OpenSpec change에 따라 구현하며, 사람이 확인할 수 있는 증거로 결과를 검토하도록 돕는다.

대상 사용자는 OpenSpec을 이미 사용하는 project의 개발자와 maintainer다.

### Product Rationale

| 반복되는 실패 | RPI의 대응 |
| --- | --- |
| 시스템을 이해하기 전에 구현을 시작한다 | Research가 기존 evidence를 먼저 검증한다. |
| 요구사항과 코드가 서로 달라진다 | OpenSpec을 Source of Truth로 유지한다. |
| 여러 도구가 같은 plan을 중복 작성한다 | proposal, design, task는 OpenSpec이 소유한다. |
| 구현자가 자신의 가정을 스스로 검증한다 | Review가 evidence를 독립적으로 대조한다. |
| 변경보다 절차가 더 무거워진다 | 불확실성과 위험에 따라 rigor를 조절한다. |
| 사람이 긴 agent transcript를 읽어야 한다 | durable artifact에 결정, 근거, 상태만 남긴다. |

### Required Capabilities

| Capability | Requirement |
| --- | --- |
| Skill discovery | 명확한 positive trigger와 anti-trigger가 있는 valid `SKILL.md`를 제공한다. |
| Progressive disclosure | core instruction은 `SKILL.md`에, phase detail은 필요한 reference에 둔다. |
| Research | 기존 evidence의 충분성, risk, open question, status를 기록할 수 있다. |
| OpenSpec integration | proposal, requirements, design, tasks, archive는 설치된 OpenSpec workflow가 소유한다. |
| Implement | 승인된 OpenSpec task와 실행한 validation을 연결한다. |
| Review | spec, implementation, evidence를 대조하고 status와 다음 route를 기록한다. |
| Human readability | 사람이 결과, risk, decision, validation을 빠르게 확인할 수 있다. |
| Portability | skill directory 전체를 Windows와 WSL에서 사용할 수 있다. |
| Package integrity | runtime asset의 internal link와 `SKILL.md` frontmatter를 deterministic check로 검증한다. |

### Product Boundaries

- Research와 Review는 선택적 decorator artifact이며 OpenSpec change의 필수 gate가 아니다.
- RPI는 OpenSpec schema, lifecycle, command, archive 조건을 변경하지 않는다.
- runtime 규칙을 이 문서에 중복 정의하지 않는다.
- asset usage analytics, token·cost dashboard, 전체 agent action logging, custom OpenSpec schema,
  IDE 전용 plugin은 현재 범위가 아니다.

### Success Criteria

skill이 의도대로 동작하면 사람은 다음 질문에 빠르게 답할 수 있다.

1. 무엇을 왜 변경했는가?
1. 어떤 근거가 변경을 정당화하는가?
1. 구현이 OpenSpec과 일치하는가?
1. 실제로 무엇을 검증했는가?
1. Review status가 `approved`, `changes_requested`, `blocked` 중 무엇인가?

## Decisions

### 2026-08-02: Delegation Is Optional

- **Status:** Accepted
- **Decision:** 서브에이전트, fresh context, forked context는 필요한 경우에 선택할 수 있는 실행 수단이다.
- **Context:** 사용 가능한 agent, project 규모, user preference, 비용, 작업의 위험은 환경마다 다르다.
- **Consequence:** artifact, observed evidence, validation result, review verdict가 품질과 routing의 기준이다. 특정 agent topology나 delegation 여부는 필수 조건이 아니다.

## Roadmap

### Next Candidates

| Priority | Candidate | Trigger |
| ---: | --- | --- |
| P1 | OpenSpec config example | 같은 project rule이 반복됨 |
| P2 | Behavioral evaluation harness | manual dogfooding에서 반복 failure가 확인됨 |
| P2 | CI validation | 둘 이상의 contributor가 skill을 수정 |
| P3 | Asset usage·provenance analytics | maintenance decision에 usage evidence가 필요 |
| P3 | IDE extension 또는 custom OpenSpec schema | filesystem skill과 config로 부족 |

### Deferred

- 더 강한 독립성이 실제로 필요하다고 확인될 때만 별도 Research·Review helper를 검토한다.
- Review `approved` 없는 automatic archive는 도입하지 않는다.
