---
type: plan
title: Cross-Domain Interface Test Design Audit and Adoption
description: 개별 도메인 테스트 검토가 반영된 뒤 도메인 경계 계약의 전수 검토와 실효성 있는 통합 테스트를 수행합니다.
---

# Cross-Domain Interface Test Design Audit and Adoption

**State:** Draft/blocked by prerequisite domain work. 새로운 통합 테스트·전수 검토·실행은 아직 수행하지 않았습니다. **Initial base:** `81fe44b2126e1c013dd2dd68259f12e34088c47b`, 실제 검증 시 선행 PR 병합 후 main으로 재확인합니다.

## Prerequisites

- 선행 검토 PR: [#269](https://github.com/mols3131d/hmda-data-reliability/pull/269), [#270](https://github.com/mols3131d/hmda-data-reliability/pull/270), [#271](https://github.com/mols3131d/hmda-data-reliability/pull/271), [#272](https://github.com/mols3131d/hmda-data-reliability/pull/272), [#273](https://github.com/mols3131d/hmda-data-reliability/pull/273), [#274](https://github.com/mols3131d/hmda-data-reliability/pull/274), [#275](https://github.com/mols3131d/hmda-data-reliability/pull/275), [#276](https://github.com/mols3131d/hmda-data-reliability/pull/276).
- 선행 PR에서 accepted/rejected/deferred finding과 변경된 테스트·계약을 확인하고, 가능한 한 모든 선행 도메인 PR이 main에 반영된 뒤 이 PR의 target/base를 재검토합니다.
- 선행 PR이 취소·보류되는 경우 영향을 받는 interface의 검증 범위를 다시 정합니다. 이 PR은 마지막에 리뷰하고 병합합니다.

## Integration Boundaries

| Interface | Representative contract to test |
| --- | --- |
| HMDA Data → Data Operations → Data Platform | Source→Bronze 적재, quality gate 통과 시 dbt build, error 시 분석 차단과 데이터 상태 보존 |
| Data Operations ↔ Data Platform ↔ Reliability | current/candidate artifact identity, lineage/profile evidence, promotion 실패와 last-known-good 보존 |
| Reliability → Review AI → Runtime AI | bounded evidence 선택·provider 메시지/오류·provenance 재현, advisory output의 비권한성 |
| Reliability proposal → approval → recovery → re-validation | exact proposal binding, 승인 범위, 실패 시 격리·재시도·recovery evidence의 일치 |
| Orchestration → Data Operations | 실제 DAGRun 순서·task failure propagation·중복 실행 부작용 경계 |

필요한 관측·제어가 가능한 최소 fixture에서 실제 서비스 경계/파일/DB 또는 deterministic fake를 선택합니다. 독립 oracle과 실패 검출력을 확인하고 이미 domain PR에서 보호한 내부 시나리오를 다시 반복하지 않습니다.

## Historical Evidence Adoption

- [PR #258의 원래 전체 목록/실행/방법/요약](01-review-historical/README.md)은 revision-bound 출발 자료이며 최신 상태의 증거가 아닙니다.
- 각 도메인 PR의 수용 결정을 확인해 남은 cross-domain finding을 `accepted / rejected / deferred / obsolete`로 판정하고, 근거·owner와 범위를 기록합니다.
- 통합 대상 전체를 current main에서 다시 식별하고, 도메인 경계별 기존 test·support·design의 관찰 범위와 제외 사유를 문서화합니다.

## Acceptance

- [ ] 선행 도메인/공통 지원 PR #269–#276의 병합 및 변경된 계약 검토
- [ ] 현재 main의 cross-domain tests/fixtures/workflows 전체 inventory와 coverage/제외 사유
- [ ] 각 interface의 주요 정상·경계·실패/복구·안전 계약을 독립 oracle로 판정
- [ ] 과거 finding과 새 evidence의 accept/reject/defer/obsolete 기록
- [ ] 누락된 고가치 통합 회귀의 최소 테스트 보강 및 관련 suite 실행
- [ ] 정확한 통합 revision 기준 CI·독립 리뷰·인간 review readiness 충족

## Boundary

여기서는 단일 도메인의 내부 테스트나 CI 도구 자체의 단위 테스트를 복제하지 않습니다. 각 영역 PR의 완료를 일괄 가정하지 않고 사용자 승인 없이 merge하지 않습니다. Inbox는 비정본입니다.

## Parallel Work And Ownership Gate

> 2026-10-25 준비 리뷰 후 확정한 병렬 작업 경계. 이 섹션은 작업 간 충돌을 피하기 위한 이 PR의 실행 계획이며 repository 전역 규칙을 변경하지 않습니다.

- **Baseline:** 이 PR의 최초 branch는 `81fe44b2`에서 생성됐습니다. PR #258은 이후 `ea39a4fd`로 main에 병합됐습니다. 실제 조사·검증·Ready 판정 때 최신 main, 현행 PR head와 prospective merge를 새로 확인하고 stale CI를 성공 근거로 사용하지 않습니다.
- **Isolation:** #269–#276은 각각 독립 작업 브랜치/worktree에서 병렬 진행할 수 있습니다. 타 PR 브랜치를 합치거나 같은 mutable fixture·DB·artifacts/캐시 디렉터리를 공유하지 않습니다. 테스트 실행은 tmp_path·별도 실행 환경으로 격리하고 자원을 점유하는 통합 실행은 필요 시 직렬화합니다.
- **Write discipline:** 아래 exclusive test 경로와 이 PR 소유 Inbox 외 파일을 수정하지 않습니다. 다른 도메인의 테스트, `tests/conftest.py`, `pyproject.toml`, `uv.lock`, `openspec/**`, `.github/workflows/**`, `scripts/ci/**` 등 공통 계약·설정/실행 경로의 변경은 여기서 수행하지 않고 #277에 전달합니다. Common Support는 자기 도메인 테스트만 수정하며 공유 production/CI 설정은 #277에서 통합합니다.
- **Read ≠ write:** 모든 관련 파일/Spec은 근거로 읽을 수 있지만, 다른 PR에 예약된 테스트는 이 PR에서 검토만 하고 발견 사항을 #277 인계 항목으로 남깁니다. **검토 파일 수 = 수정 가능 파일 수**가 아닙니다.
- **Finding handoff:** 교차 영향·공용 파일 필요 발견 시 위치/계약/재현 증거/영향/권장 oracle/필요 변경을 이 PR의 검토 결과에 기록하고 #277에서 취합합니다. 동일 문제를 두 PR이 병렬 수정하지 않습니다. 급한 안전 결함이 발견되면 조용히 우회하지 말고 사람에게 우선순위 결정을 요청합니다.
- **Completion gate:** 최신 main의 해당 도메인 tracked 테스트/fixture/design 목록과 각 하위 영역의 검토·제외 사유를 모두 기록합니다. 기존 리뷰의 모든 finding은 수용/기각/보류/기해결을 evidence와 함께 판정하고 미완료 scope를 표시합니다. 코드 검토·테스트/CI·병합 판단은 준비 문서의 완료와 구분합니다.

### PR #277 Exclusive Lane

- **Writable tests:** `예약 통합 테스트: tests/data_operations/{test_system_recovery_e2e.py,test_system_recovery_e2e.design.md,test_quality_gate.py}, tests/orchestration/{test_airflow_dagrun.py,test_airflow_dagrun.design.md,test_airflow_execution.py}, tests/review_ai/test_live_harness.py, tests/scripts/ci/{test_ci_workflow.py,test_ci_steps.py,test_ci_classifier_openspec.py}, tests/test_pytest_opentelemetry.py 및 새 교차 도메인 테스트`.
- **Reserved for final #277 (review-only here):** 선행 PR들이 소유한 일반 domain unit test에 대한 중복 수정.
- **Focus:** Source→Bronze→gate→dbt, artifact promotion↔Reliability, Review AI↔Runtime AI, recovery approval·revalidation, Airflow 실제 DAGRun, shared validation/CI entrypoint.

## Current Tracked Test Inventory Seed

**Snapshot:** `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` (2026-10-25). 아래는 GitHub tracked file 목록을 기반으로 구성한 **착수용 seed**이며, 검사한 테스트 목록이나 전수 검토 완료 근거가 아닙니다. 착수 시 현재 main을 다시 조회하고 신규/이동/삭제된 파일, fixture·design·실제 소유 계약을 반영합니다. `__init__.py` 등 지원 파일도 inventory 대상입니다.

### Exclusive Modification Candidates (11)

- `tests/data_operations/test_quality_gate.py`
- `tests/data_operations/test_system_recovery_e2e.design.md`
- `tests/data_operations/test_system_recovery_e2e.py`
- `tests/orchestration/test_airflow_dagrun.design.md`
- `tests/orchestration/test_airflow_dagrun.py`
- `tests/orchestration/test_airflow_execution.py`
- `tests/review_ai/test_live_harness.py`
- `tests/scripts/ci/test_ci_classifier_openspec.py`
- `tests/scripts/ci/test_ci_steps.py`
- `tests/scripts/ci/test_ci_workflow.py`
- `tests/test_pytest_opentelemetry.py`

### Inspect Here, Change Only In Final #277 (0)

- 없음

- 다른 PR에서 필요한 공용 설정·workflow·source 수정이 확인돼도 파일을 이 PR에 끌어오지 말고 증거를 #277의 접점 작업에 인계합니다.
