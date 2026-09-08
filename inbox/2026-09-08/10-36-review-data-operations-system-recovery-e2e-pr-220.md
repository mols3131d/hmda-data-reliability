---
type: review
title: PR #220 System Recovery E2E Review
description: PR #220의 결정론적 시스템 복구 E2E와 사전 승인 안전 테스트를 repository contract와 false-green 관점에서 검토한 결과다.
status: "completed"
tags:
  - data-operations
  - testing
  - reliability
---

# PR #220 System Recovery E2E Review

> [!NOTE]
> **Revise.** 현재 production recovery 구현에서 즉시 확인된 correctness defect는 없지만, PR 자체에 범위를 벗어난 Rulesync/tooling 변경이 섞여 있고 replay 무변이와 approval-before-source-processing이라는 핵심 safety contract를 E2E oracle이 독립적으로 증명하지 못한다. 이 세 항목을 정리한 뒤 다시 검토하는 것이 적절하다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| PR #220 `test(data_operations): 결정론적 시스템 복구 E2E 및 사전 승인 안전 케이스 추가` | base `ab90cb3ae9d94420046cc103da86517c3f989eb1`, reviewed head `204183f482d709dcc88ed4156b691fdebd6fa493` | PR diff, recovery/backfill contract, test scenario·oracle, observed CI evidence | Revise |

검토 기준은 `tests/AGENTS.md`, `docs/development/test-design.md`, `docs/ARCHITECTURE.md`, `docs/mvp.md`, `openspec/specs/reliability-recovery-backfill/spec.md`와 PR의 명시적 scope다. 테스트가 현재 구현을 통과하는지보다, contract 위반을 실제로 검출할 수 있는지를 우선했다.

## Findings

### F1. Unrelated Rulesync and lockfile changes are mixed into the test PR

- **Severity** - Major
- **Location** - commit `0728c1d48cac85aa779c05ab164bc5ca4ea95575`; `.agents/route/skills.jsonl`, `docs/INDEX.tsv`, `docs/development/INDEX.tsv`, `rulesync.jsonc`, `rulesync.lock`, `uv.lock`
- **Evidence** - PR의 목적과 설명은 system recovery E2E 및 safety test 추가로 한정되어 있지만, 별도 commit `chore(rulesync): 외부 agent skill 추가 및 lockfile 동기화`가 외부 agent skill 목록, route, docs index와 lockfile을 함께 변경한다. `tests/AGENTS.md`는 test 작업의 authored write boundary를 test·fixture·대응 design 문서로 제한하고 project configuration과 dependency 변경을 금지한다.
- **Impact** - 테스트 증명과 무관한 agent/tooling 상태가 같은 PR에서 함께 채택되어 review surface와 merge effect가 불필요하게 넓어진다. 특히 테스트 결과와 무관한 Rulesync/lock 변경까지 승인해야 하므로 PR의 재현성과 책임 경계가 흐려진다.
- **Required Change** - history rewrite 없이 정상 commit으로 위 6개 파일을 base 상태로 복원해 #220의 functional change set에서 제거한다. 해당 tooling 변경이 필요하면 별도 branch/PR에서 다룬다. 이 review artifact는 branch-owned non-canonical working artifact로 유지할 수 있다.

### F2. S7 does not independently prove that replay skipped partition overwrite

- **Severity** - Major
- **Location** - `tests/data_operations/test_system_recovery_e2e.py#test_deterministic_system_recovery_e2e`, S7 Replay Reconciliation
- **Evidence** - S7은 두 번째 `execute_approved_backfill()` 호출 뒤 `mutation_state == "already_recovered"`, `validation_passed`, logical content identity와 row count만 확인한다. 그러나 `PartitionContentIdentity`는 재적재 시각 차이를 stale state로 취급하지 않기 위해 `ingested_at`을 digest에서 명시적으로 제외한다. 따라서 구현이 동일 logical rows를 불필요하게 `DELETE`/`INSERT`로 다시 교체한 뒤 `already_recovered`를 반환하는 회귀가 생겨도 현재 assertion은 모두 통과할 수 있다. 반면 governing recovery spec은 expected recovered state에서 partition overwrite를 반복하지 않고 verification만 재개하도록 요구한다.
- **Impact** - PR이 핵심 E2E proof로 제시하는 replay idempotency가 실제 no-mutation contract가 아니라 최종 logical content equality만 증명한다. redundant write 회귀가 false green으로 남을 수 있다.
- **Required Change** - replay 직전과 직후의 target에서 implementation 반환값과 독립적인 mutation-sensitive evidence를 비교한다. 예를 들어 deterministic fixture와 `partition_max_ingested_at` 또는 동등한 Bronze provenance를 사용해 target provenance가 정확히 보존됐음을 검증한다. 핵심은 `mutation_state` 문자열을 다시 믿는 것이 아니라 실제 partition overwrite가 없었음을 외부 상태로 증명하는 것이다.

