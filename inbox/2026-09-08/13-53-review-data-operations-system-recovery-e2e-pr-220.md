---
type: review
title: PR #220 System Recovery E2E Independent Review
description: PR #220의 결정론적 시스템 복구 E2E 및 사전 승인 안전 케이스에 대해 review-lead가 품질 및 적대적 분석을 통합 검토한 독립 리뷰 결과다.
status: completed
tags:
  - data-operations
  - testing
  - reliability
  - review-lead
  - pr-220
---

# PR #220 System Recovery E2E Independent Review

> [!IMPORTANT]
> **Verdict: Revise (Changes Required).** review-lead를 통한 품질(Quality) 및 적대적(Adversarial) 교차 분석 결과, PR #220은 프로덕션 복구 코드 자체의 즉각적인 결함은 없으나, (1) 테스트 PR 범위 외 Rulesync 및 의존성 lockfile 변경 혼입, (2) S7 Replay 및 Zero-mutation 오라클의 독립 증명 결여(False Green 갭), (3) 사전 승인 안전 케이스의 소스 I/O 선행 차단 미검증, (4) Airflow 런타임 경계 대비 E2E 명칭 및 계약 불일치 등 4건의 필수 수정 사항(changes_required)이 확인되었습니다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| PR #220 `test(data_operations): 결정론적 시스템 복구 E2E 및 사전 승인 안전 케이스 추가` | Base `ab90cb3ae9d94420046cc103da86517c3f989eb1`, Head `519d49b14831ed9b1e1d14eab362dd9fc082b53b` | PR 전체 diff, 복구/백필 규약, E2E 시나리오 및 오라클, 의존성 변경 영향 | Revise (Changes Required) |

본 검토는 `review-lead` 주관 하에 `review-quality`와 `review-adversarial` 전문 에이전트의 독립 분석을 위임·종합하여 수행되었습니다. 단순히 테스트가 통과하는지 여부를 넘어, 구현체의 규약 위반을 오라클이 실제로 잡아낼 수 있는지(False Green 방지)와 PR의 변경 경계 적합성을 중점적으로 검증했습니다.

## Findings

### F1. Unrelated Rulesync and Lockfile Changes Mixed into Test PR

- **Severity** - Major
- **Disposition** - `current_required` (`explicit_target`)
- **Location** - 커밋 `0728c1d48cac85aa779c05ab164bc5ca4ea95575`; [rulesync.jsonc](../../rulesync.jsonc), [rulesync.lock](../../rulesync.lock), [uv.lock](../../uv.lock), [.agents/route/skills.jsonl](../../.agents/route/skills.jsonl), [docs/INDEX.tsv](../../docs/INDEX.tsv), [docs/development/INDEX.tsv](../../docs/development/INDEX.tsv)
- **Evidence** - PR의 목적은 시스템 복구 E2E 및 안전 케이스 추가이지만, 별도 커밋 `chore(rulesync): 외부 agent skill 추가 및 lockfile 동기화`를 통해 외부 스킬 정의와 2,491라인 규모의 [uv.lock](../../uv.lock) 변경(`alembic`, `anyio` 등의 패키지 버전 변경 포함)이 PR에 포함되었습니다. 이는 [tests/AGENTS.md](../../tests/AGENTS.md)의 Authored Write Boundary(테스트 코드, fixture, 대응 design 문서 외 프로젝트 설정 및 의존성 수정 금지)를 위반합니다.
- **Impact** - 테스트 PR의 검증 출처(provenance)가 오염되며, 향후 병합 시 의도치 않은 서드파티 패키지 판올림과 에이전트 라우팅 상태 드리프트를 유발합니다.
- **Required Change** - 강제 푸시(force push) 없이 정상 후속 커밋을 통해 해당 6개 파일을 베이스 커밋(`ab90cb3ae9d94420046cc103da86517c3f989eb1`) 상태로 원복하여 PR 변경 집합에서 제외합니다.

### F2. Missing Independent Proof in Replay and Zero-Mutation Oracles

- **Severity** - Major
- **Disposition** - `current_required` (`acceptance_gap`)
- **Location** - [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py) (`_assert_pre_approval_zero_mutation`, S7 Replay)
- **Evidence** - [src/hmda_reliability/hmda_data/ingestion/identity.py](../../src/hmda_reliability/hmda_data/ingestion/identity.py)에서 `_VOLATILE_COLUMNS = frozenset({"ingested_at"})`로 규정되어 `PartitionContentIdentity` 해시 계산 시 `ingested_at`이 배제됩니다. S7 단계는 검증 대상인 `execute_approved_backfill()`의 자체 반환값(`mutation_state == "already_recovered"`)과 논리적 identity(`actual_identity == clean_identity`), row count만 단언합니다. 구현체에서 Replay 시 파티션을 불필요하게 `DELETE`/`INSERT`로 재작성하더라도 논리 데이터가 동일하면 `ingested_at`만 바뀐 채 모든 단언을 통과(False Green)합니다.
- **Impact** - [openspec/specs/reliability-recovery-backfill/spec.md](../../openspec/specs/reliability-recovery-backfill/spec.md)의 복구 조정 규약(기 복구 상태 시 파티션 덮어쓰기 금지)을 독립적으로 증명하지 못하여, 중복 I/O 및 테이블 락을 유발하는 redundant write 회귀를 검출할 수 없습니다.
- **Required Change** - Replay 호출 전 대상 DB 파티션의 `partition_max_ingested_at()` 또는 `ingested_at` 메타데이터를 스냅샷하고, Replay 호출 직후에도 해당 provenance가 정확히 동일함을 비교하는 독립 단언을 추가합니다. S2/S4의 `_assert_pre_approval_zero_mutation`에도 동일한 provenance 보존 검증을 보강합니다.

