---
type: plan
title: Domain Bug And Test Design Audit
description: 기존 일곱 도메인의 버그 탐색과 테스트 설계·검출력 검토를 위한 범위, 증거 기준과 실행 계획입니다.
tags:
  - reliability
  - testing
  - review
---

# Domain Bug And Test Design Audit

기존 도메인의 실제 결함과 테스트 설계의 빈틈을 함께 조사한다. 정상 동작을 보호하는 테스트가 잘못된 구현에도 통과하는지 확인하고, 재현된 결함과 검증 공백을 근거에 따라 수정한다.

현재 187개 파일의 정적 감사와 결함 재현 근거는 [08](08-report-cloud-validation.md)·[09](09-review-cloud-audit.md)에 있다. 2026-10-17부터 실제 수정·회귀 검증은 [실행 계획](11-plan-remediation-execution.md)과 [완료 체크리스트](03-plan-audit-completion-checklist.md)의 Implementation Work Packages로 이어간다. 아래 초기 감사 계획의 체크박스는 당시 이력이다.

## State And Ownership

| Field | Value |
| --- | --- |
| Status | In Progress |
| Snapshot Date | 2026-10-14 Asia/Seoul |
| Owning Branch | `agent/docs/plan-domain-bug-test-audit` |
| Audit Baseline | `8bc62fa6ec995f2e57456d55712b36ff11b1f1d9` (`main`) |
| Scope | HMDA Data, Data Platform, Data Operations, Reliability, Review AI, Runtime AI, Orchestration |
| Current Evidence | baseline tree 187개 대상 path 검증(존재/중복 없음), [Reliability 첫 감사](02-report-reliability-schema-recovery-first-pass.md), [일곱 도메인 위험 경계 first pass](04-report-seven-domain-risk-first-pass.md) |
| Not Verified | 187개 대상의 전수 의미론 검토, domain pytest, 재현·검출력 실험, 독립 도메인 리뷰 |

초기 계획 baseline은 `5532dca2fd93696d40ba870471fa2359c5662335`(2026-10-01)이었다. 2026-10-14 `main` 동기화 뒤 현재 full SHA로 감사 기준을 갱신했으며, 이전에 미병합 상태였던 변경도 최신 `main`에 포함된 범위에서 검토한다. Base 또는 관련 코드가 바뀌면 영향받는 검토와 실행 근거를 다시 확인한다.

이 문서는 이 작업의 non-canonical 계획이다. 현재 행동 계약은 [OpenSpec Specs](../../openspec/specs/), domain 책임은 [Domain Guides](../../docs/domains/OVERVIEW.md), 테스트 방법은 [Test Design](../../docs/development/test-design.md)이 소유한다. 새 capability나 계약 변경이 필요하면 별도 OpenSpec 변경으로 다루며 결함 수정으로 위장하지 않는다.

## Scope And Priority

모든 기존 도메인의 구현과 대응 테스트 파일을 먼저 목록화하고 계약에 연결한다. 집중 검토 순서는 상태 변경 영향과 실패 시 복구 비용을 기준으로 정한다. 낮은 우선순위도 파일별 검토 또는 근거 있는 제외를 남긴다.

| Priority | Domain | Main Review Questions | Test Surface |
| --- | --- | --- | --- |
| 1 | Reliability | 임계값·state identity·approval binding·복구 실패·재시도·재검증이 계약을 지키는가? | `tests/reliability/` |
| 1 | Data Operations | quality gate와 mutation lock, dbt failure, candidate/current promotion, 오류·결과 경계가 일관적인가? | `tests/data_operations/` |
| 1 | HMDA Data | 입력 검증·partition identity·재적재·부분 실패와 synthetic defect 생성이 기존 상태를 보호하는가? | `tests/hmda_data/` |
| 1 | Data Platform | DuckDB transaction·SQL 경계·dbt 변환·artifact pair identity가 보존되는가? | `tests/data_platform/`, `tests/dbt/` |
| 2 | Review AI | evidence/context binding, 구조화 응답 검증, provenance, utility comparison과 projection failure가 advisory 경계를 지키는가? | `tests/review_ai/` |
| 2 | Runtime AI | settings·bounded invocation·timeout·응답 정규화·provider 실패가 caller 계약을 지키는가? | `tests/runtime_ai/` |
| 2 | Orchestration | dependency와 config 변환, quality gate 차단, 선행 실패·재실행의 결과가 맞는가? | `tests/orchestration/` |

공유 fixture와 domain별 `conftest.py`, pytest 설정과 테스트 실행 경로는 해당 테스트의 신뢰성에 영향을 주는 범위에서 포함한다. `tests/scripts/`와 관찰 도구 자체의 전체 감사는 제외하되, domain 테스트를 잘못 skip하거나 결과를 숨기는 실행 문제는 기록한다. 외부 provider·Langfuse live 호출은 별도 opt-in evidence로 구분하고, 로컬 mock 성공을 live proof로 취급하지 않는다.

## Test Design Review

파일마다 보호하려는 계약, 주요 scenario, 기대 결과의 근거와 적절한 test level을 확인한다. 파일 크기나 pass count를 설계 품질의 대리 지표로 사용하지 않는다.