### F3. Rejected and incomplete approval tests do not prove blocking before source processing

- **Severity** - Major
- **Location** - `tests/data_operations/test_system_recovery_e2e.py#test_pre_approval_safety_rejected_approval_zero_mutation`, `#test_pre_approval_safety_mismatched_actions_zero_mutation`
- **Evidence** - recovery spec의 Missing/Incomplete approval scenario는 source 처리와 target mutation 전에 차단하도록 요구한다. 현재 두 테스트는 모두 정상적으로 읽을 수 있는 `clean_csv`를 recovery source로 넘기고 `ApprovalGateError`와 target identity/null-rate 무변이만 확인한다. 따라서 구현 순서가 잘못되어 source를 먼저 읽고 staging한 뒤 approval을 거부하더라도 source 처리가 성공하는 한 테스트는 그대로 통과한다. 현재 `execute_approved_backfill()` 구현은 `_ensure_approved()`를 source staging보다 먼저 호출하므로 production path는 contract와 일치하지만, 새 E2E가 그 순서를 보호하지는 못한다.
- **Impact** - 승인 거부가 target mutation만 막고 unapproved source I/O는 허용하는 회귀를 safety proof가 검출하지 못한다. PR이 명시한 "사전 차단"의 증거가 불완전하다.
- **Required Change** - approval 자체만으로 source 접근 전에 거부되어야 하는 rejected/missing-action case에는 존재하지 않거나 읽을 수 없는 valid-extension source path를 사용하고, source-processing error보다 approval-specific `ApprovalGateError`가 먼저 발생함을 검증한다. target 무변이 assertion은 그대로 유지한다. Target-state mismatch case는 target freshness/reconciliation 단계의 별도 contract이므로 같은 source-before-gate oracle을 기계적으로 적용하지 않는다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| PR live state and diff scope | PR #220 reviewed head `204183f482d709dcc88ed4156b691fdebd6fa493`, 3 commits, 8 changed files | Pass |
| Scope provenance | commit `0728c1d48cac85aa779c05ab164bc5ca4ea95575`가 Rulesync/tooling/lock 변경을 별도 commit으로 추가 | Fail |
| Replay oracle review | S7 assertions와 `PartitionContentIdentity`의 volatile-column exclusion, recovery reconciliation spec 비교 | Fail |
| Approval ordering oracle review | rejected/missing-action tests와 approval gate spec, current executor ordering 비교 | Fail |
| Current CI | GitHub Actions `CI Lite` run 779 (`34176105865`)가 reviewed head에서 success; selected tests 포함 | Pass |
| PR description validation claims | focused E2E 5 pass, data_operations 55 pass 등은 PR body에 기록되어 있으나 이 invocation에서 재실행하지 않음 | Not Verified |
| Independent dual-perspective orchestration | 이 invocation에서는 별도 review subagent 실행 surface를 사용할 수 없어 direct review만 수행함. PR body의 기존 `review-lead: clear` 주장은 독립적으로 재검증하지 않음 | Not Verified |

## Remaining Risks

- 이 review는 #220의 명시적 test/E2E scope와 직접 연결된 contract만 검토했다. Human E2E, Agent E2E, live LLM/provider, Airflow control-plane 확장은 PR이 명시적으로 제외한 범위이므로 finding으로 만들지 않았다.
- Current production executor는 확인한 세 safety path에서 contract에 맞게 동작하도록 구현되어 있다. F2와 F3는 production defect 판정이 아니라, 향후 회귀를 놓칠 수 있는 E2E evidence gap이다.
- CI success는 현재 코드의 실행 가능성 evidence로 사용했으며 finding 부재의 증거로 해석하지 않았다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | unrelated tooling scope를 분리하고 replay no-write 및 approval-before-source-processing oracle을 보강해야 #220이 주장하는 deterministic safety proof를 신뢰할 수 있다. | PR #220 head branch `agent/test/system-recovery-e2e` |
