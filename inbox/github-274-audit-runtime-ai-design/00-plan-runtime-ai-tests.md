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
