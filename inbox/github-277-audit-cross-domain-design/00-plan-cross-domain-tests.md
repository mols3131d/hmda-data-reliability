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
