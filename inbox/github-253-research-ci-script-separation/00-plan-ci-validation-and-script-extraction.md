---
type: plan
title: CI Validation Scope and Script Extraction
description: PR 253의 불필요한 검증 제거, inline shell 분리와 동작 보존 검증을 위한 실행 순서와 완료 기준을 정의한다.
---

# CI Validation Scope and Script Extraction

PR [#253](https://github.com/mols3131d/hmda-data-reliability/pull/253)의 현재 branch에서 진행한다. 기준 revision은 `4f6c9960cda33136fe989e02ca90c40c46bc7e11`이며 [조사 보고서](../2026-10-02/22-55-research-ci-workflow-script-separation.md)와 [CI policy](../../docs/development/ci.md)가 근거다. 아래 계획은 [셀프 리뷰](01-review-ci-plan-self-review.md)를 반영했다.

## Goal

변경에 필요한 검증만 실행하면서 긴 workflow shell을 로컬에서도 실행·테스트할 수 있는 독립 스크립트로 옮긴다. 필수 검증 실패, 불확실한 영향 범위와 도구 실행 실패를 성공으로 바꾸지 않는다.

## Scope

- CI-only 변경은 classifier와 추출한 step의 계약 테스트로 보호한다. Python source, dependency와 Tach 설정의 boundary 검증은 유지하되 workflow path라는 이유만으로 Tach를 실행하는 조건은 제거한다.
- 일반 Inbox 변경은 변경 파일 formatting과 artifact metadata 검증만 선택한다. 비차단 formatting 진단은 로그에서 informational로 구분하고 docs lint·Inbox metadata failure는 계속 차단한다.
- Markdown, OpenSpec, Python validation, selected pytest의 긴 inline shell을 책임별 Bash 스크립트로 추출한다. 반복되는 변경 파일 수집은 작은 공용 helper로 모으며 단순 도구 호출과 Actions orchestration은 YAML에 유지한다.
- 새 스크립트는 scripts/ci 아래에 두고 path mapping과 회귀 테스트를 함께 추가한다. 새로운 의존성이나 범용 CI framework는 도입하지 않는다.
- pre-push의 문서-only 실행은 실제 push range와 hook contract를 대조한다. 새 branch의 첫 push에서 무관한 변경이 포함된 원인이 확인되지 않으면 hook을 추측으로 수정하지 않고 한계를 기록한다.

Skills CLI lock과 route generator의 schema 호환성 수정, 애플리케이션 변경, 전체 CI 재설계, 권한·branch protection 변경, Ready 전환과 merge는 범위 밖이다. Route-only 변경의 필요한 generator 검증을 끄지 않는다.

## Tasks

1. 검증 범위의 실패하는 회귀 테스트를 먼저 추가한다. Inbox-only 및 route-only의 기존 좁은 선택을 유지하고 CI-only에서는 Tach를 선택하지 않으며 새 스크립트의 변경은 직접 관련 테스트를 선택하게 한다.
1. classifier 조건을 수정하고 같은 테스트를 다시 실행한다. 알려지지 않은 CI helper 경로는 검증이 조용히 빠지지 않도록 CI 계약 테스트로 보수적으로 묶는다.
1. 네 step을 각각 독립 스크립트로 추출한다. 입력은 기존 selector 환경값과 base/head 인자, 출력은 도구 stdout/stderr·summary, 성공은 0·실패는 nonzero다. 비교 기본값은 prospective merge의 `HEAD^1`과 `HEAD`이며 Git 비교 실패를 빈 변경으로 바꾸지 않는다.
1. 외부 CLI는 fake executable로 통제하고 실제 임시 Git 저장소에서 변경 수집, docs-only lint, OpenSpec target, Python scoped/full, pytest scoped/unit/full 분기와 실패 전파를 검증한다. 삭제 파일과 공백 포함 경로, 빈 target, metadata-only 변경을 포함한다.
1. workflow를 짧은 script 호출로 교체한다. 현재 step 이름·조건, 도구 버전, read-only 권한, timeout/concurrency와 pytest marker·xdist 정책은 유지한다. 추출 파일만 수정해도 CI에서 해당 동작과 wiring test가 실행돼야 한다.
1. CI policy·Testing Guide의 소유 경로 설명을 갱신하고 local focused tests, shell syntax, 관련 static checks를 실행한다. 독립 review-lead가 현재 변경을 검토한 뒤 범위 안 필수 finding만 수정한다.

## Acceptance

| Scenario | Expected Evidence |
| --- | --- |
| Inbox-only / docs-only / route-only | unrelated Python, Tach, full pytest를 선택하지 않으며 해당 metadata/docs/route contract는 유지 |
| CI workflow 또는 CI helper 변경 | CI 회귀 테스트를 선택하고 unrelated domain runtime suite는 선택하지 않음 |
| source/dependency/Tach 변경 | 기존 boundary 검증과 필요한 dependency setup 유지 |
| Markdown format 진단 | 비차단·정보성으로 표시; docs lint와 tool failure는 nonzero 유지 |
| scoped/full validation | 기존 target, marker, xdist, OpenSpec strict/archive 의미를 보존 |
| Git diff 또는 external command 실패 | 빈 입력이나 성공으로 숨기지 않음 |
| workflow script invocation | 같은 입력을 로컬과 CI에서 실행 가능하고 YAML이 실제 파일을 호출 |

## Validation

테스트는 기존 classifier module과 새 CI step contract module에 한정한다. 테스트 도구는 외부 endpoint를 호출하지 않으며 임시 Git 저장소와 fake tool을 사용한다. 관련 scripts tests, Bash syntax, Python static check, 변경 Markdown과 Inbox validator를 실행하고 실제 실행 결과만 기록한다. 원격 CI와 독립 리뷰는 local test를 대체하는 근거로 취급하지 않는다.

## Delivery

이 계획 작성·셀프 리뷰·구현은 PR #253의 같은 작업 목적이다. 이번 요청에서는 파일 수정과 검증을 수행하며 commit/push/PR 본문 변경은 별도 요청 없이 하지 않는다. 실행 결과와 리뷰 제한은 해당 계획의 후속 기록과 사용자 답변에 남긴다.