### F3. Pre-Approval Safety Cases Do Not Prove Blocking Prior to Source Processing

- **Severity** - Major
- **Disposition** - `current_required` (`acceptance_gap`)
- **Location** - [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py) (`test_pre_approval_safety_rejected_approval_zero_mutation`, `test_pre_approval_safety_mismatched_actions_zero_mutation`)
- **Evidence** - [openspec/specs/reliability-recovery-backfill/spec.md](../../openspec/specs/reliability-recovery-backfill/spec.md)의 `Requirement: Approval gate`는 승인 결함 시 소스 처리(I/O, staging) 및 타깃 변경 전에 요청을 차단할 것을 명시합니다. 현재 두 안전 테스트는 모두 정상 유효 파일(`clean_csv`)을 전달하므로, 구현체에서 소스 파일을 먼저 스테이징한 뒤 승인 상태를 검증하는 순서 역전 결함이 발생하더라도 테스트가 그대로 통과합니다.
- **Impact** - 미승인 요청에 대해 불필요한 대용량 파일 I/O나 스테이징 파싱이 선행 구동되는 회귀를 방지하지 못합니다.
- **Required Change** - 존재하지 않거나 유효하지 않은 파일 경로(`missing.csv`)를 소스로 전달하여, 파일 I/O 에러보다 `ApprovalGateError`가 선행하여 발생하는지 검증하도록 테스트 픽스처를 개선합니다.

### F4. Conceptual Mismatch Between Claimed Data Plane System E2E and Airflow Execution Boundary

- **Severity** - Minor
- **Disposition** - `current_required` (`acceptance_gap`)
- **Location** - [tests/data_operations/test_system_recovery_e2e.design.md](../../tests/data_operations/test_system_recovery_e2e.design.md), [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py)
- **Evidence** - PR 설명과 설계 문서는 "Data Plane 시스템 복구 E2E"를 명시하고 [openspec/specs/orchestration-pipeline/spec.md](../../openspec/specs/orchestration-pipeline/spec.md)를 참조 규격으로 제시합니다. 그러나 [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) 및 [docs/mvp.md](../../docs/mvp.md)에서 Data Plane 시스템 실행은 Apache Airflow가 소유하며, 본 테스트는 Airflow DAG 런타임을 거치지 않고 Data Operations 모듈 함수를 직접 호출합니다.
- **Impact** - 실제 Airflow 파이프라인의 런타임 설정 변환 및 태스크 의존성 검증 갭이 가려질 위험이 있습니다.
- **Required Change** - 설계 문서와 docstring의 범위를 "Data Operations ↔ Reliability Control Plane 간의 결정론적 통합 E2E 코어(Deterministic Integration E2E Core)"로 정정하고 Airflow 런타임 경계는 본 테스트 범위에서 제외됨을 명시합니다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| Independent Dual-Perspective Orchestration | `review-lead` subagent를 통한 `review-quality` 및 `review-adversarial` 독립 위임 및 통합 평가 수행 | Pass |
| PR Target and Scope Decomposition | PR #220 Base `ab90cb3`, Head `519d49b` 확인 및 커밋 `0728c1d` 무관 변경 추적 완료 | Pass |
| Contract & False-Green Analysis | [identity.py](../../src/hmda_reliability/hmda_data/ingestion/identity.py), [executor.py](../../src/hmda_reliability/reliability/recovery/executor.py), [reliability-recovery-backfill/spec.md](../../openspec/specs/reliability-recovery-backfill/spec.md) 규약 대조를 통해 S7 및 사전 승인 오라클 갭 입증 | Fail |
| CI Status Checks | GitHub Actions CI Lite run `34177719880` 성공 이력 확인 | Pass |
| Direct Local Test Execution | 현재 세션에서 pytest 직접 실행은 생략하고 CI 증적 및 코드 정적 분석으로 갈음 | Not Verified |

## Remaining Risks

- 프로덕션 코드인 [executor.py](../../src/hmda_reliability/reliability/recovery/executor.py)는 현재 `_ensure_approved()`를 `_stage_approved_candidate_source()`보다 먼저 호출하고 기 복구 상태에서 파티션을 덮어쓰지 않도록 정상 구현되어 있습니다. 따라서 F2와 F3는 프로덕션 결함이 아닌 테스트 오라클의 방어력 갭(False Green 위험)입니다.
- CI Lite 성공은 의존성 그래프가 변경된 환경에서의 실행 가능성만을 보증하므로, 무관한 lockfile 변경 분리 후 baseline 의존성 위에서 테스트 재검증이 필요합니다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise (Changes Required) | 무관한 tooling/lock 변경 분리(F1), Replay/Pre-approval 오라클의 독립 증명 보강(F2, F3), 및 E2E 경계 규약 명시(F4)가 완료되어야 신뢰할 수 있는 시스템 복구 증적으로 채택 가능함 | PR #220 head branch `agent/test/system-recovery-e2e` |
