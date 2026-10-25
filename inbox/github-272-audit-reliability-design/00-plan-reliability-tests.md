---
type: plan
title: Reliability Test Design Audit and Adoption
description: Reliability의 하위 영역별 모든 테스트 설계를 새로 조사하고 기존 finding의 수용 여부와 최소 회귀 보강을 결정합니다.
---

# Reliability Test Design Audit and Adoption

**State:** 전수 조사·회귀 보강 진행 중. **Initial base:** `81fe44b2`. 2026-10-26 인계 시 원격 head `7a93a60c8b345dadc401968e2100ba19a395fd52`를 확인하고 최신 main `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`를 병합했다. 현재 조사 기준은 `b16ad5734b4a5a35c1db3d12fe03124438e71348`이다. [현재 검토](02-review-current/README.md)에서 inventory·finding 판정·검증 결과를 이어 기록한다.

## Continuation State

- **Goal:** 8개 하위 영역의 현행 테스트 설계 전수 검토와 수용한 gap의 최소 회귀 보강을 마치고 Draft PR로 전달한다.
- **Work split:** contracts·metadata·profiling·detection·impact·remediation 및 공통 support 조사, recovery 조사·보강, evaluation 조사·보강을 독립 파일 소유권으로 병렬 진행한다.
- **Validation:** 독립 worktree의 locked 환경에서 baseline → 변경 focused test → Reliability domain suite와 정적 검사 → 별도 `review-lead` 검토를 수행한다. 추가 테스트의 검출력은 잘못된 동작을 주입한 별도 실행으로 확인한다.
- **Loops State:** Prepare `READY`; intensity `standard`; Main Loop `0/30`; acceptance `open`; next `Research → Plan → Work → Review`. 미완료 항목은 아래 Acceptance와 현재 검토 결과에서 추적한다.
- **Authority:** production·공유 설정·타 도메인 변경은 #277로 인계한다. Draft 전환 해제·approval·merge는 별도 인간 결정이다.

## Scope

- **Subdomains:** contracts, metadata, profiling, detection, impact, remediation, recovery, evaluation.
- **Test candidates:** `tests/reliability/**`의 tracked modules, fixtures, helpers, designs; 각 소유 source 및 normative OpenSpec.
- 각 하위 영역별 contract·불변식·안전 경계와 테스트의 실제 관찰 범위, 독립 oracle, 성공/실패·rollback/replay·경계 사례를 전수 확인합니다. 최신 파일 inventory를 재구성하여 각각 검토/제외 사유를 기록합니다.
- Cross-domain contract/flow를 이 PR의 내부 단위 테스트에 강제로 넣지 않습니다. 마지막 cross-domain PR에 명시적으로 인계합니다.

## Finding Adoption

- [Historical Reliability reports](01-review-historical/README.md)의 R/I/E 등 각 finding을 `accepted / rejected / deferred / obsolete`로 **개별** 판정하고 이유·현재 revision·근거·필요 테스트/후속 조치를 기록합니다.
- #263~#268에 이미 병합된 G1~G6 관련 수정 및 재검증을 고려하고, 이전 오류를 현재의 미해결 결함으로 다시 주장하지 않습니다.
- 새 회귀 테스트는 현재 올바른 source에 GREEN이고 구체적인 잘못된 구현에 RED인 최소 oracle을 우선합니다. 결함 발견 시 source bug와 test gap, Spec gap을 구분합니다.

## Acceptance

- [ ] 8개 subdomain의 최신 전체 tests/support/design inventory·계약/coverage/제외 사유 완성
- [ ] 주요 정상·경계·잘못된 입력·실패·복구·재검증 흐름의 test oracle/검출력 검토
- [ ] 기존 모든 finding별 수용/기각/보류/기해결 판정 및 해당 근거
- [ ] 수용한 유효 gap에 최소 테스트 추가, 기존 회귀 보존, 필요 시 별도 production 수정을 소유자에게 전달
- [ ] focused·관련 suite, 정적 검사, 이전/현재 evidence 구분, 독립 리뷰 후 인간 검토

## Boundary

기존 Inbox는 비정본 참고이고 현재 OpenSpec·source·test가 우선합니다. 다른 도메인 간 접점 검증은 마지막 PR에서 수행합니다.

## Parallel Work And Ownership Gate

> 2026-10-25 준비 리뷰 후 확정한 병렬 작업 경계. 이 섹션은 작업 간 충돌을 피하기 위한 이 PR의 실행 계획이며 repository 전역 규칙을 변경하지 않습니다.

