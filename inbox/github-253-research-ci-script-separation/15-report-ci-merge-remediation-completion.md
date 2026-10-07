---
type: report
title: "PR 253 Remediation Completion"
description: "PR #253 개선 계획의 구현 결과, 회귀 검증과 전달 경계를 기록한 작업 완료 보고서입니다."
---

# PR 253 Remediation Completion

[개선 계획](14-plan-ci-merge-remediation.md)의 F1, F2, F4와 F3 문구 보완을 구현했다. 구현 완료는 아래 로컬 근거에 한정하며 독립 리뷰와 최신 prospective merge CI를 대신하지 않는다.

## State Basis

- Owner: [PR #253](https://github.com/mols3131d/hmda-data-reliability/pull/253), `agent/research-ci-script-separation`.
- Baseline: `ee86aff4a7a91d21541cd8f9f8a01597907ff0c1`.
- Implementation: `0c9628065a5ca08a4172ad758b1a2f8821ad90ac`; 최초 구현 `358c7d9` 이후 독립 리뷰에서 확인한 전체 타입 검사 경로를 보완했다.
- Scope: CI tooling, route 다운로드 실패 처리, 해당 테스트와 현재 동작 안내. 애플리케이션, dependency, retry 체계와 Git 손상 복구는 제외했다.

## Delivered Changes

| ID | Result | Implementation |
| --- | --- | --- |
| F1 | Implemented | Classifier와 shared 파일 수집에서 `inbox/**` 전체를 제외하고 전용 CI validator 단계를 삭제했다. 혼합 변경의 Markdown·Python·JSON·TOML 검증은 다른 경로만 받으며 전체 타입 검사에도 명시적 제외를 적용했다. Workflow 생성과 로컬 Inbox validator는 유지한다. |
| F2 | Implemented | 상한 내 archive 읽기 후 HTTPResponse에 미수신 길이가 남으면 `IncompleteRead`를 전파한다. 제한 없는 read나 retry를 추가하지 않았다. |
| F4 | Implemented | Base/head를 `rev-parse --verify --end-of-options`로 commit SHA로 확인한 뒤 비교한다. 옵션형 입력과 없는 ref는 실패하고 정상 빈 diff는 성공한다. |
| F3 | Implemented | Ref 없는 허용 source의 root `SKILL.md` 단일 파일 hash 예외와 lock의 설치 방식 식별 한계를 안내했다. 허용 범위와 hash 검증 동작은 바꾸지 않았다. |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| Pass | HTTP 중단 회귀 | `16 passed`: commits, chunked archive, 파싱 가능한 ZIP의 Content-Length 중단, metadata × 쓰기/check × 기존/없는 route. Exit 2, 기존 파일 보존·신규 파일 미생성 확인. |
| Pass | Revision 입력 회귀 | `14 passed`: 두 caller와 양쪽 인자의 옵션형/없는 revision 거부, branch·SHA·HEAD의 빈 비교 성공. |
| Pass | Inbox 분류·step·workflow | `96 passed`: 존재하는 6개 확장자, 삭제·이름 변경 경로와 혼합 변경; Markdown 및 structured-data 입력 제외. |
| Pass | 관련 전체 suite | `PYTHONDONTWRITEBYTECODE=1 uv run --no-sync pytest -p no:cacheprovider tests/scripts/ci tests/scripts/test_generate_agent_routes.py tests/scripts/test_agent_assets.py -q`: 최종 구현에서 `238 passed in 6.33s`. |
| Pass | 전체 타입 검사 제외 | 임시 Inbox 파일의 `int`에 문자열을 대입해 기본 `ty check`가 정확히 1건을 진단하는 것을 확인했다. 같은 파일에서 `ty check --exclude 'inbox/**'`는 통과했고 focused command 계약 테스트도 `1 passed`다. 임시 파일은 제거했다. |
| Pass | Python quality | 변경 파일 Ruff check/format, `ty check scripts/agent_routes tests/scripts/ci tests/scripts/test_generate_agent_routes.py`. |
| Pass | Bash | 변경한 3개 script의 `bash -n`, `git diff --check`. |
| Pass | 안내 문서 | Repository 설정의 rumdl check와 MD001/MD051/MD052/MD057 검사, pre-commit hook 성공. |
| Not Verified | 원격 prospective merge CI | 이 구현 commit의 원격 CI는 보고서 작성 시점에 아직 실행 전이다. 이전 head의 CI를 새 구현 성공으로 세지 않는다. |

## Review And Delivery

작업 완료 후 별도 context의 `review-lead`로 quality/adversarial 리뷰를 수행했다. 최초 리뷰는 전체 타입 검사의 Inbox 제외 여부를 `unknown`으로 남겨 `blocked`였으며, 실제 probe로 확인한 뒤 현재 승인된 F1 범위에서 보완했다. 최종 구현의 재리뷰는 `clear`다. 범위와 제한은 [독립 리뷰 보고서](16-review-ci-merge-remediation.md)가 소유한다. 최종 전달 commit의 CI 결과는 GitHub에서 별도로 확인한다.

## Limits

VS Code 테스트 실행 도구가 비활성화되어 native pytest를 사용했다. 실제 tracked되지 않은 Skills lock의 network end-to-end와 전체 domain suite를 실행했다고 주장하지 않는다. Protection 조회 제한은 승인 불필요를 의미하지 않는다. Draft 해제, 승인, 병합과 force-push는 작업 범위가 아니다.
