---
type: plan
title: HMDA Data Test Design Audit and Adoption
description: HMDA Data의 서브도메인별 테스트 설계를 전수 검토하고 과거 리뷰 finding을 근거에 따라 수용·기각·보류합니다.
---

# HMDA Data Test Design Audit and Adoption

**State:** Draft / 준비 완료, 최신 기준 전수 검토와 구현은 미수행. **Base:** `81fe44b2126e1c013dd2dd68259f12e34088c47b` (착수 시 최신 main으로 재확인).

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

- [ ] 현재 main의 도메인·하위 도메인 테스트 및 support 파일 전수 inventory를 확정하고 모든 파일에 판정·제외 사유를 부여
- [ ] 각 중요 계약·위험의 대표 정상/경계/실패/회귀 사례 및 독립 oracle 검토
- [ ] 이전 리뷰의 모든 finding에 대해 수용/기각/보류/기해결 + 근거 기록
- [ ] 수용한 gap에 대한 최소 test 보강 및 필요 시 분리된 production defect 처리
- [ ] 관련 focused suite·정적 검사, 필요한 통합 검증을 현재 base/head 근거로 실행
- [ ] 독립 리뷰, 최신 evidence와 인간 검토를 거쳐 review readiness 판단

## Boundaries

- 다른 도메인의 내부 동작을 이 PR 테스트로 고정하지 않습니다. **도메인 간 실제 상호작용 검증은 마지막 cross-domain PR**에서, 앞선 PR이 main에 반영된 후 수행합니다.
- 원본 보고서의 성공·오류 주장과 과거 CI 수치는 historical이며 현재 상태를 증명하지 않습니다. 인박스는 비정본이고 계약은 OpenSpec과 source가 소유합니다.
