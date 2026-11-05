---
type: research
title: "Reliability Agentic Refactoring — Source and Boundary Investigation"
description: "현재 Reliability·Review AI의 실제 변경 경계, 정본 계약, 병렬 개발 위험을 확인해 전체 에이전트 리팩터링의 범위와 순서를 판단한다."
tags:
  - reliability
  - ai-engineering
  - architecture
---

# Reliability Agentic Refactoring — Source and Boundary Investigation

> [!IMPORTANT]
> **조사 결론:** `reliability`와 AI 처리 책임을 구별하는 방향은 타당하다. 그러나 단순 디렉터리 4분할만으로 에이전트 기능이나 병렬 개발 가능성이 확보되지는 않는다. **기존 계약을 보존한 채 실제 변경 이유·생산자/소비자 관계·권위 있는 상태 변경 소유자를 기준으로 소스 리팩터링을 완료해야 한다.**

## Question

기존 소스를 어떤 경계로 변경해야 `reliability`의 결정론적 신뢰성 처리와 `reliability_ai`의 도구 사용·위임 실행·보고를 모두 구현하고, 여러 코딩 에이전트가 안전하게 병렬 개발할 수 있는가?

## Scope

- 확인 기준: `main` `061a2f6435879d466dda329c14b8232d03e95b7d` (2026-11-05 조회). 구현을 시작하기 직전에 revision과 진행 중인 변경을 다시 확인한다.
- 기존 공개 API, OpenSpec, 검증 경계, Langfuse 연동과 변경 이유를 확인한다.
- 계획 단계의 아키텍처·도메인 명칭은 **제안**으로 취급한다. 구현·평가·사용자 승인 완료로 간주하지 않는다.
- 외부 승인을 우회하는 DB 수정, 기존 PR의 history rewrite, 검증 없는 provider·framework 교체는 범위 밖이다.

## Findings

### F1. Deterministic Reliability는 유지해야 할 기반이다

