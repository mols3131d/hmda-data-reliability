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

## Agent Contract and Runtime Decisions

**기존 제안서 v2의 핵심 맥락 복원:** 아래는 아직 새 코드에 구현되거나 정본으로 채택된 계약이 아닌, 구현 시 검토할 *conceptual design*이다. 필요성이 입증되지 않은 공통 모델·서브에이전트·서비스를 미리 생성하지 않는다.

| 계약 후보 | 필요한 의미 | 정본 owner |
| --- | --- | --- |
| `TaskEnvelope` | `task_id`·상위 task·요청자/수신자·goal/target·허용 작업·예산·deadline·approval policy·고정 snapshot refs | `reliability_ai` |
| `InvestigationResult` | 증거와 연결된 findings·서로 다른 가설·불확실성·누락 자료·실제 도구 결과/호출 기록 | AI Investigation |
| `ActionProposal` | 실행 요청·대상·리스크·사전 검증·승인 필요 여부. **승인도 RecoveryProposal 정본도 아님** | AI Execution의 요청; 실제 Recovery 계약은 Reliability |
| `ExecutionReceipt` | 실행자·승인 참조·before/after·실제 성공/부분/실패·rollback/replay 추적 | **실제 조치를 수행한 도메인의 정본**, AI는 참조 |
| `ReportEnvelope` | `human`/`supervisor` 수신자, facts/hypotheses/actions 구분, evidence refs, 완료/차단/미확정, 다음 요청 | AI Execution/Reporting |

- **작업 상태와 권한:** 최소 queued/running/completed/failed/blocked/partial/awaiting-approval를 검토하되, 실제 상태·재개·멱등성은 사용 사례로 정한다. 상위 모델의 task 위임은 사람의 외부 승인이나 실행 도구 권한을 대체하지 못한다.
- **협업 역할:** Coordinator(계획·예산·범위), Investigator(추가 근거), Verifier(근거·모순·누락), Executor(허가 도구 호출), Reporter(인간/상위 모델 보고). 역할은 Skills/함수/실행 단계로도 구현할 수 있다. 독립 조사 결과를 합칠 때는 task/revision/evidence ID와 충돌을 보존하며, 단순 중복 인용을 독립 검증으로 계산하지 않는다.
- **Evidence identity:** 기존 사건의 불변 Evidence snapshot·dbt projection identity와 런타임 read-only 조회 결과를 구분한다. 도구 응답에 source·관측 시각·snapshot/projection reference를 남기고, 후속 조회의 최신값을 과거 사건 사실로 덮어쓰지 않는다.
- **Tool Gateway:** `get_incident_evidence`, `compare_profiles`, `inspect_dbt_impact` 같은 bounded read-only typed tool 2~3개를 우선 후보로 두고 필요 시 MCP adapter/server를 연결한다. 허용 작업과 대상은 코드의 allowlist·스키마·권한 검사로 제한한다. 범용 SQL, `dbt build`, Airflow DAG 제어와 Recovery mutation을 모델에 직접 노출하지 않는다.
- **Agent Skills:** `incident-investigation`, `remediation-safety-review`, `evidence-reporting` 같은 절차 자산은 후보이며, Skills 자체는 권한을 부여하지 않는다. 실제 추가 가치가 있는 경우에만 점진적 로딩을 선택한다.

### Framework Sequencing

사용자가 확정한 **PR #284의 목표는 '리팩터링 완료'**이며, 여기에는 동작 가능한 도구 사용·위임·보고 기능이 포함된다. 다만 **LangChain·LangGraph·Deep Agents 전체 도입 및 멀티에이전트 확대는 자동 완료 조건이 아니다.** 기존 논의의 '#284 완료 이후 프레임워크 고도화'와 충돌하지 않도록 다음을 구별한다.