- **Baseline:** 이 PR의 최초 branch는 `81fe44b2`에서 생성됐습니다. PR #258은 이후 `ea39a4fd`로 main에 병합됐습니다. 실제 조사·검증·Ready 판정 때 최신 main, 현행 PR head와 prospective merge를 새로 확인하고 stale CI를 성공 근거로 사용하지 않습니다.
- **Isolation:** #269–#276은 각각 독립 작업 브랜치/worktree에서 병렬 진행할 수 있습니다. 타 PR 브랜치를 합치거나 같은 mutable fixture·DB·artifacts/캐시 디렉터리를 공유하지 않습니다. 테스트 실행은 tmp_path·별도 실행 환경으로 격리하고 자원을 점유하는 통합 실행은 필요 시 직렬화합니다.
- **Write discipline:** 아래 exclusive test 경로와 이 PR 소유 Inbox 외 파일을 수정하지 않습니다. 다른 도메인의 테스트, `tests/conftest.py`, `pyproject.toml`, `uv.lock`, `openspec/**`, `.github/workflows/**`, `scripts/ci/**` 등 공통 계약·설정/실행 경로의 변경은 여기서 수행하지 않고 #277에 전달합니다. Common Support는 자기 도메인 테스트만 수정하며 공유 production/CI 설정은 #277에서 통합합니다.
- **Read ≠ write:** 모든 관련 파일/Spec은 근거로 읽을 수 있지만, 다른 PR에 예약된 테스트는 이 PR에서 검토만 하고 발견 사항을 #277 인계 항목으로 남깁니다. **검토 파일 수 = 수정 가능 파일 수**가 아닙니다.
- **Finding handoff:** 교차 영향·공용 파일 필요 발견 시 위치/계약/재현 증거/영향/권장 oracle/필요 변경을 이 PR의 검토 결과에 기록하고 #277에서 취합합니다. 동일 문제를 두 PR이 병렬 수정하지 않습니다. 급한 안전 결함이 발견되면 조용히 우회하지 말고 사람에게 우선순위 결정을 요청합니다.
- **Completion gate:** 최신 main의 해당 도메인 tracked 테스트/fixture/design 목록과 각 하위 영역의 검토·제외 사유를 모두 기록합니다. 기존 리뷰의 모든 finding은 수용/기각/보류/기해결을 evidence와 함께 판정하고 미완료 scope를 표시합니다. 코드 검토·테스트/CI·병합 판단은 준비 문서의 완료와 구분합니다.

### PR #272 Exclusive Lane

- **Writable tests:** `tests/reliability/**`.
- **Reserved for final #277 (review-only here):** tests/data_operations/test_system_recovery_e2e.py 등 외부 도메인 소유 E2E.
- **Focus:** Reliability의 profile/detection/impact/recovery/evaluation 및 내부 approval 계약.

## Current Tracked Test Inventory Seed

**Snapshot:** `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` (2026-10-25). GitHub tracked file에 기반한 착수용 목록입니다. **전수 검토·테스트 실행 결과가 아니며**, PR 작업 착수 시 최신 main에서 변경된 경로를 다시 조회합니다.

**Write eligibility:** `tests/AGENTS.md`가 허용한 `test_*.py`, `conftest.py`, test helper/fixture 및 필요 시 `test_*.design.md`에 한정합니다. 단순히 도메인 폴더에 속한다는 이유로 `__init__.py` 또는 일반 source/config를 수정하지 않습니다. 아래의 검토 전용 파일도 전수 coverage 계산에는 포함합니다.

### Exclusive Test Modification Candidates (26)

- `tests/reliability/conftest.py`
- `tests/reliability/contracts/test_approval.py`
- `tests/reliability/contracts/test_evidence.py`
- `tests/reliability/contracts/test_incident.py`
- `tests/reliability/contracts/test_lineage.py`
- `tests/reliability/contracts/test_profile.py`
- `tests/reliability/contracts/test_recovery_proposal.py`
- `tests/reliability/contracts/test_schema_recovery.py`
- `tests/reliability/contracts/test_validation.py`
- `tests/reliability/test_approval_backfill_validation.py`
- `tests/reliability/test_basic_incident_detection.py`
- `tests/reliability/test_evaluation_report.py`
- `tests/reliability/test_fixtures.py`
- `tests/reliability/test_freshness_delay_evaluation.design.md`
- `tests/reliability/test_freshness_delay_evaluation.py`
- `tests/reliability/test_impact_analysis.py`
- `tests/reliability/test_null_spike_evaluation.py`
- `tests/reliability/test_profile_snapshots.py`
- `tests/reliability/test_quality_gate.py`
- `tests/reliability/test_recovery_runtime_evidence.py`
- `tests/reliability/test_remediation_draft.py`
- `tests/reliability/test_schema_drift_evaluation.py`
- `tests/reliability/test_schema_recovery_candidate.py`
- `tests/reliability/test_schema_recovery_executor.py`
- `tests/reliability/test_table_metadata_evidence.py`
- `tests/reliability/test_table_state_identity.py`

### Read-only Support Or Reserved Integration (2)

- `tests/reliability/__init__.py`
- `tests/reliability/contracts/__init__.py`
- `__init__.py`는 support inventory 대상으로 검토하되 변경하지 않습니다. 예약 통합 파일은 #277에서, 공통 환경·CI 설정도 #277에서 선행 PR 병합 후 검토합니다.