[`reliability` 정본 가이드](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/domains/reliability.md)는 profile, incident detection, evidence, dbt impact, remediation draft, recovery, replay/evaluation을 담당한다. [`data_operations/incident_lifecycle.py`](https://github.com/mols3131d/hmda-data-reliability/blob/main/src/hmda_reliability/data_operations/incident_lifecycle.py)가 탐지·영향 분석·초안 작성을 조합한다.

기존 [`reliability/remediation/workflow.py`](https://github.com/mols3131d/hmda-data-reliability/blob/main/src/hmda_reliability/reliability/remediation/workflow.py)의 LangGraph는 `triage → rca → plan`이라는 고정된 결정론적 처리에 사용된다. LLM 기반 자율 조사 루프가 아니므로 별도로 비용 대비 가치를 검토해야 한다. 단순화하더라도 `RemediationDraft` 계약과 결과 의미는 보존해야 한다.

### F2. Review AI는 아직 도구 호출 에이전트가 아니다

[`review_ai/staged/service.py`](https://github.com/mols3131d/hmda-data-reliability/blob/main/src/hmda_reliability/review_ai/staged/service.py)는 제한된 세 단계의 텍스트를 수집하고 코드로 결과를 조립한다. 입력·provenance 보존과 실행 예산은 이미 존재하지만, 실제 근거 도구를 선택해 호출하고 조사 결과에 따라 다음 단계를 결정하는 동적 실행을 제공하는 것으로 확인되지 않는다.

[`reliability-agentic-review` Spec](https://github.com/mols3131d/hmda-data-reliability/blob/main/openspec/specs/reliability-agentic-review/spec.md)은 `null_spike` 제한, 불변 입력, evidence linkage, 단계별 응답과 미승인 복구 불가를 규정한다. 신규 capability를 도입한다면 정본 Spec 변경 또는 추가가 선행되어야 한다.

### F3. 기존 Runtime AI는 도메인 정책을 소유하지 않는다

[`runtime_ai`](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/domains/runtime-ai.md)는 provider-neutral 호출, timeout, retry, usage와 오류 경계를 담당한다. 조사 정책·Agent Task 상태·권한 판단을 단순히 provider adapter로 옮기면 책임이 혼합된다.

### F4. Recovery와 Approval의 권위는 한 곳에 유지해야 한다

현재 `reliability/remediation/`은 제안 초안 생성, `reliability/recovery/`는 승인·실행 경계를 담당한다. 목표 논리 영역을 `reliability.remediation`이라고 명명하더라도 현재 `remediation`의 물리적 구현과 Recovery를 무조건 합치는 것은 잘못된 출발점이다. AI는 권한 있는 공개 실행 경계만 호출할 수 있고 승인·상태 재검증을 생략하지 않는다.

### F5. 다중 코딩 에이전트와 제품 내부 Multi-Agent는 다르다

[Software Architecture for Multi-Agent Development](https://github.com/mols3131d/mols-agent-assets/blob/main/catalog/patterns/software-engineering/multi-agent-development-architecture.md)의 평가 대상은 여러 **개발 에이전트**가 동일한 소프트웨어를 변경할 때의 책임·공유 의미·조합 비용이다. 제품 내부에서 investigator/worker/reporter를 분리했다고 이 패턴에 부합하는 것은 아니다.

[Notion 패턴 적합성 보고서](https://app.notion.com/p/40f13d7e58b9810bae96f9ea42d80d80)는 v2가 방향에는 부합하지만 W1~W4 병렬성 과대평가와 W8에 집중된 늦은 통합 검증을 지적했다.

### F6. 기존 Review와 새 Agent는 서로 다른 계약이 필요하다

[현행 Agentic Review Spec](https://github.com/mols3131d/hmda-data-reliability/blob/main/openspec/specs/reliability-agentic-review/spec.md)은 고정 3단계·`null_spike`·텍스트 모드·**no tools**를 요구한다. Tool Calling을 기존 entry point에 조용히 추가하면 계약 위반이다. 기존 baseline을 보존한 신규 capability/entry point를 우선 검토하고, 기존 API·CLI의 제거 또는 대체는 명시적 OpenSpec 전환과 소비자 검증에 따른다.

### F7. 외부 진행 작업과 기술 채택 시점이 결합된다

- [PR #285](https://github.com/mols3131d/hmda-data-reliability/pull/285)는 `code-flow-map`, `mols-project-task-command-design`, `mols-dev-env-bootstrap-design` 도입과 bootstrap/명령 개선을 진행 중이다. 이번 PR의 스크립트·도구 설정·라우팅 변경과 수정 파일이 겹칠 수 있으며 #285의 잠금·생성 산출물을 수동 수정해서는 안 된다. **#285 완료가 #284의 전역 선행조건은 아니며**, 실제 공유 파일·명령 변경에 대해서만 병합/재기반화 순서를 정한다.
- [Framework 기술 조사](https://app.notion.com/p/40e13d7e58b981198335f151caf1a65c)는 LangChain `create_agent` → 필요 시 Deep Agents/직접 LangGraph를 권고하지만 **채택 확정이 아니다**. 기존 대화에는 #284 이후 프레임워크 고도화라는 순서가 있었으므로, #284에서 요구하는 *실제 Agent 동작*과 *후속 프레임워크 전면 도입*을 구분해야 한다.
- [MCP·Skills 조사](https://app.notion.com/p/40f13d7e58b9819384edccb4954968ea)는 MCP-first·Skills-first를 설계 후보로 제시한다. 모든 도구를 새 MCP 서버에 강제하거나 범용 Skills 로더를 직접 구현하라는 확정 요구사항은 아니다.

### F8. 로컬 모델과 Langfuse의 기존 상태를 보호해야 한다

- [PR #280 실험 인계](https://github.com/mols3131d/hmda-data-reliability/blob/main/inbox/github-280-improve-review-ai-output-quality/17-brief-review-ai-session-handoff.md)에는 Qwen3.5 4B의 실제 단계 실행과 Langfuse Dataset/Prompt 증거가 있다. **단계 완료는 의미적 정확성 또는 인간 유용성 평가 통과가 아니다.**
- [현행 Review AI 평가 가이드](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/development/review-ai-evaluation.md)에 따르면 프로젝트 Langfuse는 `4.15.6` 기준 native Prompt·Dataset·Experiment/trace를 사용한다. `setup` 재실행은 원격 Prompt 버전·Dataset 항목에 중복/변화를 만들 수 있으므로 기존 실행 상태를 조사하지 않고 반복하지 않는다.
- [PR #280 계획](https://github.com/mols3131d/hmda-data-reliability/blob/main/inbox/github-280-improve-review-ai-output-quality/00-plan-review-ai-output-quality.md)에 기록된 사용자 수용값은 **RTX 3070 8GB + Qwen3.5 4B에서 16K 우선 검증, 32K 조건부 후속 시험**이다. 실제 16K/32K 성능이나 Thinking ON/OFF 개선은 검증 전까지 성공으로 취급하지 않는다.

## Change Scenarios

| 대표 변경 | 주된 소유 | 선행 계약 / 결합 조건 | 각 변경의 검증 |
| --- | --- | --- | --- |
| 탐지 규칙 변경 | Reliability Assessment | Incident·Evidence 식별, 품질 정책 | 탐지/프로파일 테스트 + lifecycle 결과 |
| 근거 도구 하나 추가 | AI Investigation | 안정된 read-only Evidence 공개 API | 도구 입력 제한·provenance·실패/timeout |
| AI 조사 후 보고 형식 확장 | AI Execution/Reporting | Agent Task·Result·인용 계약 | 출력 계약·인간/상위 모델 가독성·trace |
| 승인된 조치 요청 연결 | Reliability Recovery + AI Execution 소비자 | Approval·Proposal·현재 상태·멱등성 | 무승인 차단, 재검증, 중복·부분 실패 |

세 번째·네 번째 사례는 한 파일만 바꾼다고 완결되지 않을 수 있다. 변경 경계를 확정할 때 기존 구현의 실제 수정을 시뮬레이션해야 한다.

## Options

| 후보 | 장점 | 위험 |
| --- | --- | --- |
| A. 현 구조 유지 | 이동·호환 비용 최소 | 고정 review와 새 Agent capability의 책임 혼재 가능 |
| B. 공개 계약·변경 접점 최소 보완 | 작은 변경으로 안정된 확장 기반 마련 | 내부 분리가 불충분할 수 있음 |
| C. 네 논리 영역 중심 재설계 | 장기적 책임 경계·확장성 개선 가능 | 대량 import 변경과 과도한 추상화 위험 |

**권장:** B로 공유 계약과 안전한 접점을 안정화하고, 실제 독립 변경 근거가 있는 부분만 C를 채택한다. 목표 PR은 코드·계약·테스트까지 **선택된 최종 구조로 리팩터링 완료**하는 것이며, 문서 준비만으로 완료 처리하지 않는다.

## Design Context Recovered

이전 v2 설계에서 보존해야 할 의미는 다음과 같다. 이는 **구현 계약 후보**이며 정본 OpenSpec이나 실제로 존재하는 모델 클래스를 뜻하지 않는다.

| 개념 | 보존할 역할 | 권위 |
| --- | --- | --- |
| `TaskEnvelope` | 목표·발급 주체/수신자·허용 도구·범위·예산·snapshot 참조 | AI 위임 작업 owner |
| `InvestigationResult` | 근거 연결 주장, 대립 가설, 미확정 사항, 실제 도구 호출 기록 | AI Investigation |
| `ActionProposal` / `ExecutionReceipt` | 조치 요청은 승인 아님. 실행 사실과 전후 상태의 정본 receipt는 **실행 도메인**이 소유 | Recovery 등 실제 실행 owner |
| `ReportEnvelope` | 인간/상위 모델 대상 facts·hypotheses·actions·blocked/unknown·추가 요청 분리 | AI Execution/Reporting |

Coordinator·Investigator·Verifier·Executor·Reporter는 도메인/서비스를 늘리는 명령이 아니라 **필요에 따라 조합할 수 있는 역할**이다. 단일 Agent + 도구로 먼저 검증하고, 병렬 독립 업무에서 성능 이점이 입증될 때만 분리한다. 자세한 작업별 설계·검증 게이트는 [계획서](01-plan-reliability-agentic-complete-refactor.md)가 소유한다.

## Unresolved Decisions

- `reliability.remediation`의 내부 `remediation` / `recovery` 물리 구조 유지 여부는 변경 이유 분석 후 결정.
- `reliability_ai.execution`이 지원하는 위임 작업 목록과 side-effect 권한은 명시적 계약으로 제한. 현 MVP의 read-only AI 경계 밖의 실제 데이터 변경은 별도 승인·Spec 변경 필요.
- 단일 tool-using Agent 대비 복수 Agent 분리가 품질·운영비를 개선하는지는 실험으로 판단. Multi-Agent를 필수 결과물로 가정하지 않는다.
- 프레임워크 교체는 선택 기술의 tool calling, pause/resume, 관측, 평가와 로컬 모델 지원을 검증한 뒤 결정한다.

## References

- [Vision](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/VISION.md) · [Architecture](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/ARCHITECTURE.md) · [MVP](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/mvp.md)
- [Domain Ownership](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/domains/OVERVIEW.md) · [Agentic Review Spec](https://github.com/mols3131d/hmda-data-reliability/blob/main/openspec/specs/reliability-agentic-review/spec.md)
- [User-authored Multi-Agent Development Architecture Pattern](https://github.com/mols3131d/mols-agent-assets/blob/main/catalog/patterns/software-engineering/multi-agent-development-architecture.md)
