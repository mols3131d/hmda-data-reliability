---
type: plan
title: HMDA Data Test Design Audit and Adoption
description: HMDA Data의 서브도메인별 테스트 설계를 전수 검토하고 과거 리뷰 finding을 근거에 따라 수용·기각·보류합니다.
---

# HMDA Data Test Design Audit and Adoption

**State:** Draft / 최신 main 기준 전수 검토·회귀 보강·독립 리뷰 완료, 원격 CI checkpoint 통과, 인간 검토 대기. **Audit baseline:** `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` (2026-10-25 착수 시 live main 확인). 기존 PR head `69afeef8b93eb348410b13eff3705cf302ef3983`에 main을 merge한 조사 기준은 `150d565a6be06bc71ca0c446ad26e8143523d780`이다.

## Goal And Scope

- **Owner:** HMDA Data. **Subdomains:** contracts, ingestion, eda, synthetic.
- 현행 tests/hmda_data/**, fixture·helper·test design과 해당 source/OpenSpec 계약을 빠짐없이 대조합니다. `inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/inventory.md`의 과거 94파일 목록을 현행 전수 검토의 증명으로 재사용하지 않습니다.
- 핵심 계약: source→Bronze, 다중 파일 schema, partition 교체·원자성, EDA evidence, synthetic 원본 보존.
- 각 subdomain의 위험·계약 → 테스트 시나리오 → 독립 oracle → 실제 assertion 및 failure path를 검토합니다. 파일별 coverage 상태와 제외 사유를 기록합니다.

## Historical Review And Adoption

- [이 PR로 이관한 역사적 보고서](01-review-historical/README.md)는 검토 후보 근거이며 확정 결과가 아닙니다. 원본 PR #258은 건드리지 않습니다.
- 각 기존 finding에 대해 `accepted / rejected / deferred / obsolete`를 선정하고, 이유·최신 revision·재현 근거·조치 또는 비조치 근거를 기록합니다. **복사 = 수용이 아닙니다.**
- 기존 G1–G6 일부는 #263–#268에서 대응됐으므로 현재 source/tests와 비교해 중복 수정하지 않습니다. 문제를 찾으면 test defect / production defect / spec gap / environment failure로 구분합니다.
- 불필요한 테스트·구현 추가를 피하고, 실제 회귀를 구별하는 최소 테스트만 추가합니다.

## Acceptance

- [x] 현재 main의 도메인·하위 도메인 테스트 및 support 파일 전수 inventory를 확정하고 모든 파일에 판정·제외 사유를 부여
- [x] 각 중요 계약·위험의 대표 정상/경계/실패/회귀 사례 및 독립 oracle 검토
- [x] 이전 리뷰의 모든 finding에 대해 수용/기각/보류/기해결 + 근거 기록
- [x] 수용한 gap에 대한 최소 test 보강 및 필요 시 분리된 production defect 처리
- [x] 관련 focused suite·정적 검사, 필요한 통합 검증을 현재 base/head 근거로 실행
- [ ] 독립 리뷰, 최신 evidence와 인간 검토를 거쳐 review readiness 판단 — 독립 기술 리뷰는 `clear`; 인간 review와 최종 lifecycle 판단은 남아 있다.

## Boundaries

- 다른 도메인의 내부 동작을 이 PR 테스트로 고정하지 않습니다. **도메인 간 실제 상호작용 검증은 마지막 cross-domain PR**에서, 앞선 PR이 main에 반영된 후 수행합니다.
- 원본 보고서의 성공·오류 주장과 과거 CI 수치는 historical이며 현재 상태를 증명하지 않습니다. 인박스는 비정본이고 계약은 OpenSpec과 source가 소유합니다.

## Execution And Evidence

- **Active scope:** 현행 tracked 8파일의 전수 검토, H1–H8 재판정, 실제 회귀를 구별하는 최소 테스트, 도메인 검증과 독립 리뷰. 수정 허용 경계는 아래 Exclusive Lane을 유지한다.
- **Research basis:** 최신 main과 최초 base 사이에는 HMDA Data source/test/Spec 변경이 없다. 따라서 main을 merge한 뒤 현재 도메인 파일을 기준으로 조사하며 과거 finding의 해결 여부는 코드와 실행으로 다시 판단한다.
- **Work ownership:** ingestion 2개 module, EDA 3개 module, synthetic 1개 module을 독립 분담한다. Coordinator는 fixture/support/contracts 검토, 전체 inventory·검증·최종 인계를 소유한다. 공용 fixture는 필요가 입증되기 전까지 변경하지 않는다.
- **Validation:** isolated worktree와 전용 `.venv`에서 기존 도메인 suite를 먼저 실행하고, 수정 module → 도메인 suite 및 Ruff/format/type 검사 순서로 확인한다. 새 oracle은 필요한 경우 transient negative control로 검출력을 확인한다. Production source를 수정하는 mutation 실험은 하지 않는다.
- **Review gate:** 구현 담당과 분리된 review-lead에 최종 변경을 전달한다. 발견 사항은 현재 필수 수정과 #277 follow-up을 구분한다. Draft 유지와 인간 검토·승인·merge는 별도 lifecycle gate다.
- **Artifacts:** [Ingestion](02-review-ingestion.md), [EDA](03-review-eda.md), [Synthetic](04-review-synthetic.md), [최종 inventory·검증·인계](05-report-hmda-data-audit.md)를 이 PR 경로에 남긴다.
- **Loops state:** RPI Main Loop 2/30. 첫 Review의 문서 R1과 hook 환경 실패를 두 번째 Loop에서 정정·복구했고, 독립 targeted assessment는 `clear`다. Finalize에서 기술 산출물과 원격 CI checkpoint를 확인했다. 요청된 Draft delivery 범위의 결과는 완료했고 인간 review·lifecycle gate는 별도로 남긴다. 최종 revision/evidence와 다음 행동은 [최종 보고서](05-report-hmda-data-audit.md#delivery-and-next-action)가 소유한다.

## Parallel Work And Ownership Gate

> 2026-10-25 준비 리뷰 후 확정한 병렬 작업 경계. 이 섹션은 작업 간 충돌을 피하기 위한 이 PR의 실행 계획이며 repository 전역 규칙을 변경하지 않습니다.

- **Baseline:** 이 PR의 최초 branch는 `81fe44b2`에서 생성됐습니다. PR #258은 이후 `ea39a4fd`로 main에 병합됐습니다. 실제 조사·검증·Ready 판정 때 최신 main, 현행 PR head와 prospective merge를 새로 확인하고 stale CI를 성공 근거로 사용하지 않습니다.
- **Isolation:** #269–#276은 각각 독립 작업 브랜치/worktree에서 병렬 진행할 수 있습니다. 타 PR 브랜치를 합치거나 같은 mutable fixture·DB·artifacts/캐시 디렉터리를 공유하지 않습니다. 테스트 실행은 tmp_path·별도 실행 환경으로 격리하고 자원을 점유하는 통합 실행은 필요 시 직렬화합니다.
- **Write discipline:** 아래 exclusive test 경로와 이 PR 소유 Inbox 외 파일을 수정하지 않습니다. 다른 도메인의 테스트, `tests/conftest.py`, `pyproject.toml`, `uv.lock`, `openspec/**`, `.github/workflows/**`, `scripts/ci/**` 등 공통 계약·설정/실행 경로의 변경은 여기서 수행하지 않고 #277에 전달합니다. Common Support는 자기 도메인 테스트만 수정하며 공유 production/CI 설정은 #277에서 통합합니다.
- **Read ≠ write:** 모든 관련 파일/Spec은 근거로 읽을 수 있지만, 다른 PR에 예약된 테스트는 이 PR에서 검토만 하고 발견 사항을 #277 인계 항목으로 남깁니다. **검토 파일 수 = 수정 가능 파일 수**가 아닙니다.
- **Finding handoff:** 교차 영향·공용 파일 필요 발견 시 위치/계약/재현 증거/영향/권장 oracle/필요 변경을 이 PR의 검토 결과에 기록하고 #277에서 취합합니다. 동일 문제를 두 PR이 병렬 수정하지 않습니다. 급한 안전 결함이 발견되면 조용히 우회하지 말고 사람에게 우선순위 결정을 요청합니다.
- **Completion gate:** 최신 main의 해당 도메인 tracked 테스트/fixture/design 목록과 각 하위 영역의 검토·제외 사유를 모두 기록합니다. 기존 리뷰의 모든 finding은 수용/기각/보류/기해결을 evidence와 함께 판정하고 미완료 scope를 표시합니다. 코드 검토·테스트/CI·병합 판단은 준비 문서의 완료와 구분합니다.

### PR #269 Exclusive Lane

- **Writable tests:** `tests/hmda_data/**`.
- **Reserved for final #277 (review-only here):** 없음 (아래 공통 공유 파일은 전부 제외).
- **Focus:** Source discovery, ingestion/partition, EDA, synthetic 데이터의 자체 계약.

## Current Tracked Test Inventory Seed

**Snapshot:** `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` (2026-10-25). GitHub tracked file에 기반한 착수용 목록입니다. **전수 검토·테스트 실행 결과가 아니며**, PR 작업 착수 시 최신 main에서 변경된 경로를 다시 조회합니다.

**Write eligibility:** `tests/AGENTS.md`가 허용한 `test_*.py`, `conftest.py`, test helper/fixture 및 필요 시 `test_*.design.md`에 한정합니다. 단순히 도메인 폴더에 속한다는 이유로 `__init__.py` 또는 일반 source/config를 수정하지 않습니다. 아래의 검토 전용 파일도 전수 coverage 계산에는 포함합니다.

### Exclusive Test Modification Candidates (7)

- `tests/hmda_data/conftest.py`
- `tests/hmda_data/eda/test_eda.py`
- `tests/hmda_data/eda/test_eda_evidence.py`
- `tests/hmda_data/eda/test_eda_explorer.py`
- `tests/hmda_data/test_ingestion.py`
- `tests/hmda_data/test_ingestion_partition.py`
- `tests/hmda_data/test_synthetic.py`

### Read-only Support Or Reserved Integration (1)

- `tests/hmda_data/__init__.py`

- `__init__.py`는 support inventory 대상으로 검토하되 변경하지 않습니다. 예약 통합 파일은 #277에서, 공통 환경·CI 설정도 #277에서 선행 PR 병합 후 검토합니다.
