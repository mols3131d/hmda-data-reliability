---
type: plan
title: "Ingestion Agent Harness MVP Implementation Plan"
description: "LangGraph 또는 Deep Agents 기반 데이터 흡수 에이전트의 범위, 설계 단계, 구현 목표와 수용 기준을 정한다."
---

# Ingestion Agent Harness MVP Implementation Plan

## Goal

**이 PR의 병합 목표는 데이터 흡수 단계의 agent harness MVP 설계·구현·검증 완료**다. LLM 응답 품질 평가나 평가 플랫폼 확장이 목표가 아니다. 이미 동작하는 HMDA ingestion과 Airflow를 유지하면서, 하나의 bounded source-intake 작업을 에이전트가 조사하고 계획하며 신뢰할 수 있는 실행 주체가 실제 적재 결과를 검증할 수 있도록 한다.

## MVP Slice

1. **Intake and Scope** — `source_root`, `source_year`, optional `source_file`, target을 typed request로 수신한다. Allowed scope, read-only source discovery, 파일 집합과 실행 식별자를 결정론적으로 검증한다.
2. **Evidence and Investigation** — existing discovery/validation API와 bounded read-only tools를 통해 지원 형식, 누락 입력, 구조 계약, provenance와 예외를 수집한다. 모델이 직접 디스크 경로, SQL 또는 전체 원본을 무제한 탐색하도록 두지 않는다.
3. **Agent Plan** — 근거 참조, 불확실성, 판정 `ready / blocked / needs_human`, 제안 action, 예상 영향 범위가 있는 typed execution plan을 생성한다. LLM은 사실이나 권한의 source of truth가 아니다.
4. **Human/Trusted Caller Gate** — 결정론적 검증 뒤 immutable 실행 범위·source identity·target expected-state와 연계한 승인/의사결정 경계를 둔다. 에이전트 output이 곧 approval이 되지 않는다.
5. **Controlled Execution** — 승인된 요청만 existing Data Operations 또는 managed ingestion API로 위임한다. Target의 stale state, input 변경 또는 권한 불일치는 mutation 전에 원자적으로 방어한다. 기존 API에 atomic guard가 부족하면 해당 계약에서 필요한 최소 보완 또는 실행을 advisory로 제한한다. Preflight의 비원자적 재확인만으로 안전하다고 주장하지 않는다.
6. **Outcome and Replay** — 결과/실패/중단을 실행 ID와 실제 loader outcome에 연결한다. Agent plan, 허용된 tool invocation, input/prompt/model revision, step/time budgets, trace 및 deterministic validation을 추적하고 동일 입력에서 통제된 offline 재실행이 가능하다.

## Architecture Decision

실제 코드 작성 전에 아래 기준으로 하나를 선택하고 간결한 근거를 이 계획이나 대응 OpenSpec design에 남긴다.

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

1. **Contract alignment:** `docs/mvp.md`의 기존 review-only MVP와 신규 ingestion agent scope의 차이를 명시적으로 정합화한다. 영향을 받는 active OpenSpec Change / canonical Spec을 확인해 필요한 requirement/scenario, design, tasks를 OpenSpec workflow로 작성·반영한다. 기존 ingestion과 orchestration 불변식은 유지한다.
2. **Minimal harness design:** 선택한 framework, state schema, model adapter, allowlisted tool contract, budget, checkpoint, approval과 failure path를 정의한다. Deep Agents를 선택하면 built-in tools 권한과 shell/file access 기본값을 검증하고 최소화한다.
3. **Implementation:** 최소 vertical slice의 agent 호출, 계획 산출, 외부 승인 경계, existing ingestion integration, evidence/trace를 구현한다. 정상 입력과 invalid/stale/denied 케이스를 지원한다.
4. **Tests and proof:** fake model / fake external boundary의 offline contract tests로 정상·실패·재진입과 tool authority를 검증한다. 실제 DuckDB 임시 파일을 이용해 승인된 실행, stale guard, idempotency, no-unauthorized-mutation을 확인한다. 로컬 모델/관측 서비스가 있다면 명시적으로 smoke를 수행하고 조건·실패를 기록하되 model 품질 점수화는 하지 않는다.
5. **Review readiness:** 현재 main/head 결합에서 CI Lite와 변경 영향에 비례한 검사 실행, 구현 근거·남은 경계를 PR에 정리한다.

## Acceptance

- 대표 HMDA source 1종에서 **intake → bounded tool evidence → agent plan → explicit external decision → guarded ingestion result → reproducible evidence**의 연결된 실행 근거가 존재한다.
- Unsupported/missing source, invalid schema, tool error, step/time budget exhaustion, unauthorized request, stale input/target와 retry가 fail-closed 또는 명시적 escalation으로 처리된다.
- 기존 Airflow DAG, `load_raw_data`, source-to-Bronze provenance, gate와 dbt 흐름은 회귀하지 않는다. 승인이 없는 agent action은 Bronze와 current dbt artifact를 변경하지 않는다.
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
