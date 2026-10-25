---
type: plan
title: Data Platform Test Design Audit and Adoption
description: Data Platform 전수 테스트 검토, 과거 finding의 선택 수용과 필요한 회귀 보호를 준비합니다.
---

# Data Platform Test Design Audit and Adoption

**State:** Draft 준비. 전수 검토·테스트 실행·finding 수용은 미완료. **Initial main:** `81fe44b2` (착수 시 재확인).

## Scope

- **Owner:** Data Platform; **Subdomains:** duckdb, sql, dbt analytics, artifacts.
- **Targets:** `tests/data_platform/** 및 tests/dbt/**` 및 test helper·fixture·design, 관련 source/OpenSpec 계약. 현재 main의 전체 추적 파일을 재발견하고 파일별 검토 결과 또는 제외 이유를 남깁니다.
- **High-risk contracts:** Bronze→mart 의미와 fixed oracle, dbt artifact pair·lineage, metric 분기.
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