1. **#284 안에서 필수:** 기존 정본 계약을 깨지 않는 새로운 read-only agent use case를 실제 실행·검증한다. framework-native 기능이 필요하면 `create_agent` 등의 **최소 PoC를 먼저 검증**하고, 별도 채택 결정 없이 과도한 자체 loop/HITL/Skills/checkpoint 구현이나 대규모 의존성 이전을 강행하지 않는다.
1. **#284 이후 선택:** Deep Agents의 Skills/subagents, LangGraph의 장기 상태·재개, 다중 에이전트 협업 등은 동일 입력·도구·모델·평가 기준에서 추가 편익을 보인 경우에만 확대한다. #284 내부의 최소 runtime 선택이 후속 표준 프레임워크 선정을 확정하지 않는다.
1. **채택 전 확인:** `runtime_ai`의 provider-neutral 역할과 SDK 호출 중복, 현재 Python/uv 잠금, Ollama tool-call 품질, Langfuse 4.15.6 호환, 로컬 비용. [Framework 검토](https://app.notion.com/p/40e13d7e58b981198335f151caf1a65c)·[MCP/Skills 검토](https://app.notion.com/p/40f13d7e58b9819384edccb4954968ea)는 제안이며 실제 채택·검증이 아니다.

## Implementation Work

### W0 — Baseline and Change Contract

- [x] 현재 `main`/PR head, 공개 import/API, CLI, OpenSpec, 소비자, 테스트, Langfuse Prompt/Dataset/trace·기존 실행 증거를 전수 대조한다.
- [x] 대표 변경(탐지 규칙, evidence 도구 추가, AI 보고 형식, 승인된 조치 요청)을 대상으로 현 구조 유지(A)·접점만 개선(B)·구조 재설계(C)의 수정 범위와 비용을 비교한다.
- [x] `Incident`, `Evidence`, `RemediationDraft`, `RecoveryProposal`, `Approval`, Agent Task/Result의 정본 소유, 오류·재시도·상태 의미, 기존 API 이전 전략을 확정한다.
- [x] 현행 `reliability-agentic-review` Spec의 **no tools / 고정 3단계 / `null_spike` 한정**을 baseline으로 고정한다. 신규 Agent entry point와 별도 계약을 우선 검토하고, 구 경로 변경·제거는 OpenSpec 전환 및 소비자 검증으로 명시한다.
- [x] [PR #285](https://github.com/mols3131d/hmda-data-reliability/pull/285)의 개발환경/Skill/명령 변경과 실제 수정 파일·실행 명령 의존성을 대조한다. #285를 모든 작업의 전제조건으로 만들지는 않는다.
- [x] 사용자 의도가 불명확한 정책 변경·프레임워크 채택·AI 권한 확대는 임의로 확정하지 않는다.

**Gate:** 생산자–소비자 계약과 금지된 변경이 식별되고 기존 테스트 baseline 및 migration target이 기록되어야 코드 재배치를 시작한다.

### W1 — Deterministic Reliability Refactoring

- [x] Assessment/Remediation의 실제 변경 책임을 따라 소스를 정리하고 내부 import·공개 export·호출 경로를 일관되게 이전한다.
- [x] quality gate, Incident·Evidence·impact, Draft, Recovery의 관찰 가능한 동작과 오류 의미를 보존한다.
- [x] 고정 `triage → rca → plan` LangGraph의 실제 가치와 대체 비용을 검증하고, 불필요하면 결정론적 서비스로 단순화한다. 결과 API는 유지한다.
- [x] Approval의 exact proposal binding, revalidation, 멱등·재시도·부분 실패와 replay 증거를 검증한다.

**Gate:** AI 없이 Reliability lifecycle와 승인 기반 Recovery 경로가 정상 동작하고 관련 기존 회귀 테스트가 통과한다.

### W2 — Reliability AI Contract and Migration

- [x] `review_ai` 기능을 `reliability_ai` 책임으로 이전한다. 단순 rename에 그치지 않고 기존 prompt, provider, evaluation, CLI, provenance, persisted artifact와 import 소비자에 대한 호환 정책을 적용한다.
- [x] Agent Task의 입력 스냅샷·capability 범위·tool budget·상태·결과·불확실성 및 reporting contract를 확정하고 검증한다.
- [x] 기존 결과 데이터·과거 실행 추적을 삭제하거나 새 버전으로 소급 재작성하지 않는다.

**Gate:** 새 도메인의 공개 API와 기존 사용 경로의 이전 전략이 통합 테스트와 Spec에 반영된다.

### W3 — Tool-Using Investigation Agent

- [x] 임의 SQL이나 원시 DB 쓰기가 아닌 **유효성 검증된 bounded read-only** Evidence/lineage/profile 조회 도구를 제공한다. MCP는 실제 필요에 따라 adapter 또는 server를 선택한다.
- [x] Agent가 도구를 선택·호출하고, 실제 결과에 따라 추가 확인/정지/보고 경로를 선택하는 동적 루프를 구현한다. 단일 에이전트로 시작하며 모델 한계에서 안전하게 실패한다.
- [x] 도구 호출 상한, 컨텍스트·토큰·시간 예산, 잘못된 tool arguments, injection, 빈 응답, 중단·취소, provider 실패, 순환 탐색을 제한한다.
- [x] Evidence provenance, 도구 실행 결과, 확인되지 않은 주장과 추가 확인 필요성을 별도로 보존한다.

**Gate:** 실제 도구 결과에 근거하여 다음 조회·가설 검토·중단·보고를 선택하는 경로와 제한·실패 경로가 재현 가능해야 한다. **불필요한 호출 횟수를 맞추기 위한 강제 도구 호출은 금지**한다. 단순 프롬프트 출력이나 mock-only 결과는 충분하지 않다.

### W4 — Delegated Execution and Reporting

- [x] 권한 검증된 위임 Task의 생성·진행·중단·결과 처리 및 실패 원인을 구현한다. 작업 결과를 인간 또는 상위 모델이 이용할 수 있는 구조화 보고/요약으로 전달한다.
- [x] 도구·계약별 side-effect 위험을 판정하고 실제 mutation은 별도의 authoritative Recovery API와 외부 승인을 필요로 하게 한다.
- [x] 완료·부분 완료·실패·재시도·취소를 구분하고 작업/도구 호출 근거를 남긴다.
- [x] 협업형 복수 에이전트는 단일 Agent보다 실질적 성능·비용 개선이 입증될 때만 같은 목표 범위 안에서 선택적으로 채택한다. 임의 fan-out 금지.

**Gate:** 허용된 위임 작업이 실제로 실행되고 결과와 불확실성을 보고한다. 무승인 상태 변경 경로는 차단된다. 사용자가 요구한 실제 쓰기 권한 도입은 별도 승인 없이는 미완료 범위로 보고한다.

### W5 — Evaluation and Integrated Validation

- [ ] Langfuse `4.15.6`의 Native Prompt·Tracing·Dataset·Experiment를 가능한 범위에서 직접 사용하고 중복 자체 구현을 줄인다. 기존 이름·버전·실행 provenance를 보존하며 **원격 `setup`은 Dataset 항목/Prompt 버전의 부작용을 확인하기 전 재실행하지 않는다**.
- [ ] 같은 사례·증거·모델·평가 규칙으로 A(기존 고정 review), B(단일 tool agent), C(Skills), D(필요 시 협업)를 **실제로 실행한 후보만** 비교한다. 기존 completed 실행은 품질 합격으로 해석하지 않는다.
- [ ] RTX 3070 8GB + Qwen3.5 4B의 수용된 **16K 우선·32K 조건부 시험**을 반영한다. `num_ctx`와 출력 상한을 구분하고 Thinking ON/OFF·프롬프트·모델 변수를 동시에 바꾸지 않는다. VRAM, GPU/CPU offload, timeout, tool-call 성공, 지연/토큰을 기록한다.
- [ ] 사람 평가에서 근거 정확성, 결함/누락의 새로운 발견, 오해·환각, 실행 결과 및 보고의 유용성을 평가한다. Langfuse Score/Annotation과 GitHub 승인·Recovery 승인은 구별한다.
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

**외부 병렬 작업:** [PR #285](https://github.com/mols3131d/hmda-data-reliability/pull/285)는 Skill·부트스트랩·스크립트/태스크 명령을 소유한다. #284는 필요한 런타임/테스트 접점만 소비하고, 양 PR의 공유 `scripts/`·`pyproject.toml`·환경 문서·라우팅 파일 수정은 실제 범위를 대조하여 소유자를 정한다. #285 병합 여부와 무관하게 #284의 회귀 검증은 최신 base/head로 다시 한다. 잠금·생성 산출물은 담당 도구로만 갱신한다.

하나의 **PR #284가 전체 목표 결과물을 소유**한다. 여러 작업 agent가 병렬로 구현하더라도 동일한 PR head에 무제한 동시 쓰기를 허용하지 않는다. 각 작업의 owning branch·계약·통합 검증 지점을 분명히 하고, 공유 API·Spec의 변경은 단일 소유자가 조정한다.

## PR Completion Criteria

모든 조건이 충족되어야 **리팩터링 완료**다.

- [x] 결정론적 Reliability의 새 논리 책임·공개 접점·소스 구조가 구현되어 기존 탐지·근거·복구 불변식이 유지된다.
- [x] `review_ai`의 `reliability_ai` 전환과 기존 API·CLI·테스트·provenance 마이그레이션이 완료된다.
- [x] Investigation Agent가 실제 허용 도구를 호출하고 필요에 따른 추가 근거 탐색·정지·오류 처리 동작을 입증한다. Evidence snapshot과 후속 live 조회의 identity를 혼동하지 않는다.
- [x] Execution이 명시적으로 위임·허용된 작업을 실행·중단·실패 처리하고 인간/상위 모델 대상 근거 보고를 생성한다.
- [x] 권한 없는 실행·도구 오용·stale approval·중복 요청·실패 시 무단 DB 변경이 발생하지 않음을 검증한다.
- [ ] Prompt/experiment/trace·human value 평가가 기존 baseline과 비교되고 기록이 보존된다.
- [ ] 관련 OpenSpec 및 도메인 정본 문서, 테스트, 예시 실행 절차가 현재 구현과 일치한다.
- [ ] 최신 base/head 기준 CI·회귀·통합·실행 증거 및 blocking review가 정리되어 merge readiness를 별도로 평가할 수 있다.
- [ ] multi-agent 개발 패턴의 독립 변경, 공유 계약 소유와 통합 정확성을 실제 변경 결과로 검토했다.

**다만** Ready/merge 전환은 별도 인간 검토에 따른다. 구현이 미완료일 때는 문서 준비가 끝났더라도 PR 완료를 주장하지 않는다.

## References

- [Research for this PR](00-research-reliability-agentic-boundary-audit.md)
- [Notion Assessment](https://app.notion.com/p/40f13d7e58b9810bae96f9ea42d80d80) · [User Pattern](https://github.com/mols3131d/mols-agent-assets/blob/main/catalog/patterns/software-engineering/multi-agent-development-architecture.md)
- [Vision](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/VISION.md) · [MVP](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/mvp.md) · [Domain Map](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/domains/OVERVIEW.md)
