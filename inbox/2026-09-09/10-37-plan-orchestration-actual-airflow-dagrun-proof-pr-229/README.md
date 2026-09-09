---
type: plan
title: "Actual Airflow DAGRun Proof Work Plan (PR #229)"
description: "OpenSpec planning 전에 actual Airflow DAGRun proof의 repository evidence, isolation feasibility와 runtime unknown을 정리하고 검증을 관리하는 작업 번들 (PR #229)."
tags:
  - orchestration
  - airflow
  - runtime-proof
  - mvp
  - pr-229
---

# Actual Airflow DAGRun Proof Work Plan (PR #229)

> [!NOTE]
> 본 번들은 GitHub Pull Request [#229](https://github.com/mols3131d/hmda-data-reliability/pull/229) (`test/actual-airflow-dagrun-proof`)에서 진행되는 실제 Airflow DAGRun 동작 증명(Proof)의 사전 조사, 런타임 격리 검증, 태스크 추적 및 OpenSpec 연계를 관리하는 작업 공간입니다.
> 이 문서는 OpenSpec artifact를 미리 작성하는 계획서가 아니며, Requirement, observable scenario, technical delta, implementation task와 acceptance는 OpenSpec으로 진입한 뒤 OpenSpec이 소유합니다.

## Navigation

- [01-research-orchestration-actual-airflow-dagrun-planning.md](01-research-orchestration-actual-airflow-dagrun-planning.md): 실제 DAGRun 검증 사전 조사 보고서
- [tasks.md](tasks.md): 단계별 사전 정찰 및 계획 태스크 체크리스트

## Context

이 branch는 실제 Apache Airflow runtime에서 `hmda_data_plane`의 DAGRun-level behavior를 검증하기 위한 작업을 준비한다. 현재 planning source는 Notion의 `Actual Airflow DAGRun Proof Plan`이며, repository 기준점은 `main@f098190b75df5ae359ab6fc2bb4646cbcddde8bd`다.

사전 준비의 목적은 이미 존재하는 orchestration contract를 Inbox에서 다시 정의하는 것이 아니다. Local agent가 OpenSpec planning을 시작하기 전에 현재 repository가 무엇을 이미 증명하고 무엇을 아직 증명하지 못했는지, actual runtime proof를 안전하게 수행할 수 있는지, 그리고 이 작업이 behavior change인지 proof/tooling change인지 판단할 수 있게 만드는 것이 목적이다.

주요 source는 다음과 같다.

- [openspec/specs/orchestration-pipeline/spec.md](../../../openspec/specs/orchestration-pipeline/spec.md) — 현재 canonical orchestration behavior.
- [src/hmda_reliability/orchestration/dags/hmda_data_plane.py](../../../src/hmda_reliability/orchestration/dags/hmda_data_plane.py) — active Airflow DAG/runtime surface.
- [tests/orchestration/test_airflow_dag.py](../../../tests/orchestration/test_airflow_dag.py)와 [tests/orchestration/test_airflow_execution.py](../../../tests/orchestration/test_airflow_execution.py) — 현재 automated verification boundary.
- [inbox/2026-09-04/07-12-guide-orchestration-sandbox-dag-testing.md](../../2026-09-04/07-12-guide-orchestration-sandbox-dag-testing.md) — 기존 sandbox 실행 경험과 한계.
- [openspec/schemas/spec-driven-tdd/README.md](../../../openspec/schemas/spec-driven-tdd/README.md) — OpenSpec artifact ownership과 planning dependency.

## Planning Boundary

| Surface | Owner in this preparation |
| --- | --- |
| 현재 repository가 제공하는 evidence와 gap | Inbox research |
| Actual runtime proof의 feasibility, isolation risk, alternative와 unresolved question | Inbox research |
| OpenSpec에 들어갈지, spec-level behavior change가 필요한지에 대한 사전 판단 근거 | Inbox research / this preparation plan |
| Change의 why와 scope | OpenSpec Proposal |
| Observable behavior와 scenario | OpenSpec Specs |
| Non-obvious technical delta | OpenSpec Design |
| Verifiable implementation outcomes | OpenSpec Tasks |
| Runtime helper, test, production code와 canonical docs 변경 | Apply / implementation |

Inbox artifact는 이후 OpenSpec artifact의 입력 자료일 뿐 competing source of truth가 아니다. OpenSpec이 생성된 뒤에는 requirement, design과 implementation sequencing을 Inbox에서 병렬로 유지하지 않는다.

## Preparation Questions

사전 조사에서는 다음 질문에 답할 수 있어야 한다.

1. 현재 automated test가 실제 Airflow scheduler-created DAGRun과 TaskInstance lifecycle 중 어디까지 증명하지 못하는가?
1. Actual runtime proof가 기존 개발 state를 오염시키지 않으려면 어떤 runtime/data/artifact surface를 격리해야 하는가?
1. 현재 Airflow CLI/runtime surface만으로 필요한 runtime evidence를 얻을 수 있는가, 아니면 repeatability 또는 evidence retrieval을 위한 별도 helper가 필요한가?
1. Task state, Asset event, DuckDB state와 dbt artifact를 실제 runtime에서 재현 가능하게 확인할 수 있는가?
1. 현재 작업은 기존 behavior를 증명하는 proof/tooling change로 끝나는가, 아니면 actual runtime에서 canonical contract와의 불일치가 발견되어 spec-level delta가 필요한가?

이 질문의 답을 Inbox에서 requirement나 implementation task로 변환하지 않는다. 답은 OpenSpec planning의 입력이 된다.

## Research Focus

### Current Verification Boundary

현재 DAG object inspection과 task function test가 검증하는 범위, 그리고 scheduler/runtime layer에서만 확인 가능한 gap을 분리한다. 이미 검증된 contract를 actual-runtime 작업에서 중복 테스트 대상으로 확대하지 않는다.

### Isolation Feasibility

Airflow metadata/runtime, DuckDB, input fixture, repository-relative dbt artifact와 working tree가 서로 독립적으로 격리 가능한지 조사한다. 기존 sandbox guide가 실제 analytics run의 artifact surface까지 안전하게 분리하는지 재검토한다.

### Runtime And Evidence Access

Airflow 3.3.0의 repository-native CLI/runtime로 actual DAGRun 생성, terminal state 확인, TaskInstance state와 Asset event 조회가 가능한지 확인한다. 별도 helper는 기존 surface만으로 reproducible proof를 만들기 어렵다는 근거가 있을 때만 OpenSpec planning 후보가 된다.

### Change Classification

실행 전에는 production behavior change를 전제하지 않는다. Local reconnaissance에서 현재 contract와 실제 runtime이 일치하면 proof/tooling/documentation 성격으로 분류하고, contract violation이 확인되면 그때 behavior delta 필요성을 OpenSpec에 넘긴다.

## Decision Gates

- **Existing runtime surface is sufficient:** 별도 production capability를 가정하지 않고 OpenSpec planning에 현재 evidence와 재현 경로를 전달한다.
- **A repeatability/evidence helper is necessary:** helper가 해결해야 하는 operational gap만 OpenSpec Design/Tasks 후보로 넘기고 requirement를 Inbox에서 만들지 않는다.
- **Canonical behavior is violated:** ad-hoc patch를 시작하지 않고 observed mismatch를 evidence로 남긴 뒤 OpenSpec이 behavior delta를 소유하게 한다.
- **Safe isolation is not feasible:** test-only production override를 즉석에서 추가하지 않고 blocker와 근거를 OpenSpec planning input으로 남긴다.

## Preparation Outputs

이 branch의 OpenSpec 이전 초기 artifact는 다음으로 제한한다.

- 이 preparation plan — 사전 조사 목적, boundary와 decision gate.
- `research` artifact — current repository evidence, runtime gap, isolation feasibility, option과 open question의 synthesized result.

Scenario checklist, acceptance matrix, implementation task list, technical design 초안과 proof report skeleton은 초기 Inbox artifact로 만들지 않는다. 필요하면 OpenSpec 또는 실제 execution 결과를 소유하는 후속 artifact가 담당한다.

## Exit

사전 준비는 local agent가 다음을 추측하지 않고 판단할 수 있을 때 충분하다.

- 무엇이 현재 evidence로 이미 증명되었는가.
- Actual Airflow runtime에서 무엇이 아직 unknown인가.
- 어떤 isolation risk가 먼저 확인되어야 하는가.
- 기존 runtime surface만으로 proof가 가능한지 어떤 local reconnaissance가 필요한가.
- 조사 결과에 따라 OpenSpec이 spec-free change로 진행할지 behavior delta를 다룰지 어떤 기준으로 결정할 것인가.

이 지점부터 normative planning은 OpenSpec workflow가 소유한다.
