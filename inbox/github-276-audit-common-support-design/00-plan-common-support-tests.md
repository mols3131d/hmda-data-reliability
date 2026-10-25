---
type: plan
title: Common Support Test Design Full Audit and Adoption
description: Common Support 독립 테스트 설계 전수 검토와 과거 finding 선택 수용을 위한 인계 계획입니다.
---

# Common Support Test Design Full Audit and Adoption

**State:** Draft preparation; 검토 완료나 테스트 실행을 주장하지 않습니다. **Initial main:** `81fe44b2` (착수 시 재확인).

## Scope

- **Responsibility:** Common Support. **Areas:** CI, bootstrap/scripts, agent routes, documentation validation, architecture guard, telemetry.
- **Test candidates:** `tests/scripts/** 및 tests/test_pytest_opentelemetry.py` 및 관련 tracked helpers, fixtures, design, owner source와 OpenSpec. 과거 inventory만 신뢰하지 말고 current main 파일과 계약을 직접 새로 inventory화합니다.
- **High-value contracts:** OpenSpec selection fail-safe, workflow entry/revision, bootstrap failure, Inbox YAML validation, routing opt-out와 xdist tracing.
- 하위 영역별 contract→risk→scenario→independent oracle→assertion→실제 실패 검출 여부를 전수 대조하고, 파일별 reviewed/excluded를 기록합니다.

## Adoption

- [역사적 리뷰 이관본](01-review-historical/README.md)의 각 finding을 `accepted / rejected / deferred / obsolete`로 분류하고, 최신 revision과 구체적 관찰 결과 및 이유, 후속 소유자를 명시합니다. **이관은 승인 아님**.
- 실제 재현과 test gap, source bug, spec gap, 환경 문제를 구별합니다. 유효한 gap만 최소 회귀 테스트로 보강하며 이미 해결된 finding은 재구현하지 않습니다.
- 교차 도메인 End-to-End interaction은 마지막 cross-domain PR로 인계합니다. 공통 지원 도구 자체의 단위 계약은 이 PR에서 맡습니다.

## Acceptance

- [ ] 관련 모든 tracked test/support/design 최신 inventory 및 검토·제외 사유
- [ ] 하위 영역별 정상·경계·예외/회귀·실제 호출/상태·독립 oracle 판정
- [ ] 모든 historical finding별 수용·기각·보류·기해결과 증거
- [ ] 선택 수용한 gap의 최소 검증 보강, focused suite 및 관련 결정론적 검사
- [ ] 최신 base/head 검증, 독립 리뷰, 인간에게 전달할 readiness 판정

## Boundary

원본 PR #258과 타 도메인의 기능·spec을 바꾸지 않습니다. 이 Inbox는 비정본이고 도메인 간 접점 검증은 마지막 PR의 책임입니다.
