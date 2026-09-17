---
type: report
title: "MVP Implementation Gap Handoff"
description: "Handoff for auditing MVP implementation completeness before PR #239 can be treated as final acceptance."
tags:
  - mvp
  - handoff
  - review
---

# MVP Implementation Gap Handoff

## Purpose

PR #239는 기존 구현을 하나의 revision에서 증명하는 acceptance PR로 준비됐지만, 현재 핵심 질문은 **proof가 통과했는가가 아니라 `docs/mvp.md`가 요구하는 MVP 구현 자체에 누락이 없는가**다. 다음 작업자는 PR body의 PASS 판정을 출발점으로만 사용하고, MVP contract에서 구현과 검증 evidence까지 다시 역추적해야 한다.

이 문서는 새 requirement를 만들지 않는다. 현재 MVP contract와 PR #239를 대상으로 implementation gap audit를 이어가기 위한 handoff다.

## Current State

- PR #239는 Draft이며, 이 handoff 작성 직전 head는 `8cbb80b66e37694124a50fb4c58906cac149b4e1`이었다.
- PR body는 해당 exact revision에서 여섯 MVP acceptance가 모두 PASS라고 기록한다.
- #239의 executable diff는 사실상 CI classifier test fixture 격리뿐이며, 나머지는 Inbox/OpenSpec proof preparation 문서다. 따라서 #239 자체가 MVP 기능을 구현한 PR은 아니다.
- `main`에는 실제 Airflow DAGRun integration test, deterministic system recovery E2E, Review AI invocation evidence와 live provider proof entrypoint 등 MVP 핵심 구현 표면이 존재한다.
- 현재까지 확인한 범위는 `implementation-complete candidate`를 지지하지만, requirement-by-requirement implementation audit를 끝낸 상태는 아니다.
- 기존 raw proof bundle은 `.local/pr239/proofs/8cbb80b66e37694124a50fb4c58906cac149b4e1/`에 local-only로 보존돼 있다.

이 파일을 commit하면 PR head가 위 proof SHA에서 이동한다. 따라서 `8cbb80b...`의 PASS는 그 revision의 evidence로만 취급하고, 현재 HEAD를 최종 acceptance로 선언하려면 모든 필요한 변경이 끝난 뒤 current revision에서 다시 증명해야 한다.

## Audit Boundary

Primary contract는 `docs/mvp.md`의 **Domain Completion Gates**와 **MVP Acceptance**다. 다음 원칙을 유지한다.

- PR body, archived OpenSpec task, 전체 테스트 PASS만으로 implementation complete를 추론하지 않는다.
- 테스트가 존재하는지보다 요구 동작이 production code에 실제로 구현되어 있고 독립적인 oracle로 검증되는지를 본다.
- Data Lake, Airflow, Reliability, Review AI가 하나의 전역 fixture를 공유해야 한다고 요구하지 않는다. Exact identity binding은 contract가 요구하는 경계에서만 강제한다.
- Airflow data plane은 Reliability control plane과 암묵적으로 결합하지 않는다.
- Agentic review는 advisory이며 approval/recovery authority를 획득하지 않는다.
- Human approval은 exact validated recovery proposal에 결합되어야 한다.
- 실제 gap이 없으면 구현량을 만들기 위해 새 capability를 추가하지 않는다.
- 새 architecture, dependency, 권한 확대 또는 MVP scope 확장이 필요한 gap은 임의로 구현하지 말고 별도 판단 대상으로 보고한다.

## Required Audit

다음 항목을 `Implemented / Proven / Gap / Not Verified`로 판정하고, 각 판정에 owning source와 가장 직접적인 evidence를 연결한다.

