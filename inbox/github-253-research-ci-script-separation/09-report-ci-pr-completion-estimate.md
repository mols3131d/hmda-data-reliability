---
type: report
title: PR 253 Completion Estimate
description: PR 253의 최신 CI, 구현·리뷰 기록과 PR 설명을 대조해 리뷰 준비까지의 잔여 작업과 조건부 소요 시간을 판단한다.
tags:
  - ci
  - pull-request
  - readiness
---

# PR 253 Completion Estimate

> [!IMPORTANT]
> **핵심 구현은 대부분 끝났고, 리뷰 준비까지 약 1~2시간의 집중 작업이 남은 것으로 추정한다.** 현재는 CI 실패 2건과 오래된 PR 설명 때문에 `not_ready`다. 새로운 결함이나 범위 조정이 나오면 반나절 정도를 잡는 편이 현실적이다. 실제 병합 완료 시점은 사람의 검토·승인 대기에 달려 있으므로 이 시간에 포함하지 않는다. 시간은 측정된 작업량이 아니라 아래 근거와 가정에 따른 추정이다.

## State Basis

2026-10-04 `Asia/Seoul`에 [PR #253](https://github.com/mols3131d/hmda-data-reliability/pull/253)을 읽기 전용으로 조사했다. 이 문서는 현재 작업 branch가 소유하는 non-canonical 조사 결과이며 독립 correctness review나 PR 승인 기록이 아니다.

| Field | Observed State |
| --- | --- |
| Branch | `agent/research-ci-script-separation` |
| Base | `5532dca2fd93696d40ba870471fa2359c5662335` |
| Head | `d77d44acb658251d5153b1e50a6c2d25952cb296` |
| Prospective Merge | `f5a2a91009efc0709e7ba6800af35cdebe98c1d1` |
| GitHub | Open, Draft, `MERGEABLE`, merge state `UNSTABLE` |
| Reviews | Latest reviews와 review requests가 빈 목록; current approvals 0, changes requested 없음 |
| Diff | 57 files, +4,968 / -1,878 lines |
| Local | 조사 시작 시 clean; local HEAD와 remote PR head가 같음 |

CI checkout 로그에서 위 merge SHA와 base/head 조합을 직접 확인했다. Run의 head SHA만으로 merge 검증을 추정하지 않았다. 보고서 추가 후에는 이 파일만 미커밋 변경으로 남으며 위 원격 CI에 포함되지 않는다.

## Findings

### Two Stale Test Inputs Block Current CI

[최신 CI Lite run 37197538121](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37197538121)은 2026-10-04 20:06:21 KST에 failure로 끝났다. Selected tests는 **403 passed, 2 failed in 15.35s**였다. 두 실패 모두 [Markdown classifier 테스트](../../tests/scripts/ci/test_ci_classifier.py#L205)에 남은 `docs/development/ci.md` 입력에서 발생했다.

- `test_changed_markdown_paths_are_selected[docs/development/ci.md]`: 존재하지 않는 문서를 넣어 `markdown=false`가 반환됐다.
- `test_markdown_path_selection_stays_within_changed_scope`: 삭제된 경로가 출력에서 제외되어 입력 목록과 달라졌다.

문서의 현재 owner는 [CI README](../../docs/development/ci/README.md)다. 조사 중 두 경로를 `classify_changes.sh --markdown-paths --stdin`에 함께 넣었으며 현재 README 경로만 반환됐다. 이는 오래된 테스트 입력이라는 원인 가설을 지지한다. **테스트 기대 입력을 현재 owner로 옮기는 작은 보완이 유력하며, classifier를 바꿔 삭제 파일까지 선택하게 만들 이유는 확인되지 않았다.** 수정이나 수정 후 pytest 실행은 이번 조사에서 수행하지 않았다.

[Route 구현 보고서](08-agent-routes-skills-lock-compatibility/02-report.md#out-of-scope-failures)에도 같은 두 실패가 기록돼 있다. Route 작업 단위에서는 범위 밖이었지만 현재 PR에는 문서 이동과 route 수정이 모두 들어 있으므로 **PR 전체의 완료 blocker**다. 실패를 무시하거나 과거 success로 대체할 수 없다.

### Most Implementation Evidence Already Exists

현재 CI에서 Markdown·Inbox 검증, dependency lock·sync, package build, Python 검증과 chatbot route 검증은 success였다. 유일한 실패 step은 selected tests다. OpenSpec, Tach boundary와 dependency runtime smoke 등 skipped 항목을 통과로 세지는 않는다. Job 자체는 45초여서 현재 근거상 CI 실행 시간은 주요 잔여 작업이 아니다.

[원래 계획](00-plan-ci-validation-and-script-extraction.md)의 script extraction과 selection 계약에는 [구현 검증](02-report-ci-script-extraction-validation.md), [보정된 리뷰](04-review-ci-script-extraction-current-head.md)와 후속 Tach target 검사가 있다. [문서 캠페인](07-campaign-ci-documentation-improvement/README.md#result)은 README 중심 전환과 로컬 문서 검증 결과를 기록한다. [Route 리뷰](08-agent-routes-skills-lock-compatibility/03-review.md)는 세 finding 수정 뒤 최종 로컬 상태에 `clear`를 기록했다.

이 자료들은 이미 수행한 작업의 근거다. 과거 미커밋 상태나 부분 범위의 리뷰를 현재 57개 파일 전체의 승인으로 승격하지 않는다. **현재 확인된 두 실패 외에 큰 미구현 항목을 발견하지는 않았지만, 새 전체 correctness review를 수행한 것은 아니다.** 테스트 통과 비율도 구현 완료율로 해석하지 않는다.

### PR Description No Longer Matches Its Head

현재 PR 본문은 head를 `63535f6d46c7735777a942fd7bbb906889fc45c6`으로 적고 당시 성공 run을 연결한다. 이후 네 커밋이 추가됐으며 실제 head는 `d77d44a`다.

그 사이 CI 계약 테스트는 [책임별 패키지](../../tests/scripts/ci/)로 옮겨졌고, CI 문서는 README 중심 번들로 전환됐으며, Skills lock 호환성과 route generator 모듈화도 들어왔다. 그런데 본문에는 여전히 Skills lock·route schema 수정이 제외 범위라고 적혀 있다. 현재 실패와 추가 범위, 현재 검증 identity를 반영해야 [Description·Validation readiness](../../docs/development/vcs-git/pull-request.md#review-readiness)를 충족할 수 있다.

기존 Inbox의 미커밋·미푸시 표현은 작성 당시 기록이다. 현재 GitHub commit 목록에서 후속 커밋을 확인했으므로 이를 오늘의 미전달 작업으로 다시 세지 않는다. 과거 기록을 현재 상태로 덮어쓸 필요도 없다.

## Remaining Work

아래는 완료 경로의 제안이며 이번 조사에서 실행하거나 새 요구사항으로 확정한 계획이 아니다. 새 기능·CI 재설계 없이 현재 추가 범위를 유지한다는 가정이다.

| Order | Work | Completion Evidence | Estimated Effort |
| --- | --- | --- | --- |
| 1 | Markdown classifier 테스트 두 입력을 현재 문서 owner와 일치시킨다. | 같은 실패 사례와 classifier 모듈 통과 | 5~15분 |
| 2 | 영향 범위를 재검증한다. | CI 계약·route 관련 suite 및 필요한 정적 검사 통과; 실패 숨김 없음 | 10~20분 |
| 3 | PR 설명과 검증 근거를 갱신한다. | 테스트·문서 이동, Skills lock scope, 최신 base/head·CI 결과 일치 | 10~15분 |
| 4 | 현재 통합 변경에 적용되는 최종 리뷰를 정리한다. | 후속 변경의 기존 review 적용성 확인 및 필요한 fresh review에서 blocker 없음 | 20~40분 |
| 5 | 승인된 delivery 후 새 prospective merge CI를 확인한다. | 최종 base/head 조합의 CI success | 5~15분 + runner 대기 |

합계는 약 50~105분이다. **리뷰 준비까지 1~2시간**이라는 추정은 위 작은 수정으로 실패가 닫히고, 추가 범위를 유지하며, 최종 검토에서 새 blocker가 나오지 않는 경우다. 새로운 결함 수정이나 scope 분리 결정이 필요하면 **반나절 수준, 대략 3~4시간 이상**으로 늘 수 있다. 이는 보장된 상한이 아니다.

Ready 전환과 실제 merge는 별개다. 현재 Draft이며 GitHub 승인 리뷰는 없다. Status tool은 required approvals 0을 표시했지만, 이것이 저장소의 인간 검토 원칙을 없애지는 않는다. 사람의 Ready·승인·병합 판단과 대기 시간은 별도이며 조사만으로 실행 권한이 생기지 않는다.

## Completion Boundary

권고는 **두 테스트 입력 보완 → 현재 범위 검증 → PR 설명 갱신 → 최종 리뷰 근거 정리 → 새 merge CI 확인**으로 마무리하는 것이다. [CI 비용 검토](06-review-ci-cost-and-complexity.md#findings)의 중복 제거·환경 축소·packaging 범위 조정은 `follow_up`이며 이번 PR을 끝내기 위한 필수 작업으로 추가하지 않는다. 기존 특수 파일명·OpenSpec symlink 제한도 별도 follow-up 경계를 유지한다.

이 조사에서는 PR API·상태 검사·Actions 로그와 기존 기록을 대조하고, 로컬 Bash 경로 선택 사례 하나를 실행했다. 애플리케이션·테스트·설정 수정, pytest 재실행, 새 독립 리뷰, commit·push, PR 본문 수정, Ready·approval·merge는 하지 않았다. 최종 수정·푸시 또는 base 변경 후에는 이 readiness 판단과 CI 근거의 최신성을 다시 확인해야 한다.
