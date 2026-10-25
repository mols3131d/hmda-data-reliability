---
type: plan
title: Data Operations Test Design Audit and Adoption
description: Data Operations 전수 테스트 검토, 과거 finding의 선택 수용과 필요한 회귀 보호를 준비합니다.
---

# Data Operations Test Design Audit and Adoption

**State:** Draft 준비. 전수 검토·테스트 실행·finding 수용은 미완료. **Initial main:** `81fe44b2` (착수 시 재확인).

## Scope

- **Owner:** Data Operations; **Subdomains:** quality gate, dbt execution/promotion, lifecycle, system recovery.
- **Targets:** `tests/data_operations/**` 및 test helper·fixture·design, 관련 source/OpenSpec 계약. 현재 main의 전체 추적 파일을 재발견하고 파일별 검토 결과 또는 제외 이유를 남깁니다.
- **High-risk contracts:** quality gate, dbt lock과 promotion, artifact identity, 장애 시 기존 증거 보존.
- 계약·위험 → 시나리오 → 독립 oracle → assertion·실행 경계·잘못된 구현 검출력을 하위 영역마다 대조합니다.

## Legacy Review Adoption

- [기존 보고서](01-review-historical/README.md)를 **검토 후보**로 이관했으며 과거 결론을 자동 승인하지 않습니다.
- 기존 finding마다 `accepted / rejected / deferred / obsolete`를 기록하고 현재 revision, 정확한 재현 또는 반박 근거, 이유, 조치 또는 후속 소유자를 명시합니다.
- #263–#268 등 이미 병합된 변경을 확인해 이미 해결한 문제를 중복 작업하지 않습니다. 실제 defect / oracle gap / spec gap을 구분합니다.
- 가치 있는 반례만 최소한의 테스트로 보강하고, 상대 도메인의 내부 구조 검증은 마지막 cross-domain PR로 이관합니다.

## Acceptance

- [ ] 현행 도메인·서브도메인 tracked tests/support/design 전수 inventory와 검토·제외 근거
- [ ] 계약·실패·경계·격리·복구의 독립 oracle 및 검출력 확인
- [ ] 모든 legacy finding별 수용·기각·보류·기해결 판단과 이유
- [ ] 채택한 필요한 테스트 보강과 현재 main 기준 targeted/related 검사
- [ ] 새 revision에 대한 독립 리뷰, evidence와 human review readiness

## Boundary

현재 파일을 읽지 않은 historical result를 검증 완료로 표현하지 않습니다. 테스트/제품/Spec의 계약은 정본을 따릅니다. **도메인 간 integration 검증은 마지막 PR**이 맡습니다.

## Parallel Work And Ownership Gate

> 2026-10-25 준비 리뷰 후 확정한 병렬 작업 경계. 이 섹션은 작업 간 충돌을 피하기 위한 이 PR의 실행 계획이며 repository 전역 규칙을 변경하지 않습니다.

- **Baseline:** 이 PR의 최초 branch는 `81fe44b2`에서 생성됐습니다. PR #258은 이후 `ea39a4fd`로 main에 병합됐습니다. 실제 조사·검증·Ready 판정 때 최신 main, 현행 PR head와 prospective merge를 새로 확인하고 stale CI를 성공 근거로 사용하지 않습니다.
- **Isolation:** #269–#276은 각각 독립 작업 브랜치/worktree에서 병렬 진행할 수 있습니다. 타 PR 브랜치를 합치거나 같은 mutable fixture·DB·artifacts/캐시 디렉터리를 공유하지 않습니다. 테스트 실행은 tmp_path·별도 실행 환경으로 격리하고 자원을 점유하는 통합 실행은 필요 시 직렬화합니다.
- **Write discipline:** 아래 exclusive test 경로와 이 PR 소유 Inbox 외 파일을 수정하지 않습니다. 다른 도메인의 테스트, `tests/conftest.py`, `pyproject.toml`, `uv.lock`, `openspec/**`, `.github/workflows/**`, `scripts/ci/**` 등 공통 계약·설정/실행 경로의 변경은 여기서 수행하지 않고 #277에 전달합니다. Common Support는 자기 도메인 테스트만 수정하며 공유 production/CI 설정은 #277에서 통합합니다.
- **Read ≠ write:** 모든 관련 파일/Spec은 근거로 읽을 수 있지만, 다른 PR에 예약된 테스트는 이 PR에서 검토만 하고 발견 사항을 #277 인계 항목으로 남깁니다. **검토 파일 수 = 수정 가능 파일 수**가 아닙니다.
- **Finding handoff:** 교차 영향·공용 파일 필요 발견 시 위치/계약/재현 증거/영향/권장 oracle/필요 변경을 이 PR의 검토 결과에 기록하고 #277에서 취합합니다. 동일 문제를 두 PR이 병렬 수정하지 않습니다. 급한 안전 결함이 발견되면 조용히 우회하지 말고 사람에게 우선순위 결정을 요청합니다.
- **Completion gate:** 최신 main의 해당 도메인 tracked 테스트/fixture/design 목록과 각 하위 영역의 검토·제외 사유를 모두 기록합니다. 기존 리뷰의 모든 finding은 수용/기각/보류/기해결을 evidence와 함께 판정하고 미완료 scope를 표시합니다. 코드 검토·테스트/CI·병합 판단은 준비 문서의 완료와 구분합니다.

### PR #270 Exclusive Lane

- **Writable tests:** `tests/data_operations/** (아래 예약 파일 제외)`.
- **Reserved for final #277 (review-only here):** tests/data_operations/test_system_recovery_e2e.py, test_system_recovery_e2e.design.md, test_quality_gate.py.
- **Focus:** DBT 실행·promotion·quality gate 호출·lifecycle 조합 중 Data Operations가 단독으로 관찰 가능한 계약.

## Current Tracked Test Inventory Seed

**Snapshot:** `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` (2026-10-25). GitHub tracked file에 기반한 착수용 목록입니다. **전수 검토·테스트 실행 결과가 아니며**, PR 작업 착수 시 최신 main에서 변경된 경로를 다시 조회합니다.

**Write eligibility:** `tests/AGENTS.md`가 허용한 `test_*.py`, `conftest.py`, test helper/fixture 및 필요 시 `test_*.design.md`에 한정합니다. 단순히 도메인 폴더에 속한다는 이유로 `__init__.py` 또는 일반 source/config를 수정하지 않습니다. 아래의 검토 전용 파일도 전수 coverage 계산에는 포함합니다.

### Exclusive Test Modification Candidates (2)

- `tests/data_operations/test_dbt_runner.py`
- `tests/data_operations/test_incident_lifecycle.py`

### Read-only Support Or Reserved Integration (4)

- `tests/data_operations/__init__.py`
- `tests/data_operations/test_quality_gate.py`
- `tests/data_operations/test_system_recovery_e2e.design.md`
- `tests/data_operations/test_system_recovery_e2e.py`

- `__init__.py`는 support inventory 대상으로 검토하되 변경하지 않습니다. 예약 통합 파일은 #277에서, 공통 환경·CI 설정도 #277에서 선행 PR 병합 후 검토합니다.