| Dimension | Review Question | Evidence To Keep |
| --- | --- | --- |
| Contract | Spec의 requirement와 observable behavior를 검증하는가? | spec requirement와 test function 연결 |
| Scenarios | 정상·경계값·invalid input·의존성 실패·재시도·invariant 중 중요한 경로가 빠졌는가? | scenario별 test 또는 명시적 gap/exclusion |
| Oracle | 기대값이 production 계산, serializer 또는 같은 model round trip에 의존하는가? | 고정 기대값, 독립 invariant 또는 출처가 고정된 golden fixture |
| Assertions | 잘못된 반환값·persisted state·오류 상태에서도 통과할 수 있는가? | 탐지하지 못하는 구체적 오동작과 관련 assertion |
| Mocks | mock이 domain 로직을 대체하거나 실제 resource boundary를 가리는가? | 실제로 검증한 경계와 대체된 경계 |
| Isolation | shared mutable fixture, 환경변수·파일·DB 누수, 순서 의존이 있는가? | setup/cleanup과 필요한 범위의 단독·묶음 실행 |
| Level And Selection | unit/component/integration marker와 skip 조건이 계약에 맞는가? | 선택·실행·skip 근거와 환경 제한 |
| Maintainability | 중복·과도한 parameterization·내부 구현 결합·오래된 design 문서가 의미를 흐리는가? | 변경 비용 또는 검증 공백에 대한 구체적 사례 |

복잡한 상태 전이와 scenario matrix는 기존 `.design.md`와 실제 test를 함께 검토한다. 단순한 파일마다 design 문서를 새로 만들거나 테스트 개수를 늘리는 것을 목표로 하지 않는다.

## Execution Plan

- [x] 별도 branch를 원격 main에서 생성하고 baseline과 검토 대상 경로를 확인한다.
- [x] 버그 검토와 테스트 설계 검토의 범위·우선순위·증거 기준을 작성한다.
- [ ] baseline의 domain source/test 파일과 관련 spec을 목록화하고 모든 대상의 검토 또는 제외를 기록한다.
- [ ] 각 test 파일의 contract/scenario/oracle/assertion/mock/isolation/level을 검토하고 실행 여부와 구분한다.
- [ ] 우선순위 1의 실제 실행 경계와 상태 변경·실패·복구 경로를 추적한다.
- [ ] 우선순위 2의 evidence·provider·orchestration 경계를 추적한다.
- [ ] 후보 결함을 spec과 기존 safeguard에 대조하고 최소 안전한 재현으로 확인하거나 기각한다.
- [ ] 높은 영향의 테스트 공백은 합의된 계약에 대한 scenario와 독립 oracle을 설계한다.
- [ ] 중요한 검출력 의심에는 한정된 잘못된 구현을 임시로 주입하고 기존 test가 이를 잡는지 확인한다.
- [ ] 확정된 결함과 테스트 공백을 관련 회귀 테스트·설계 설명과 함께 수정한다.
- [ ] focused validation 후 영향 범위에 맞는 component/integration 검증을 수행한다.
- [ ] 최종 source/test 변경을 review-lead를 통한 독립 검토에 전달하고 finding을 해결하거나 미해결로 명시한다.
- [ ] 현재 base/head에 맞는 결과, 한계와 후속 작업으로 PR 본문을 갱신한다.

임시 변형은 격리된 checkout에서만 수행하고 delivery diff에 남기지 않는다. 전체 mutation framework 도입은 이 작업의 기본 범위가 아니다. Red test는 collection·fixture·환경 오류가 아닌 observable behavior assertion에서 실패해야 한다.

수정이 여러 독립 목적에 걸치면 재현·검토 기록은 이 PR에 유지하고 독립적으로 검토·되돌릴 수 있는 수정 PR로 분리해 연결한다. 테스트 변경 시 [Tests Agent Guidance](../../tests/AGENTS.md)와 관련 구현·OpenSpec workflow를 로드한다.

## Evidence And Findings

후속 검토 보고서는 이 PR의 Inbox directory에 추가한다. 도메인별 결과에는 다음 근거를 남긴다.

- 검토한 full source SHA, spec·source·test 위치, 검토한 파일과 제외한 파일 및 이유.
- 계약과 scenario, 도달 가능한 trigger, expected/actual behavior, 영향과 severity.
- 버그, test-design gap, 계약 모호성, 환경 제한의 구분. 선호하는 스타일만으로 버그를 선언하지 않는다.
- 재현 명령과 결과. 재현하지 못한 후보는 확인된 결함과 분리한다.
- 실행 명령·선택된 테스트·pass/fail/skip·환경 조건. 테스트 통과와 검출력 입증을 구분한다.
- 수정 전 실패와 수정 후 통과 근거, 필요할 때 사용한 임시 변형과 탐지 여부.

독립 리뷰는 이 문서의 작성자 검토와 구분한다. 필요한 독립 reviewer가 없으면 `Not Verified`로 남기며 같은 context의 self-review로 대체하지 않는다.

## Completion Criteria

전체 감사는 다음 조건을 만족할 때 완료한다. 이 계획 문서가 전달되었다는 사실은 감사 완료를 뜻하지 않는다.

- 일곱 도메인과 대응 test 파일마다 검토 상태가 있고, 미검토·제외 범위와 이유가 명확하다.
- 중요한 계약이 scenario와 oracle에 연결되며 missing coverage와 false-green 위험이 식별되어 있다.
- 확인된 결함은 수정·회귀 검증되거나, 영향·이유·후속 owner가 있는 미해결 상태로 기록된다.
- 중요한 test-design gap은 보강 검증되거나 명시적 잔여 위험으로 남는다.
- 최종 revision의 필요한 validation과 독립 리뷰 근거가 있고, failure·skip·live 미검증을 숨기지 않는다.

완료 표현은 “검토한 범위에서 확인된 결함과 검증 공백을 처리했다”로 제한한다. 모든 입력·환경에 버그가 없다는 보장은 하지 않는다.
