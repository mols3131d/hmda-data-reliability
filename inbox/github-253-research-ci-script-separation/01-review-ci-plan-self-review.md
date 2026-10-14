---
type: review
title: CI Plan Self-Review
description: PR 253의 CI 범위 개선과 script extraction 계획을 기존 계약, 위험과 실행 가능성에 대조한다.
---

# CI Plan Self-Review

> [!IMPORTANT]
> **Revised before implementation** — 채팅의 작업 목록을 실행 가능한 계획으로 구체화했다. 불필요한 검증 제거와 script extraction의 목적은 유지하되 세 가지 조건을 보완했다. 작성자가 수행한 셀프 리뷰이며 독립 구현 리뷰나 GitHub approval은 아니다.

- **Target** — [구현 계획](00-plan-ci-validation-and-script-extraction.md), 앞선 채팅의 작업 목록
- **Revision** — branch `agent/research-ci-script-separation`, 기준 `4f6c9960cda33136fe989e02ca90c40c46bc7e11`
- **Scope** — 영향 라우팅, 추출 단계의 실패 의미, hook 변경 경계와 검증 가능성

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Major | script를 새 경로로 옮기면 기존 classifier가 새 경로의 변경을 검사하지 않을 수 있다. | CI helper 변경을 CI 계약 테스트로 명시적으로 연결하고 workflow wiring도 검증한다. |
| F2 | Major | process substitution의 Git 비교 실패를 빈 파일 목록으로 처리하면 필요한 검증이 빠질 수 있다. | 변경 수집의 실패를 전파하고 invalid revision 회귀 테스트를 추가한다. |
| F3 | Minor | 이전 문서-only push의 넓은 hook 실행을 곧바로 CI defect나 hook configuration defect로 확정할 근거가 없다. | CI와 hook evidence를 분리하고 실제 push range가 입증되지 않으면 hook은 변경하지 않는다. |

계획은 위 조치를 포함한다. Skills lock 실패는 이미 독립된 Python generator에서 발생하므로 inline shell 추출의 해결 대상으로 삼지 않으며 필요한 route 검증을 유지한다. Inbox 링크 메시지는 관찰한 CI run에서 비차단이므로 검증을 꺼서 해결할 blocker가 아니라 결과 표시를 명료하게 할 대상이다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| Pass | Scope and ownership inspection | 기존 CI policy의 Markdown/Inbox boundary와 classifier의 CI path selection을 대조했다. |
| Pass | Existing test inspection | classifier stdin tests와 workflow wiring assertions를 재사용할 수 있다. |
| Not Verified | Implementation behavior | 계획 리뷰 시점에는 script extraction과 새로운 회귀 테스트를 아직 실행하지 않았다. |

## Risks and Limits

셀프 리뷰는 실제 구현의 correctness를 증명하지 않는다. 구현 후 focused validation과 별도 review-lead 검토가 필요하다. pre-push range 원인과 Skills CLI vendor schema는 이 계획의 확인되지 않은 독립 경계로 유지한다.
