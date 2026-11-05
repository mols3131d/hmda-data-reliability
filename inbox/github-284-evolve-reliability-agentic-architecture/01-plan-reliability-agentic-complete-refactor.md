---
type: plan
title: "Reliability Agentic Refactoring — Complete Implementation Plan"
description: "PR #284의 전체 리팩터링 완료 목표, 계약 선행조건, 구현·평가 작업, 병렬화 경계와 검증 가능한 완료 기준을 정의한다."
tags:
  - reliability
  - ai-engineering
  - refactoring
---

# Reliability Agentic Refactoring — Complete Implementation Plan

> [!IMPORTANT]
> **PR #284의 완료 목표는 자료 준비가 아니라 소스 리팩터링의 실제 완료다.** 결정론적 Reliability의 안전한 동작을 보존하면서 `reliability_ai`가 실제 도구를 사용하고, 위임받은 작업을 수행·추적하며, 인간 또는 상위 모델에 근거 기반 보고를 제공하도록 구현한다. 코드·Spec·테스트·실행 증거까지 완료되어야 한다.

## Goal and Boundary

- **Result:** `reliability.assessment` / `reliability.remediation` / `reliability_ai.investigation` / `reliability_ai.execution`의 네 논리적 책임을 현재 코드에서 검증 가능한 경계로 완성한다. 필요하면 내부 더 작은 변경 단위로 분할한다. 물리 폴더 네 개를 기계적으로 만드는 것은 목표가 아니다.
- **Agent capability:** 고정 채팅 입출력 대신 **동적 도구 선택·실제 조회·가설 검토·작업 진행/중단·실행 결과 보고**를 갖춘 동작 가능한 use case를 제공한다. 조사 도중 추가 근거가 필요하면 제한된 범위에서 다시 탐색할 수 있어야 한다.
- **Execution:** 위임된 작업은 명시된 범위·예산·권한 안에서만 실행한다. read-only 도구 호출은 기본값이다. 실제 Recovery/DB 변경은 기존 정본 RecoveryProposal·Approval·재검증·lock·멱등성 경계를 통과하는 경우에만 검토한다. 기존 MVP를 넘어서는 AI 쓰기 권한은 **별도의 명시적 승인 및 정본 Spec 변경이 필요**하며 이번 PR의 준비 문서가 권한을 부여하지 않는다.
- **Out of scope:** 근거 없는 마이크로서비스·이벤트 버스 도입, 무단 DB mutation/권한 상승, 과거 Langfuse/Git 기록 재작성, 연관 없는 타 도메인 리팩터링.
- **Current state:** 2026-11-05 최초 Draft PR 준비. 구현·테스트·평가는 아직 수행하지 않았다.

## Ownership and Change Seams

| 논리적 책임 | 소유할 의미 | 공개 접점 / 소비 방향 | 보호할 불변식 |
| --- | --- | --- | --- |
| `reliability.assessment` | 결정론적 프로파일·탐지·quality gate·Evidence·impact | `data_operations` 조합, `reliability_ai` read-only 소비 | 동일 입력의 근거 의미, incident identity |
| `reliability.remediation` | 기계적 조치 초안·외부 승인 기반 Recovery·재검증 | Draft·Proposal·Recovery 공개 API | Draft ≠ 승인, 정확한 target/proposal, stale approval 차단 |
| `reliability_ai.investigation` | 도구 기반 근거 조회·가설/불확실성·조사 기록 | `reliability` 계약과 제한된 Tool API 소비 | 근거·출처 보존, tool output 불신, 무단 mutation 차단 |
| `reliability_ai.execution` | 위임 Task·실행 흐름·결과 기록·인간/상위 모델 보고 | Investigation 결과, 명시적으로 허가된 tools·`runtime_ai` 소비 | 재시도·취소·상태 전이·실행 권한 분리 |

`runtime_ai`는 provider-neutral 호출·오류·예산을 소유하고, 업무 정책·승인 의미를 소유하지 않는다. 기존 `reliability/remediation/`과 `reliability/recovery/`는 서로 다른 변경 이유가 입증된다면 물리적으로 유지한다. `data_operations` 같은 상위 application 조합 책임을 AI 하위 모듈마다 중복 구현하지 않는다.

## Implementation Work

### W0 — Baseline and Change Contract

