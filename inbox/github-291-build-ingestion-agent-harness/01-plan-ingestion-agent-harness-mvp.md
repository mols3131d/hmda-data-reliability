---
type: plan
title: "Ingestion Agent Harness MVP Implementation Plan"
description: "LangGraph 또는 Deep Agents 기반 데이터 흡수 에이전트의 범위, 설계 단계, 구현 목표와 수용 기준을 정한다."
---

# Ingestion Agent Harness MVP Implementation Plan

## Goal

**이 PR의 병합 목표는 LangChain 생태계의 LangGraph 또는 Deep Agents를 활용해 데이터 흡수 단계에서 에이전트가 수행하는 실제 작업의 LLMOps harness를 설계·구현·검증하는 것이다.** LLM 응답 품질 평가나 평가 플랫폼 고도화는 목표가 아니다. 에이전트가 원천 근거에 따라 조사 도구와 다음 작업을 선택·계획하고, 명시된 권한 경계 안에서 기존 ingestion의 실행/결과와 연결되도록 한다. 기존 HMDA ingestion과 Airflow는 대체하지 않는다.

## MVP Slice

아래는 검토할 **첫 vertical slice 후보**이며, 로컬 작업 에이전트가 실제 HMDA ingest 업무의 필요성과 현재 계약을 확인해 최소 coherent workflow를 확정한다. 단순 검증 결과 요약 또는 프레임워크 의존성 추가만으로 MVP 구현을 완료한 것으로 보지 않는다.

1. **Intake and Scope** — `source_root`, `source_year`, optional `source_file`, target을 typed request로 수신한다. Allowed scope, read-only source discovery, 파일 집합과 실행 식별자를 결정론적으로 검증한다.
2. **Evidence and Investigation** — 기존 discovery/validation API와 제한된 read-only tools로 근거를 확인한다. 에이전트는 관찰된 문제에 따라 **추가 점검, 설명, 실행 준비 또는 사람에게 이관** 중 다음 작업을 선택할 수 있어야 한다. 모델이 직접 디스크 경로, SQL 또는 전체 원본을 무제한 탐색하도록 두지 않는다.
3. **Agent Plan** — 근거 참조, 불확실성, 판정 `ready / blocked / needs_human`, 제안 action, 예상 영향 범위가 있는 typed execution plan을 생성한다. LLM은 사실이나 권한의 source of truth가 아니다.
4. **Authority and State Gate** — 에이전트 출력은 실행 권한이 아니다. 실제 mutation이 필요한 경로는 **이미 권한을 가진 trusted caller**의 명시적 실행 요청과 기존 target/partition consistency guard를 통과해야 한다. 고위험 작업만 필요한 사람 승인으로 이관하며 일반 raw-load 전체에 새로운 human approval 조건을 자동 추가하지 않는다.
5. **Controlled Execution or Handoff** — 실제 agent-mediated write가 선택된 경우에만 기존 Data Operations 또는 managed ingestion API로 trusted caller 요청을 위임한다. Model-generated arbitrary command나 direct Bronze mutation은 금지한다. 기존 API에서 필요한 원자적 state guard를 충족할 수 없다면 mutation 경로를 이번 slice에서 빼고, **기존 실행 경로에 근거·계획을 넘기는 read-only integration**으로 구현한다. 비원자적 preflight만으로 안전한 write라 주장하지 않는다.
6. **Outcome and Replay** — 결과/실패/중단을 실행 ID와 실제 domain outcome에 연결한다. 실행된 tool, input/prompt/model revision, step/time budget, trace를 보존한다. Replay는 **agent 판단과 허용된 read-only 도구를 기본**으로 하며 state mutation의 자동 재실행을 의미하지 않는다. 관측 저장소와 checkpoint는 MVP에 필요한 최소만 둔다.

## Architecture Decision

실제 코드 작성 전에 아래 기준으로 하나를 선택하고 근거를 해당 OpenSpec design 또는 계획에 남긴다. **Deep Agents를 harness 후보로 동등하게 검토**하고, 단순 의존성 존재를 채택의 충분 근거로 사용하지 않는다.

| Candidate | Choose When | Cost / Caution |
| --- | --- | --- |
| Existing LangGraph | 유한한 상태·승인·복구 transition과 명확한 deterministic ownership이 핵심 | 직접 agent-loop/tool contract를 제한적으로 구성해야 함 |
| Self-hosted Deep Agents SDK | 계획 분해·상위 subagent 위임·context file management가 첫 slice에 실질적 이점 제공 | 새로운 dependency, 기본 도구 권한·state와 model adapter 경계 검증 필요 |

`langgraph`는 이미 project dependency이고 `deepagents`는 아직 direct dependency가 아니다. 무조건 둘을 함께 끼우지 않는다. 둘을 사용하면 **Deep Agents 상위 계획/도구 orchestration, LangGraph 명시적 safety state**처럼 중복 없는 소유권을 증명해야 한다. 새 SDK/adapter가 필요하면 호환성 검증 후 최소 dependency만 추가하고 lock state를 정상 workflow로 갱신한다.

## Ownership and Compatibility

