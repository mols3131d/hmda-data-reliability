---
type: review
title: "Primary Marker PR Preparation Self-Review"
description: "PR #290 준비 문서의 개발 의도 보존, marker 검증 계획과 로컬 인계 실효성을 평가한다."
---

# Primary Marker PR Preparation Self-Review

> [!NOTE]
> **Preparation: fit after targeted clarification. Implementation readiness: not ready.** 마커 정합성의 원인과 시작 지점이 구체적이며, 수정 범위가 테스트로 한정되어 있다. 아래 검증 지침의 오해 가능성을 정리했으나 pytest 실행·수정은 아직 수행하지 않았다.

- **Target:** [PR #290](https://github.com/mols3131d/hmda-data-reliability/pull/290), `agent/test/align-primary-pytest-markers`
- **Revision:** 최초 리뷰 기준 `main@35d099c748cbe08ae6a12ce60acd7574fe086719` → head `1de0beb13324bbb112fa28b3f3b6c6e24fcb34ef`; 이후 준비 문서 보완은 동일 PR에서 수행
- **Scope:** 초기 인박스 3개 문서와 현재 pytest 기본 설정·테스트 코드의 정적 비교. Production code 및 실제 pytest 실행 제외

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟡 Minor | CLI `-m`이 기본 resource exclusion을 보존한다는 잘못된 가정을 유발할 수 있음 | 복합 marker 표현식과 full collection audit 절차를 명시 |
| F2 | 🟡 Minor | class-level 재분류만으로 module marker 상속을 해소할 수 있다고 오해할 소지 | marker 누적 규칙과 최소한의 유효한 이동·재표기 대안을 구분 |
| F3 | 🔵 Note | 전수 수집 결과가 확인되지 않은 상태에서 범위를 확정하면 과도한 테스트 개편으로 이어질 수 있음 | 두 근거 사례에서 시작하고 추가 결함은 실제 collection으로 판단 |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | PR 범위와 작업 인계 문서의 정적 검토 | [Research](00-research-testing-primary-marker-accuracy.md), [Plan](01-plan-testing-primary-marker-selection.md), [Handoff](02-brief-testing-primary-marker-implementation-handoff.md) |
| ✅ Pass | 정본의 primary marker 계약 확인 | [Test Design](../../docs/development/test-design.md), [Testing](../../docs/development/testing.md), [pytest config](../../pyproject.toml) |
| ⚪ Not Verified | 실제 marker collection, tests 및 CI | 작업용 Python runtime에서 실행하지 않았음 |

## Risks and Limits

Local agent는 보고서를 명령으로 무조건 수용하지 말고 현재 head의 source와 marker collection으로 재검증해야 한다. 이 리뷰는 사용자 승인이 아니며, Draft PR의 review readiness를 완료했다고 뜻하지 않는다.