- [ ] 현재 `main`/PR head, 공개 import/API, CLI, OpenSpec, 소비자, 테스트, Langfuse Prompt/Dataset/trace·기존 실행 증거를 전수 대조한다.
- [ ] 대표 변경(탐지 규칙, evidence 도구 추가, AI 보고 형식, 승인된 조치 요청)을 대상으로 현 구조 유지(A)·접점만 개선(B)·구조 재설계(C)의 수정 범위와 비용을 비교한다.
- [ ] `Incident`, `Evidence`, `RemediationDraft`, `RecoveryProposal`, `Approval`, Agent Task/Result의 정본 소유, 오류·재시도·상태 의미, 기존 API 이전 전략을 확정한다.
- [ ] Spec에서 기존 `null_spike` 고정 세 단계 검토와 새 도구 호출 Agent capability의 **현행/신규 계약**을 구분한다. 사용자 의도가 불명확한 정책 변경은 승인 없이 강행하지 않는다.

**Gate:** 생산자–소비자 계약과 금지된 변경이 식별되고 기존 테스트 baseline 및 migration target이 기록되어야 코드 재배치를 시작한다.

### W1 — Deterministic Reliability Refactoring

- [ ] Assessment/Remediation의 실제 변경 책임을 따라 소스를 정리하고 내부 import·공개 export·호출 경로를 일관되게 이전한다.
- [ ] quality gate, Incident·Evidence·impact, Draft, Recovery의 관찰 가능한 동작과 오류 의미를 보존한다.
- [ ] 고정 `triage → rca → plan` LangGraph의 실제 가치와 대체 비용을 검증하고, 불필요하면 결정론적 서비스로 단순화한다. 결과 API는 유지한다.
- [ ] Approval의 exact proposal binding, revalidation, 멱등·재시도·부분 실패와 replay 증거를 검증한다.

**Gate:** AI 없이 Reliability lifecycle와 승인 기반 Recovery 경로가 정상 동작하고 관련 기존 회귀 테스트가 통과한다.

### W2 — Reliability AI Contract and Migration

- [ ] `review_ai` 기능을 `reliability_ai` 책임으로 이전한다. 단순 rename에 그치지 않고 기존 prompt, provider, evaluation, CLI, provenance, persisted artifact와 import 소비자에 대한 호환 정책을 적용한다.
- [ ] Agent Task의 입력 스냅샷·capability 범위·tool budget·상태·결과·불확실성 및 reporting contract를 확정하고 검증한다.
- [ ] 기존 결과 데이터·과거 실행 추적을 삭제하거나 새 버전으로 소급 재작성하지 않는다.

**Gate:** 새 도메인의 공개 API와 기존 사용 경로의 이전 전략이 통합 테스트와 Spec에 반영된다.

### W3 — Tool-Using Investigation Agent

- [ ] 임의 SQL이나 원시 DB 쓰기가 아닌 **유효성 검증된 bounded read-only** Evidence/lineage/profile 조회 도구를 제공한다. MCP는 실제 필요에 따라 adapter 또는 server를 선택한다.
- [ ] Agent가 도구를 선택·호출하고, 실제 결과에 따라 추가 확인/정지/보고 경로를 선택하는 동적 루프를 구현한다. 단일 에이전트로 시작하며 모델 한계에서 안전하게 실패한다.
- [ ] 도구 호출 상한, 컨텍스트·토큰·시간 예산, 잘못된 tool arguments, injection, 빈 응답, 중단·취소, provider 실패, 순환 탐색을 제한한다.
- [ ] Evidence provenance, 도구 실행 결과, 확인되지 않은 주장과 추가 확인 필요성을 별도로 보존한다.

**Gate:** 로컬 모델 또는 재현 가능한 provider harness에서 **실제 두 단계 이상 도구 사용을 수반하는 조사**와 제한·실패 경로가 입증된다. 실행 가능한 소스와 테스트가 있어야 하며 단순 프롬프트 예시는 불충분하다.

### W4 — Delegated Execution and Reporting

- [ ] 권한 검증된 위임 Task의 생성·진행·중단·결과 처리 및 실패 원인을 구현한다. 작업 결과를 인간 또는 상위 모델이 이용할 수 있는 구조화 보고/요약으로 전달한다.
- [ ] 도구·계약별 side-effect 위험을 판정하고 실제 mutation은 별도의 authoritative Recovery API와 외부 승인을 필요로 하게 한다.
- [ ] 완료·부분 완료·실패·재시도·취소를 구분하고 작업/도구 호출 근거를 남긴다.
- [ ] 협업형 복수 에이전트는 단일 Agent보다 실질적 성능·비용 개선이 입증될 때만 같은 목표 범위 안에서 선택적으로 채택한다. 임의 fan-out 금지.