- `hmda_data`: source discovery / ingestion / provenance의 deterministic source of truth를 유지한다.
- `data_operations`: stage invocation / result를 유지한다. 새 agent workflow를 통해서만 이용할 수 있게 제한하지 않는다.
- `orchestration`: Airflow raw → quality gate → dbt 순서의 **유일한 data-plane owner**다. Agent graph는 별도 bounded control plane이며 full pipeline DAG을 복제하지 않는다.
- `runtime_ai` 및 현행 observability: 기존 provider-neutral invocation / Langfuse 재사용 가능성을 먼저 검토한다. 별도 LangSmith 유료 서비스, model-specific binding, 두 번째 tracing source of truth를 필수로 만들지 않는다.
- 새 package는 기존 domain owner로 책임이 명확히 표현되지 않을 때만 도입한다. Domain boundary와 source/test path guidance에 따른다.

## Delivery Steps

1. **Contract alignment:** 사용자가 지정한 신규 ingestion agent MVP 목표와 `docs/mvp.md`의 기존 review 중심 scope 사이의 차이를 먼저 식별한다. 현재 OpenSpec change/spec을 확인하고 실제 **새 contract가 필요할 때만** 적합한 소유자에 proposal/design/tasks 및 검증된 Spec delta를 반영한다. 기존 ingestion, recovery, orchestration 불변식은 유지하되 사용자 의도를 기존 review 평가로 축소하지 않는다.
2. **Minimal harness design:** 우선 **agent에 위임할 실제 ingest 작업과 판단 지점**을 결정하고, 이를 설명할 수 있는 최소 framework/state/model adapter/tool contract/budget/failure path를 선정한다. 필요한 경우 checkpoint와 permission gate를 도입한다. Deep Agents를 선택하면 built-in planning, subagents, filesystem, shell 도구의 실제 노출 범위를 검증한다.
3. **Implementation:** 결정된 vertical slice에서 실제 agent tool selection 및 계획/후속 작업이 실행되게 하고, 기존 ingestion boundary와 observability를 연결한다. 실행 경로가 허용될 때만 trusted caller의 guarded invocation을 제공한다. 정상·invalid/denied 및 선택된 통합 경로의 stale scenario를 다룬다.
4. **Tests and proof:** fake model과 독립 oracle의 offline tests에서 에이전트가 **서로 다른 입력 증거에 따라 올바른 허용 도구/다음 작업을 선택하는지** 확인한다. 현재 구현한 경계를 대상으로 tool denial, timeout, state/retry/replay를 검사한다. 실제 데이터 mutation을 연결했으면 임시 DuckDB에서 idempotency, stale state, 무단 변경 부재를 증명한다. 승인된 로컬 모델이 있다면 최소 smoke를 실행하고 조건·실패를 기록하되 모델 품질 점수화는 하지 않는다.
5. **Review readiness:** 현재 main/head 결합에서 CI Lite와 변경 영향에 비례한 검사 실행, 구현 근거·남은 경계를 PR에 정리한다.

## Acceptance

- 대표 HMDA source를 대상으로 **실제 agent의 도구 선택·작업 분기 → 근거 있는 계획 또는 조치 → 기존 ingestion 실행 경계와의 명확한 연결 → 재현 가능한 결과/실패 증거**가 존재한다. 반드시 직접 mutation까지 연결해야 한다는 뜻은 아니며, trusted caller에 인계하는 경우도 성공/실패/다음 action이 관찰 가능해야 한다.
- In-scope failure (unsupported/missing source, invalid schema, tool error, 허용 범위 위반, budget 소진)는 fail-closed 또는 명시적 escalation으로 처리된다. Target stale-state와 mutation retry는 실제 쓰기 경로를 구현한 경우에만 완료 gate에 추가한다.
- 기존 Airflow DAG, `load_raw_data`, source-to-Bronze provenance, gate와 dbt 흐름은 회귀하지 않는다. AI 계획/메시지 자체로 Bronze나 current dbt artifact를 변경하지 않는다. 외부 trusted caller가 가진 기존 실행 권한을 새로운 인간 승인 강제 정책으로 바꾸지 않는다.
- Offline pytest/contract test는 외부 모델·네트워크 없이 재현 가능하다. 실제 관측/모델 호출을 수행하지 않았으면 미검증으로 남긴다.
- Canonical MVP/OpenSpec과 user-facing operation guide가 새로운 실제 동작에 부합한다. 기능 미구현 상태에서 "MVP 완료"를 주장하지 않는다.

## Exclusions

- 인간 LLM 품질 rubric, benchmark / Langfuse Dataset eval 고도화
- 범용 autonomy, 무제한 shell/file/SQL 권한, 외부 원천 다운로드
- Airflow를 대신하는 full-pipeline graph / LangSmith managed infrastructure 강제
- Self-modifying policy, agent가 직접 approval 발행, mutation 후 결과를 자기 주장만으로 채택

## References

- [Research](00-research-ingestion-agent-harness-boundary.md)
- [Vision](../../docs/VISION.md), [MVP](../../docs/mvp.md), [Architecture](../../docs/ARCHITECTURE.md)
- [Ingestion Spec](../../openspec/specs/hmda-data-ingestion/spec.md)
- [Orchestration Spec](../../openspec/specs/orchestration-pipeline/spec.md)