| Area | Required question |
| --- | --- |
| HMDA Data | 같은 source와 representative case에서 Source → Bronze state와 synthetic incident input을 재현할 수 있는가? |
| Data Platform | Bronze → staging → mart가 실제 dbt 실행으로 닫히고 채택된 artifact와 lineage evidence를 추적할 수 있는가? |
| Data Operations | ingestion, quality gate, dbt, reliability execution과 candidate/current adoption boundary 및 failure evidence가 명확한가? |
| Reliability | deterministic incident → validated proposal → proposal-bound approval → recovery → 같은 기준의 re-validation이 실제 state transition으로 닫히는가? |
| Review AI | incident evidence와 `RemediationDraft`를 bounded structured review로 변환하고 deterministic validation과 durable provenance를 남기는가? |
| Runtime AI | provider-neutral settings, bounded invocation, retry/error semantics와 observable invocation contract가 Review semantics와 분리되어 있는가? |
| Orchestration | 실제 Airflow DAGRun이 raw → quality gate → dbt 순서와 주요 failure path를 framework 경계에서 증명하는가? |
| Safety | Agentic output이나 LLM availability가 deterministic guardrail, approval gate 또는 mutation authority를 우회하거나 변경할 수 없는가? |
| Reproducibility | 정상, incident, recovery, 주요 failure/retry 결과를 같은 revision에서 다시 설명할 수 있고 live invocation provenance를 보존할 수 있는가? |

우선 확인할 evidence entrypoint는 다음과 같다.

- `docs/mvp.md`
- `docs/ARCHITECTURE.md`
- `openspec/specs/**`
- `tests/data_operations/test_system_recovery_e2e.py`
- `tests/orchestration/test_airflow_dagrun.py`
- `scripts/run_agentic_review_live.py`
- `src/hmda_reliability/{hmda_data,data_platform,data_operations,reliability,review_ai,runtime_ai,orchestration}/`
- `inbox/github-239-prove-current-revision-mvp-e2e/01-checklist-current-revision-mvp-e2e-proof.md`
- `inbox/github-239-prove-current-revision-mvp-e2e/03-plan-project-mvp-proof-execution.md`

## Decision Rule

Gap은 **MVP contract가 요구하는 observable behavior가 production implementation에 없거나, 존재한다고 주장하지만 그 동작을 신뢰할 independent evidence가 없는 경우**에만 만든다. 단순히 코드가 분산돼 있거나 #239 diff에 구현 코드가 없다는 이유는 gap이 아니다.

반대로 test fixture나 proof script가 production behavior를 대신해 MVP가 있는 것처럼 보이게 하는 경우는 gap이다. 특히 mock, synthetic-only path, manual evidence assembly가 실제 owning implementation을 우회하는지 확인한다.

## Required Output

다음 작업자는 먼저 audit 결과를 남긴다.

1. MVP requirement별 status, owning source, test/runtime evidence, 남은 uncertainty를 한 표로 정리한다.
1. `Gap`마다 빠진 **동작**을 구체적으로 설명하고 단순 test/documentation 부족과 구분한다.
1. 실제 gap이 없으면 `implementation complete candidate`라고 결론 내리고 current HEAD에서 final acceptance rerun이 필요하다고 명시한다.
1. 실제 gap이 있으면 MVP 완료 판정을 중단하고 최소 coherent remediation을 제안한다. 구현은 해당 invocation에 별도 권한이 있을 때만 진행한다.
1. 모든 수정이 끝난 뒤에만 하나의 clean current revision에서 여섯 acceptance를 다시 실행해 최종 완료 여부를 판단한다.

## Completion

이 handoff의 목적은 다음 둘 중 하나가 evidence로 확정되면 달성된다.

- **No implementation gap** — MVP contract의 각 요구가 production implementation과 직접 evidence에 연결되고, 남은 일은 current-revision final acceptance뿐이다.
- **Confirmed implementation gap** — 빠진 동작, owning boundary, 최소 remediation과 검증 방법이 특정되어 MVP 완료 선언을 보류할 근거가 생겼다.

그 전에는 PR #239를 MVP 종료 증거로 취급하지 않는다.
