---
type: review
title: Agent Routes Compatibility Review
description: PR 253 route 번들의 source·CLI·CI·테스트 계약을 독립 검토한 결과와 finding 대응, 최종 검증 한계를 확인할 때 사용한다.
---

# Agent Routes Compatibility Review

> [!IMPORTANT]
> 최종 fresh independent review의 Assessment는 `clear`다. 승인된 범위에 미해결 `current_required` finding과 review blocker가 없다. 이 판정은 아래 로컬 상태에만 적용하며 원격 CI 성공을 의미하지 않는다.

- **Target:** PR #253의 08번 route bundle·Skills lock compatibility 구현.
- **Revision:** branch `agent/research-ci-script-separation`, HEAD/baseline `cf9c1384bdd9c8c8cedc01c001f0806095ff766e` 위의 uncommitted 상태. [Report의 12개 파일 fingerprint](02-report.md#exact-state)로 최종 review 대상을 식별한다.
- **Scope:** bundle 5개 파일, 기존 generator 삭제, Agent Assets·classifier·workflow·현행 README와 관련 테스트 3개. 병행 07번 문서 작업은 제외했다.

## Findings

현재 미해결 finding은 없다. 아래는 앞선 두 독립 리뷰에서 발견하고 최종 리뷰 전에 해소한 항목이다. 모두 승인된 출력·이름·오류 계약 안의 `current_required`로 판단해 수정했으며, 수정만으로 이전 판정을 통과로 바꾸지 않고 fresh review를 받았다.

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Major | 검증된 archive 경로의 예약문자가 실제 HTTP 조회 대상을 바꿀 수 있었다. | version 1의 검증된 경로에만 URL 인코딩 적용. 정확한 후속 요청 URL 회귀로 해소. |
| F2 | Major | explicit `skillPath`가 같은 이름의 Skill 중복 거부를 우회했다. | 전체 eligible Skill의 이름 유일성을 먼저 검사. 유효한 hash·explicit path·중복 이름 회귀로 해소. |
| F3 | Major | HTTP `IncompleteRead`가 조회 오류 `2`가 아닌 미처리 예외로 전파됐다. | 좁은 remote 경계에서 `HTTPException`을 생성 오류로 연결. 세 조회 단계의 exit 2·무쓰기 회귀로 해소. |

### Resolution Evidence

[Sources](../../../scripts/agent_routes/sources.py)와 [기존 generator 테스트](../../../tests/scripts/test_generate_agent_routes.py)에서 각 후보를 확인했다. 구현 담당자는 F1·F2와 commits·metadata의 F3를 수정 전 실행 실패로 재현했고, 수정 직후 동일한 판별 검사를 통과시켰다. Archive에는 잘린 chunked HTTP body를 추가해 bounded read의 같은 오류 계약도 보호했다. 이 실행 결과는 리뷰어가 수행한 것이 아니다.

최종 `review-lead`는 `review-quality`와 `review-adversarial`의 독립 정적 분석을 통합했다. 인코딩은 새 version 1 URL에만 적용되어 Rulesync·legacy URL 출력을 바꾸지 않고, 이름 검사는 explicit path와 무관하게 수행된다. HTTP 읽기 예외는 source 경계에서 변환되어 CLI의 기존 오류 처리로 전달된다. CLI 생성 단계에서는 파일을 쓰지 않으므로 실패 시 기존 route를 보존한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| Pass | Independent specialist coverage | `review-lead`가 두 specialist의 독립 분석을 받아 candidate와 승인 계약을 대조했다. 필수 specialist coverage gap 없음. |
| Pass | 최종 소스와 regression 정적 검토 | F1·F2·F3 수정과 테스트의 판별력을 확인했다. 모듈 진입점·CI 선택 경로와 옛 generator 부재도 확인했다. |
| Pass | 리뷰어의 editor diagnostics | 범위 내 Python 9개 파일 진단 없음. |
| Pass | 구현 담당자의 좁은 재현·재검증 | 예약문자·중복 이름 2개 및 실제 stdlib HTTPResponse의 전송 중단 3개 GREEN. HTTP 사례는 exit 2와 두 route 파일·디렉터리 항목 보존을 검사한다. |
| Pass | 구현 담당자의 정적·route 검사 | Ruff check/format, ty, 현재 no-project route check와 diff whitespace gate 통과. |
| Fail | 구현 담당자의 최종 관련 확장 suite | 178개 통과, 2개 실패. [Report](02-report.md#out-of-scope-failures)에 기록한 parallel07 문서 이동의 실패이며 `unrelated`로 분류했다. |
| Pass | 구현 담당자의 실제 lock smoke | 최종 bundle을 복사한 격리 환경에서 실제 #251 lock의 생성·check 모두 0. 실제 GitHub 조회로 hash와 commit URL을 확인했다. |
| Not Verified | 리뷰어의 executable verification | 리뷰어는 pytest·CLI·Ruff·ty·network를 실행하지 못했다. 부모 실행 근거를 독립 실행으로 취급하지 않았다. |
| Not Verified | 리뷰어의 Git·fingerprint 확인 | 최종 리뷰어는 branch·HEAD·baseline diff·SHA256을 독립 확인하지 못했다. Report의 identity는 구현 담당자가 확인·계산해 제공했다. |
| Not Verified | 새 구현의 remote CI | push와 새 Actions 실행은 수행하지 않았다. |

## Risks and Limits

Version 1 explicit-ref 분기와 archive symlink 제외는 전용 test oracle이 없는 비차단 coverage 한계다. 최종 리뷰는 현재 결함 근거 없이 이를 `follow_up`으로 남겼으며 이번 승인 조건으로 추가하지 않았다.

독립 리뷰 판정은 명시된 구현 상태에 한정된다. 동작·계약·검증 근거나 finding disposition에 영향을 주는 후속 변경은 fresh assessment를 요구한다. Scope 밖 문서 실패, 원격 delivery와 prospective merge CI는 이 로컬 판정에 포함하지 않는다.
