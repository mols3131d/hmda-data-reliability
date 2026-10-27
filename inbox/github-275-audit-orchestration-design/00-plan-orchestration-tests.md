---
type: plan
title: Orchestration Test Design Full Audit and Adoption
description: Orchestration 독립 테스트 설계 전수 검토와 과거 finding 선택 수용을 위한 인계 계획입니다.
---

# Orchestration Test Design Full Audit and Adoption

**State:** Bounded audit and reinforcement delivered; independent review clear. [현행 검토·검증·전달 근거](02-review-current.md). **Current base:** `be1dca8d044494e92a0d25c791471a41b5d11bcf`.

## Scope

- **Responsibility:** Orchestration. **Areas:** config, application entrypoint, Airflow DAG, DAGRun.
- **Test candidates:** `tests/orchestration/**` 및 관련 tracked helpers, fixtures, design, owner source와 OpenSpec. 과거 inventory만 신뢰하지 말고 current main 파일과 계약을 직접 새로 inventory화합니다.
- **High-value contracts:** DAG dependencies, task-order, failure propagation, config projection.
- 하위 영역별 contract→risk→scenario→independent oracle→assertion→실제 실패 검출 여부를 전수 대조하고, 파일별 reviewed/excluded를 기록합니다.

## Adoption

- [역사적 리뷰 이관본](01-review-historical/README.md)의 각 finding을 `accepted / rejected / deferred / obsolete`로 분류하고, 최신 revision과 구체적 관찰 결과 및 이유, 후속 소유자를 명시합니다. **이관은 승인 아님**.
- 실제 재현과 test gap, source bug, spec gap, 환경 문제를 구별합니다. 유효한 gap만 최소 회귀 테스트로 보강하며 이미 해결된 finding은 재구현하지 않습니다.
- 교차 도메인 End-to-End interaction은 마지막 cross-domain PR로 인계합니다. 공통 지원 도구 자체의 단위 계약은 이 PR에서 맡습니다.

## Acceptance

- [x] 관련 모든 tracked test/support/design 최신 inventory 및 검토·제외 사유
- [x] 하위 영역별 정상·경계·예외/회귀·실제 호출/상태·독립 oracle 판정
- [x] 모든 historical finding별 수용·기각·보류·기해결과 증거
- [x] 선택 수용한 gap의 최소 검증 보강, focused suite 및 관련 결정론적 검사
- [x] 최신 base/head 검증, 독립 리뷰, 인간에게 전달할 readiness 판정

## Boundary

원본 PR #258과 타 도메인의 기능·spec을 바꾸지 않습니다. 이 Inbox는 비정본이고 도메인 간 접점 검증은 마지막 PR의 책임입니다.

## Parallel Work And Ownership Gate

> 2026-10-25 준비 리뷰 후 확정한 병렬 작업 경계. 이 섹션은 작업 간 충돌을 피하기 위한 이 PR의 실행 계획이며 repository 전역 규칙을 변경하지 않습니다.

- **Baseline:** 이 PR의 최초 branch는 `81fe44b2`에서 생성됐습니다. PR #258은 이후 `ea39a4fd`로 main에 병합됐습니다. 실제 조사·검증·Ready 판정 때 최신 main, 현행 PR head와 prospective merge를 새로 확인하고 stale CI를 성공 근거로 사용하지 않습니다.
- **Isolation:** #269–#276은 각각 독립 작업 브랜치/worktree에서 병렬 진행할 수 있습니다. 타 PR 브랜치를 합치거나 같은 mutable fixture·DB·artifacts/캐시 디렉터리를 공유하지 않습니다. 테스트 실행은 tmp_path·별도 실행 환경으로 격리하고 자원을 점유하는 통합 실행은 필요 시 직렬화합니다.
- **Write discipline:** 아래 exclusive test 경로와 이 PR 소유 Inbox 외 파일을 수정하지 않습니다. 다른 도메인의 테스트, `tests/conftest.py`, `pyproject.toml`, `uv.lock`, `openspec/**`, `.github/workflows/**`, `scripts/ci/**` 등 공통 계약·설정/실행 경로의 발견은 #277에서 수집·인계합니다. Production/Spec/공유 CI·hook 수정은 exclusive test 목록에 포함되지 않으며 별도 owner와 명시적 write scope를 정한 뒤 수행합니다.
- **Read ≠ write:** 모든 관련 파일/Spec은 근거로 읽을 수 있지만, 다른 PR에 예약된 테스트는 이 PR에서 검토만 하고 발견 사항을 #277 인계 항목으로 남깁니다. **검토 파일 수 = 수정 가능 파일 수**가 아닙니다.
- **Finding handoff:** 교차 영향·공용 파일 필요 발견 시 위치/계약/재현 증거/영향/권장 oracle/필요 변경을 이 PR의 검토 결과에 기록하고 #277에서 취합합니다. 동일 문제를 두 PR이 병렬 수정하지 않습니다. 급한 안전 결함이 발견되면 조용히 우회하지 말고 사람에게 우선순위 결정을 요청합니다.
- **Completion gate:** 최신 main의 해당 도메인 tracked 테스트/fixture/design 목록과 각 하위 영역의 검토·제외 사유를 모두 기록합니다. 기존 리뷰의 모든 finding은 수용/기각/보류/기해결을 evidence와 함께 판정하고 미완료 scope를 표시합니다. 코드 검토·테스트/CI·병합 판단은 준비 문서의 완료와 구분합니다.

### PR #275 Exclusive Lane

- **Writable tests:** `tests/orchestration/** (아래 예약 파일 제외)`.
- **Reserved for final #277 (review-only here):** tests/orchestration/test_airflow_dagrun.py, test_airflow_dagrun.design.md, test_airflow_execution.py.
- **Focus:** DAG 정의·config 등 Orchestration 자체 불변식.

## Current Tracked Test Inventory Seed

**Snapshot:** `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` (2026-10-25). GitHub tracked file에 기반한 착수용 목록입니다. **전수 검토·테스트 실행 결과가 아니며**, PR 작업 착수 시 최신 main에서 변경된 경로를 다시 조회합니다.

**Write eligibility:** `tests/AGENTS.md`가 허용한 `test_*.py`, `conftest.py`, test helper/fixture 및 필요 시 `test_*.design.md`에 한정합니다. 단순히 도메인 폴더에 속한다는 이유로 `__init__.py` 또는 일반 source/config를 수정하지 않습니다. 아래의 검토 전용 파일도 전수 coverage 계산에는 포함합니다.

### Exclusive Test Modification Candidates (2)

- `tests/orchestration/test_airflow_dag.py`
- `tests/orchestration/test_config.py`

### Read-only Support Or Reserved Integration (4)

- `tests/orchestration/__init__.py`
- `tests/orchestration/test_airflow_dagrun.design.md`
- `tests/orchestration/test_airflow_dagrun.py`
- `tests/orchestration/test_airflow_execution.py`
- `__init__.py`는 support inventory 대상으로 검토하되 변경하지 않습니다. 예약 통합 파일은 #277에서, 공통 환경·CI 설정도 #277에서 선행 PR 병합 후 검토합니다.
