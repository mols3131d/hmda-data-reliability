---
type: plan
title: Reliability Test Design Audit and Adoption
description: Reliability의 하위 영역별 모든 테스트 설계를 새로 조사하고 기존 finding의 수용 여부와 최소 회귀 보강을 결정합니다.
---

# Reliability Test Design Audit and Adoption

**State:** Draft 준비. 현재 main 전체 코드에 대한 전수 검토나 새로운 테스트·negative control 실행은 미완료. **Initial base:** `81fe44b2` (착수 시 검증).

## Scope

- **Subdomains:** contracts, metadata, profiling, detection, impact, remediation, recovery, evaluation.
- **Test candidates:** `tests/reliability/**`의 tracked modules, fixtures, helpers, designs; 각 소유 source 및 normative OpenSpec.
- 각 하위 영역별 contract·불변식·안전 경계와 테스트의 실제 관찰 범위, 독립 oracle, 성공/실패·rollback/replay·경계 사례를 전수 확인합니다. 최신 파일 inventory를 재구성하여 각각 검토/제외 사유를 기록합니다.
- Cross-domain contract/flow를 이 PR의 내부 단위 테스트에 강제로 넣지 않습니다. 마지막 cross-domain PR에 명시적으로 인계합니다.

## Finding Adoption

- [Historical Reliability reports](01-review-historical/README.md)의 R/I/E 등 각 finding을 `accepted / rejected / deferred / obsolete`로 **개별** 판정하고 이유·현재 revision·근거·필요 테스트/후속 조치를 기록합니다.
- #263~#268에 이미 병합된 G1~G6 관련 수정 및 재검증을 고려하고, 이전 오류를 현재의 미해결 결함으로 다시 주장하지 않습니다.
- 새 회귀 테스트는 현재 올바른 source에 GREEN이고 구체적인 잘못된 구현에 RED인 최소 oracle을 우선합니다. 결함 발견 시 source bug와 test gap, Spec gap을 구분합니다.

## Acceptance

- [ ] 8개 subdomain의 최신 전체 tests/support/design inventory·계약/coverage/제외 사유 완성
- [ ] 주요 정상·경계·잘못된 입력·실패·복구·재검증 흐름의 test oracle/검출력 검토
- [ ] 기존 모든 finding별 수용/기각/보류/기해결 판정 및 해당 근거
- [ ] 수용한 유효 gap에 최소 테스트 추가, 기존 회귀 보존, 필요 시 별도 production 수정을 소유자에게 전달
- [ ] focused·관련 suite, 정적 검사, 이전/현재 evidence 구분, 독립 리뷰 후 인간 검토

## Boundary

기존 Inbox는 비정본 참고이고 현재 OpenSpec·source·test가 우선합니다. 다른 도메인 간 접점 검증은 마지막 PR에서 수행합니다.
