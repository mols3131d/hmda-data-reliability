---
type: plan
title: Domain Test Design Review Plan
description: 도메인·서브도메인별 테스트 설계 리뷰의 고정 대상, 분할 검토 순서와 완료·검증 기준을 기록합니다.
tags:
  - testing
  - review
---

# Domain Test Design Review Plan

## Goal And Scope

사용자가 PR #258 작업의 연속으로 요청한 각 도메인·서브도메인의 테스트 설계 리뷰 보고서를 생성한다. 고정 revision은 `3ab899100fc0b35e23d464bd761f3b144a978ae7`, 작업 branch는 `agent/test/cover-sdk-retry-classification`이다. 사용자의 소유 관계 정정에 따라 [PR #258](https://github.com/mols3131d/hmda-data-reliability/pull/258)의 GitHub work unit이 이 묶음을 소유한다. 기존 27문서를 같은 내용·구조로 PR Inbox의 sequence `03`으로 이동하고 소유 관계·탐색 링크를 갱신했다.

검토 폭은 branch 전체 테스트이며, [PR의 SDK 회귀 보강 범위](../00-plan-sdk-retry-classification.md)와 구분한다. 전체 snapshot의 발견 사항을 모두 PR #258의 새 결함·필수 수정 작업으로 승격하지 않는다.

제품 도메인 7개와 공통 개발 지원 영역을 포함한다. Source 하위 패키지를 우선 사용하고, 평면 domain은 관찰 가능한 계약 단위로 하위 영역을 나눈다. 이 분류는 읽기용 review view이며 새 canonical domain 정의가 아니다. Test·fixture·design 문서를 inventory에 연결하고 관련 source·Spec으로 oracle와 실제 실행 경계를 대조한다.

리뷰는 source·test·fixture·Spec·설정·CI를 수정하지 않고 발견한 결함을 영향·근거·제안으로 기록한다. 보고서 생성 뒤 사용자가 PR #258로 푸시하고 PR을 갱신하도록 요청했으므로, 같은 branch에서 보고서와 연결 문서를 커밋·푸시하고 PR 본문에 검토 범위·실행 근거를 반영한다. 발견 사항의 구현 수정이나 새 PR 생성·branch 변경·merge는 이 전달에 포함하지 않는다. 실제 AI 품질 평가는 포함하지 않고 deterministic test와 live/human proof의 경계를 구분한다.

## Review Method

각 영역에서 contract → risk → scenario → independent oracle → assertion → 관찰 가능한 실패를 확인한다. 정상·경계·invalid input·의존성 실패·rollback/replay·격리·선택 누락을 필요한 범위에서 검토한다. Test 수, 파일 수 또는 pass count를 설계 품질로 대신하지 않는다. False green은 통과 가능한 구체적인 오동작이나 확인된 보호 공백을 제시할 때만 finding으로 채택한다.

review-lead가 quality/adversarial 두 관점을 독립 위임해 대조한다. Caller는 inventory·실행 근거·문서 합성과 material candidate의 최소 재현을 담당한다. 실제 읽은 파일과 미검토 영역을 구분하며 필요한 coverage가 빠지면 해당 판정을 보류한다.

## Work Units

| Batch | Review Work |
| --- | --- |
| A | HMDA Data, Data Platform와 dbt, Data Operations |
| B | Reliability contracts·metadata·profiling·detection·impact·remediation·recovery |
| C | Reliability evaluation과 report |
| D | Review AI, Runtime AI, Orchestration 및 compatibility 경계 |
| E | CI·scripts·도구·문서 유지보수·공통 설정·관찰 경계 |

각 batch의 독립 검토 후 해당 보고서를 만들고 inventory 상태를 갱신한다. 새로운 material evidence가 필요할 때만 최소 읽기·실행을 추가한다. 모든 batch가 닫힌 뒤 교차 중복·미매핑 파일·링크·metadata를 확인한다.

## Acceptance

- [x] 추적 중인 테스트·fixture·helper·design 파일이 담당 도메인과 review 상태에 연결된다.
- [x] 7개 제품 domain과 공통 지원 영역의 요약 보고서가 있다.
- [x] 서브도메인별 계약·시나리오·독립 oracle·mock 경계·주요 제한을 구체적인 test 근거와 함께 기록한다.
- [x] Candidate는 기존 safeguard·현재 revision과 대조하고 defect·coverage gap·optional improvement를 구분한다.
- [x] 직접 실행·독립 정적 검토·과거/현재 CI·미실행을 구분한다.
- [x] 문서 metadata·링크·Markdown을 검증하고 검토 대상이 유지됐음을 확인한다.

## Run State

Prepare: READY WITH LIMITS. Terminal: goal. Intensity: standard. Loops: 5/30. Acceptance: complete. A–E의 94파일 두 관점 full review와 결과 합성·최종 검증을 완료했다. 제품 domain 7개·공통 지원 1개·별도 하위 리뷰 15개와 plan/inventory/validation, 총 27문서를 PR #258 Inbox에 저장했다. [현재 오동작·격리 negative control·정적 gap](validation.md)을 구별하고 중복 root cause와 다른 batch의 safeguard를 대조했다. Metadata·Markdown·링크 검증, frozen HEAD·94개 target blob 동일성 확인이 통과했다. PR 귀속·탐색 링크 정정은 문서 변경이며 실행 대상은 유지한다. 보고서 생성 목표에 남은 필수 작업은 없다. 후속 구현 제안은 각 보고서의 Findings가 소유한다.

사용자가 요청한 문서 전달은 이 검토 snapshot 이후의 별도 commit으로 기록한다. 해당 commit에서도 검토 대상 94파일과 SDK 테스트 blob의 동일성을 확인하며, 최종 head의 push·CI 상태는 PR #258의 본문과 checks에서 확인한다.