**Gate:** 허용된 위임 작업이 실제로 실행되고 결과와 불확실성을 보고한다. 무승인 상태 변경 경로는 차단된다. 사용자가 요구한 실제 쓰기 권한 도입은 별도 승인 없이는 미완료 범위로 보고한다.

### W5 — Evaluation and Integrated Validation

- [ ] Langfuse Native Prompt·Tracing·Dataset·Experiment를 가능한 범위에서 직접 사용하고 중복 자체 구현을 줄인다. 기존 이름·버전·실행 provenance를 보존한다.
- [ ] 기존 고정 review baseline 대비 새 조사/보고의 유용성, 사실성, 도구 성능, 지연·토큰 비용을 비교한다. 사람 평가에서 정확한 증거와 '다음 판단에 유용한 추가 가치'를 판단한다.
- [ ] 개별 PR/작업 단위부터 domain 테스트 + 소비자 계약 검증 + 실패 경로를 거쳐 전체 integration/regression 검사로 확장한다. 최종 취합에 최초 통합을 미루지 않는다.
- [ ] 도메인 guide, Architecture, OpenSpec, tests, CLI, 평가 guide와 실행 명령을 실제 동작에 일치시킨다.
- [ ] 개발 에이전트 협업 평가는 제품 에이전트의 성능과 별도로 독립 완료·교차 계약 위반·통합 오류·재작업 비용을 측정한다.

**Gate:** 최신 PR head/base 조합을 대상으로 필요한 테스트와 CI·실제 실행 증거가 충족되고, 기존 Safety invariant의 위반이 없다.

## Parallel Work and Integration

| 관계 | 허용 방식 | 예시 |
| --- | --- | --- |
| 독립 | 계약을 소비하며 각자의 테스트로 완료 가능한 변경만 병렬 | 서로 다른 read-only evidence tool |
| 생산자–소비자 | 공개 스키마·오류 의미를 먼저 합의하고 호환 전환 후 병렬 | Reliability Evidence API와 Agent Tool |
| 결합 | 함께 결정하거나 순차 변경하고 연결 검증을 즉시 수행 | Approval state transition과 AI 실행 소비자 |

하나의 **PR #284가 전체 목표 결과물을 소유**한다. 여러 작업 agent가 병렬로 구현하더라도 동일한 PR head에 무제한 동시 쓰기를 허용하지 않는다. 각 작업의 owning branch·계약·통합 검증 지점을 분명히 하고, 공유 API·Spec의 변경은 단일 소유자가 조정한다.

## PR Completion Criteria

모든 조건이 충족되어야 **리팩터링 완료**다.

- [ ] 결정론적 Reliability의 새 논리 책임·공개 접점·소스 구조가 구현되어 기존 탐지·근거·복구 불변식이 유지된다.
- [ ] `review_ai`의 `reliability_ai` 전환과 기존 API·CLI·테스트·문서·provenance 마이그레이션이 완료된다.
- [ ] Investigation Agent가 실제 허용 도구를 호출하고 추가 근거를 탐색하는 동작을 입증한다.
- [ ] Execution이 명시적으로 위임·허용된 작업을 실행·중단·실패 처리하고 인간/상위 모델 대상 근거 보고를 생성한다.
- [ ] 권한 없는 실행·도구 오용·stale approval·중복 요청·실패 시 무단 DB 변경이 발생하지 않음을 검증한다.
- [ ] Prompt/experiment/trace·human value 평가가 기존 baseline과 비교되고 기록이 보존된다.
- [ ] 관련 OpenSpec 및 도메인 정본 문서, 테스트, 예시 실행 절차가 현재 구현과 일치한다.
- [ ] 최신 base/head 기준 CI·회귀·통합·실행 증거 및 blocking review가 정리되어 merge readiness를 별도로 평가할 수 있다.
- [ ] multi-agent 개발 패턴의 독립 변경, 공유 계약 소유와 통합 정확성을 실제 변경 결과로 검토했다.

**다만** Ready/merge 전환은 별도 인간 검토에 따른다. 구현이 미완료일 때는 문서 준비가 끝났더라도 PR 완료를 주장하지 않는다.

## References

- [Research for this PR](00-research-reliability-agentic-boundary-audit.md)
- [Notion Assessment](https://app.notion.com/p/40f13d7e58b9810bae96f9ea42d80d80) · [User Pattern](https://github.com/mols3131d/mols-agent-assets/blob/main/catalog/patterns/software-engineering/multi-agent-development-architecture.md)
- [Vision](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/VISION.md) · [MVP](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/mvp.md) · [Domain Map](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/domains/OVERVIEW.md)
