---
type: review
title: "PR 253 Remediation Review"
description: "PR #253의 승인된 CI·route 개선 구현을 quality/adversarial 독립 리뷰로 대조한 결과입니다."
---

# PR 253 Remediation Review

> [!NOTE]
> **Assessment: clear.** 최종 개선 구현에 confirmed `current_required` finding이나 남은 blocker가 없다. 이는 해당 revision의 bounded 독립 리뷰 결과이며 인간 승인이나 병합 판정이 아니다.

- **Target:** [PR #253](https://github.com/mols3131d/hmda-data-reliability/pull/253)의 [개선 계획](14-plan-ci-merge-remediation.md) 구현.
- **Revision:** `ee86aff4a7a91d21541cd8f9f8a01597907ff0c1` → `0c9628065a5ca08a4172ad758b1a2f8821ad90ac`.
- **Scope:** F1 Inbox 전체 제외, F2 bounded HTTP 수신 완결성·무쓰기, F4 양쪽 revision 검증, F3 기존 hash 예외 안내와 대응 테스트. 원래 PR 전체와 과거 artifact는 재리뷰 범위가 아니다.

## Findings

최종 리뷰에서 material finding이 없다. `review-lead`가 별도 context의 `review-quality`와 `review-adversarial`을 조정하고 두 결과를 대조했다.

최초 `358c7d9` 리뷰에서는 인자 없는 전체 `ty check`가 Inbox를 포함할 가능성을 `unknown`으로 남겨 `blocked`였다. 구현자가 실제 locked 환경에서 임시 Inbox 타입 오류를 사용해 포함 여부를 확인했다. 기본 검사는 해당 오류 1건을 보고했고, 같은 파일에서 제외 옵션을 적용하면 통과했다. `python.sh`의 전체 검사에 `--exclude 'inbox/**'`와 명령 계약 테스트를 추가하고 임시 파일을 제거한 뒤 최종 revision을 새로 리뷰했다.

| Contract | Reviewed Evidence |
| --- | --- |
| F1 | Classifier 조기 제외, collector exclude pathspec, 전체 타입 검사 제외 옵션과 mixed 변경 테스트. Workflow 상시 생성, docs 차단 lint, non-Inbox formatting과 structured-data 실패 전파는 유지. |
| F2 | ZIP 파싱 전 잔여 HTTP length 검사, 기존 오류 변환과 CLI exit 2. 쓰기/check와 기존/없는 route를 포함한 무쓰기 회귀. Unknown-length, 크기 상한, hash·경로 방어 유지. |
| F4 | 양쪽 ref를 `--verify --end-of-options`와 `^{commit}`으로 검증 후 SHA 비교. 잘못된 입력의 도구 미호출, 정상 빈 비교, 삭제 제외·공백 경로 보존. |
| F3 | 문구가 baseline의 allowlisted ref-less root-blob 예외와 일치. 허용 범위 변경 없음. |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| Pass | Independent review | 두 specialist의 독립 정적 검토와 lead의 구현·테스트·BASE 대조 완료. Final assessment `clear`. |
| Pass | 구현자 실행 근거 | 최종 구현의 관련 suite `238 passed in 6.33s`, focused full-type command `1 passed`, Ruff·Bash syntax·pre-commit 성공 기록을 제공받아 검토. |
| Pass | Blocker 해소 근거 | 동일 임시 Inbox probe에서 기본 전체 ty 실패 1건, 명시적 제외로 통과한 실제 실행 기록과 FINAL의 옵션을 함께 대조. |
| Not Verified | 리뷰어 runtime 재실행 | 리뷰어 context의 shell/runtime capability 부재로 직접 실행한 test·lint·shell check는 0건. 구현자 실행을 독립 재실행으로 표현하지 않음. |
| Not Verified | 새 원격 CI | 리뷰 시점의 원격 prospective merge CI는 아직 실행 전. 이전 PR CI를 최종 구현 근거로 대체하지 않음. |

## Risks And Limits

정확한 commit에서 생성한 BASE/FINAL archive와 전체 diff를 제공했으나 리뷰어가 archive와 commit의 대응, 원본 로그·환경을 독립 인증하지 못했다. Specialist coverage gap은 없지만 실행 근거의 독립성에는 이 제한이 남는다. 실제 Skills lock의 network end-to-end와 전체 domain suite는 이번 검토에 포함하지 않았다.

후속 report-only commit은 이 구현 리뷰의 행동 근거를 바꾸지 않는다. 구현·계약·검증 근거에 영향을 주는 변경은 새 리뷰가 필요하다. Draft 해제, approval, merge, Git 손상 복구와 scope 확장은 수행하지 않았다.
