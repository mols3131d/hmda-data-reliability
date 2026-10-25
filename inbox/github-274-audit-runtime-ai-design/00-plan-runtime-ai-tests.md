---
type: plan
title: Runtime AI Test Design Full Audit and Adoption
description: Runtime AI의 하위 영역 전체 테스트 설계를 새로 검증하고 기존 리뷰 후보를 선택 수용합니다.
---

# Runtime AI Test Design Full Audit and Adoption

**State:** Draft preparation — 구현·전수 검토·실행은 아직 미완료. **Initial base:** `81fe44b2`; 착수 시 최신 main 확인.

## Scope

- **Owner:** Runtime AI. **Subdomains:** settings/contracts, OpenAI-compatible provider, error classification/retry.
- **Targets:** `tests/runtime_ai/**`, 모든 해당 fixture/helper/design과 관련 source·OpenSpec을 최신 기준으로 재발견합니다. 과거 94파일 inventory는 현재 coverage의 증거로 재사용하지 않습니다.
- **Important contracts:** provider-neutral messages, typed failure, bounded attempt_count와 실제 SDK 오류 분류; PR #258 보강 이후 남은 회귀 공백.
- 각 하위 영역의 contract→risk→scenario→independent oracle→assertion과 mock 경계를 추적하고, 모든 대상 파일을 reviewed/excluded로 기록합니다.

## Historical Finding Decisions

- [Historical sources](01-review-historical/README.md)를 있는 그대로 수용하지 않습니다. 각 finding의 최신 근거를 조사하고 `accepted / rejected / deferred / obsolete`로 이유·근거 revision·owner·후속 조치를 기록합니다.
- 이미 source/tests로 해결된 항목은 중복 구현하지 않습니다. 회귀 검출력의 구체적인 witness가 있는 경우에만 최소 회귀 테스트를 추가합니다.
- Production defect와 test design gap, Spec gap, 환경 실패를 구분합니다. 도메인 밖 cross-boundary 검증은 마지막 PR로 이관합니다.

## Acceptance

- [ ] 해당 domain/subdomain의 최신 tracked test·support·design inventory와 검토/제외 근거
- [ ] 각 주요 계약·정상·경계·failure path·회귀 oracle의 설계/검출력 확인
- [ ] 과거 모든 finding별 수용/기각/보류/기해결 판단 기록
- [ ] 수용한 테스트 공백의 최소 보강과 focused/관련 검증
- [ ] 최신 base/head에 맞는 독립 리뷰, validation과 인간 review readiness

## Boundary

기존 PR #258은 변경하지 않습니다. 이 Inbox는 비정본이며 도메인 간 접점 검증은 마지막 PR에서 처리합니다.

## Parallel Work And Ownership Gate

> 2026-10-25 준비 리뷰 후 확정한 병렬 작업 경계. 이 섹션은 작업 간 충돌을 피하기 위한 이 PR의 실행 계획이며 repository 전역 규칙을 변경하지 않습니다.

- **Baseline:** 이 PR의 최초 branch는 `81fe44b2`에서 생성됐습니다. PR #258은 이후 `ea39a4fd`로 main에 병합됐습니다. 실제 조사·검증·Ready 판정 때 최신 main, 현행 PR head와 prospective merge를 새로 확인하고 stale CI를 성공 근거로 사용하지 않습니다.
- **Isolation:** #269–#276은 각각 독립 작업 브랜치/worktree에서 병렬 진행할 수 있습니다. 타 PR 브랜치를 합치거나 같은 mutable fixture·DB·artifacts/캐시 디렉터리를 공유하지 않습니다. 테스트 실행은 tmp_path·별도 실행 환경으로 격리하고 자원을 점유하는 통합 실행은 필요 시 직렬화합니다.
- **Write discipline:** 아래 exclusive test 경로와 이 PR 소유 Inbox 외 파일을 수정하지 않습니다. 다른 도메인의 테스트, `tests/conftest.py`, `pyproject.toml`, `uv.lock`, `openspec/**`, `.github/workflows/**`, `scripts/ci/**` 등 공통 계약·설정/실행 경로의 변경은 여기서 수행하지 않고 #277에 전달합니다. Common Support는 자기 도메인 테스트만 수정하며 공유 production/CI 설정은 #277에서 통합합니다.
- **Read ≠ write:** 모든 관련 파일/Spec은 근거로 읽을 수 있지만, 다른 PR에 예약된 테스트는 이 PR에서 검토만 하고 발견 사항을 #277 인계 항목으로 남깁니다. **검토 파일 수 = 수정 가능 파일 수**가 아닙니다.
- **Finding handoff:** 교차 영향·공용 파일 필요 발견 시 위치/계약/재현 증거/영향/권장 oracle/필요 변경을 이 PR의 검토 결과에 기록하고 #277에서 취합합니다. 동일 문제를 두 PR이 병렬 수정하지 않습니다. 급한 안전 결함이 발견되면 조용히 우회하지 말고 사람에게 우선순위 결정을 요청합니다.
- **Completion gate:** 최신 main의 해당 도메인 tracked 테스트/fixture/design 목록과 각 하위 영역의 검토·제외 사유를 모두 기록합니다. 기존 리뷰의 모든 finding은 수용/기각/보류/기해결을 evidence와 함께 판정하고 미완료 scope를 표시합니다. 코드 검토·테스트/CI·병합 판단은 준비 문서의 완료와 구분합니다.

### PR #274 Exclusive Lane

- **Writable tests:** `tests/runtime_ai/**`.
- **Reserved for final #277 (review-only here):** tests/review_ai/test_live_harness.py 및 실제 Review AI→Runtime AI 연결 시나리오.
- **Focus:** provider settings, SDK wire contract, bounded retry (PR #258 merge 반영 후 현행 검토).

## Current Tracked Test Inventory Seed

**Snapshot:** `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` (2026-10-25). GitHub tracked file에 기반한 착수용 목록입니다. **전수 검토·테스트 실행 결과가 아니며**, PR 작업 착수 시 최신 main에서 변경된 경로를 다시 조회합니다.

**Write eligibility:** `tests/AGENTS.md`가 허용한 `test_*.py`, `conftest.py`, test helper/fixture 및 필요 시 `test_*.design.md`에 한정합니다. 단순히 도메인 폴더에 속한다는 이유로 `__init__.py` 또는 일반 source/config를 수정하지 않습니다. 아래의 검토 전용 파일도 전수 coverage 계산에는 포함합니다.

### Exclusive Test Modification Candidates (2)

- `tests/runtime_ai/test_provider.py`
- `tests/runtime_ai/test_settings.py`

### Read-only Support Or Reserved Integration (1)

- `tests/runtime_ai/__init__.py`

- `__init__.py`는 support inventory 대상으로 검토하되 변경하지 않습니다. 예약 통합 파일은 #277에서, 공통 환경·CI 설정도 #277에서 선행 PR 병합 후 검토합니다.
