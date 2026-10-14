---
type: proposal
title: PR 253 Completion Proposal
description: PR 253의 다음 작업으로 문서 이동에 따른 테스트 실패를 최소 수정으로 닫고 현재 통합 변경의 검증·리뷰 근거를 확보하는 순서와 완료 조건을 제안한다.
tags:
  - ci
  - pull-request
  - readiness
---

# PR 253 Completion Proposal

> [!IMPORTANT]
> **단계 1~3을 로컬에서 완료했다.** 테스트 입력 두 곳을 보완했고 관련 suite 180개가 통과했으며 새 독립 리뷰는 `clear`다. 다음은 별도 승인 후의 커밋·푸시와 새 merge CI 확인이다. 현재 원격 CI 실패는 아직 해소됐다고 주장할 수 없다.

사용자의 후속 실행 요청에 따라 수정·로컬 검증·독립 리뷰를 수행했다. 결과는 [Local Execution Results](#local-execution-results)에 기록하고 원래 제안한 순서는 아래에 유지한다. Commit·push는 별도 승인이 필요하며, Ready 전환·승인·merge는 사람의 판단에 맡긴다. 로컬 리뷰의 `clear`는 PR 전체의 readiness나 승인이 아니다.

## Status Snapshot

아래는 2026-10-04 20:30:46 KST의 제안 작성 당시 PR 상태다. 후속 실행에서 같은 base/head와 Draft를 재확인했다. 테스트 보완은 미커밋·미푸시 상태이므로 원격 CI 결과와 구분하며, 전달 전에는 최신 상태를 다시 확인해야 한다.

| Field | Recorded State |
| --- | --- |
| Target | [PR #253](https://github.com/mols3131d/hmda-data-reliability/pull/253) |
| Branch | `agent/research-ci-script-separation` |
| Title | `refactor(ci): 검증 계약 정리와 route 호환성 보완` |
| PR Update | 본문에 구현 범위와 실패 근거 반영; 재조회에서 Draft·base·head 보존 확인 |
| Base | `5532dca2fd93696d40ba870471fa2359c5662335` |
| Head | `d77d44acb658251d5153b1e50a6c2d25952cb296` |
| CI | [Run 37197538121](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37197538121): 403 passed, 2 failed |
| Merge SHA | `f5a2a91009efc0709e7ba6800af35cdebe98c1d1` |

두 실패는 삭제된 `docs/development/ci.md`를 테스트 입력으로 사용하는 데서 발생했다. 상세 근거와 시간 추정은 [완료 예상 보고서](09-report-ci-pr-completion-estimate.md)를 참고한다.

## Proposed Actions

### 1. Fix Stale Test Paths

[Classifier 테스트](../../tests/scripts/ci/test_ci_classifier.py#L205)의 다음 두 입력을 [현재 CI README](../../docs/development/ci/README.md) 경로로 바꾼다.

- `test_changed_markdown_paths_are_selected`의 parameter
- `test_markdown_path_selection_stays_within_changed_scope`의 목록 항목

검증 의도는 **존재하는 변경 Markdown의 선택과 입력 범위 보존**이다. 삭제된 문서를 복원하거나 classifier의 파일 존재 확인을 완화하지 않는다.

수정 전 아래 검사로 두 실패를 재현하고, 두 입력만 수정한 직후 같은 검사를 다시 실행한다.

```bash
uv run --no-sync pytest tests/scripts/ci/test_ci_classifier.py \
  -k 'changed_markdown_paths_are_selected or markdown_path_selection_stays_within_changed_scope' \
  -q -p no:sugar -p no:cacheprovider --color=no --tb=short
```

- **Done When:** 기존 assertion을 유지한 채 위 사례가 통과하고, 변경은 두 테스트 입력으로 한정된다.
- **Reassess When:** 실패가 재현되지 않거나 다른 원인이 드러나면 현재 head·테스트·문서 상태를 확인한 뒤 수정안을 다시 판단한다.

### 2. Verify Affected Contracts

단계 1이 통과하면 기존 CI 계약 패키지와 route 관련 suite를 함께 실행한다. 현재 통합 상태에서 같은 두 실패가 사라졌는지 확인하고, 수정 파일의 정적 검사도 수행한다.

```bash
uv run --no-sync pytest \
  tests/scripts/ci \
  tests/scripts/test_generate_agent_routes.py \
  tests/scripts/test_agent_assets.py \
  -q -p no:sugar -p no:cacheprovider --color=no --tb=short
uv run --no-sync ruff check tests/scripts/ci/test_ci_classifier.py
uv run --no-sync ruff format --check tests/scripts/ci/test_ci_classifier.py
uv run --no-sync ty check tests/scripts/ci/test_ci_classifier.py
```

- **Done When:** 실행한 suite와 정적 검사에 미해결 실패가 없고, 검증한 head·작업 트리가 식별된다. 예상 통과 개수는 완료 조건으로 고정하지 않는다.
- **Limit:** 로컬 검증은 실제 upstream 조회의 새 증명이나 원격 CI를 대신하지 않는다. 새 테스트 패키지나 전체 애플리케이션 검증을 관성적으로 추가하지 않는다.

### 3. Review the Integrated Change

기존 extraction·문서·route 기록과 후속 수정의 관계를 확인한 뒤, 현재 base와 최종 변경 상태를 기준으로 필요한 새 독립 리뷰를 받는다. 검토 초점은 다음과 같다.

- 문서 이동과 테스트 입력의 일치
- workflow·classifier·module CLI의 연결
- 기존 리뷰가 후속 수정에도 적용되는 범위

**Done When:** 현재 변경에 적용되는 blocking feedback이 없고, 리뷰 범위·revision·실행 검증 한계가 분명하다.

**If Findings Remain:** 이번 범위의 필수 항목만 보완하고 관련 검증과 리뷰 적용성을 갱신한다.

[Route의 과거 scoped clear](08-agent-routes-skills-lock-compatibility/03-review.md)는 PR 전체 승인이 아니다.

### 4. Deliver and Confirm Merge CI

**별도 commit·push 승인 후** 현재 PR branch에 필요한 변경만 전달한다.

1. 기존 미커밋 보고서와 이 제안서의 포함 여부를 명시적으로 정한다. 무관한 변경은 함께 stage하지 않는다.
1. 전달 후 새 CI run이 실제로 checkout한 merge SHA와 base/head 조합을 확인한다.
1. PR 본문의 `revision`·`Validation`을 새 head와 실제 결과에 맞춘다.

- **Done When:** 최종 통합 상태의 CI가 success이고 PR 본문이 해당 상태를 반영한다.
- **Reassess When:** CI 실패나 base/head 변경이 있으면 이전 readiness 판정을 재사용하지 않는다.

조건이 충족되면 사람에게 리뷰 준비 상태를 보고하고 Ready 전환·승인·merge 판단을 넘긴다.

## Scope and Execution Record

작은 보완을 기존 PR에서 완료하는 것이 권고안이다. 현재 근거상 classifier 재설계, route 재작성, 새 dependency 도입은 필요하지 않다.

- **Follow-up:** [CI 비용 검토](06-review-ci-cost-and-complexity.md#findings)의 중복 제거·환경 축소·packaging 범위 조정과 기존 특수 파일명·OpenSpec symlink 제한은 별도 후속 작업으로 유지한다.
- **Completed at Drafting:** PR 제목·본문 갱신과 제안서 작성.
- **Not Executed at Drafting:** 코드·테스트 수정, pytest 재실행, 새 독립 리뷰, commit·push, PR lifecycle 변경. 이후 실행 결과는 아래 기록을 따른다.

## Local Execution Results

2026-10-04, branch `agent/research-ci-script-separation`의 HEAD `d77d44acb658251d5153b1e50a6c2d25952cb296` 위의 로컬 보완 결과다. 변경한 테스트는 [classifier 모듈](../../tests/scripts/ci/test_ci_classifier.py)의 문서 경로 두 곳뿐이며 assertion·classifier·workflow·route 구현은 수정하지 않았다. 이 문서에는 결과만 추가하고 기존 09번 보고서는 보존했다.

| Check | Result | Evidence |
| --- | --- | --- |
| Focused reproduction | Fail, 예상된 재현 | 수정 전 2 failed, 6 passed, 38 deselected |
| Same focused check | Pass | 수정 후 8 passed, 38 deselected |
| CI and route suite | Pass | 단계 2의 pytest 명령: 180 passed in 5.78s |
| Changed-file static checks | Pass | 단계 2의 Ruff check·format check·ty check 통과 |
| Changed-file diagnostics | Pass | 수정된 classifier 테스트의 편집기 진단 없음 |
| Independent integrated review | Clear | `review-lead`가 quality·adversarial 검토를 통합; `current_required` 없음 |
| New remote merge CI | Not Verified | 커밋·푸시하지 않았으므로 로컬 보완을 포함한 원격 실행 없음 |

VS Code 테스트 도구는 이 파일을 발견하지 못해 저장소 pytest 명령으로 실행했다. `--tach`로 테스트를 생략하지 않았다. 위 실행 결과는 구현자가 수행한 검증이며 리뷰어의 독립 실행으로 취급하지 않는다.

### Review Basis and Limits

최종 리뷰 대상은 위 base/head와 미커밋 테스트 보완이다. 테스트의 SHA-256은 `8e97d73b5d1920b296189daab4ec174b89af51f6bc890369f9f818397d1f0821`이며 리뷰 후에도 같은 값을 확인했다.

첫 리뷰는 baseline 비교 자료 부족으로 `blocked`였다. 기준 Git 리비전의 원문 snapshot을 제공하고 기존 변경 대상 14개 파일의 Git blob 일치와 신규 27개 경로의 baseline 부재를 검증한 뒤, 새 독립 리뷰에서 `clear`를 받았다. 두 specialist는 workflow·step·route generator·consumer·테스트·문서의 전후 계약을 비교했다. 원격 CI 성공이나 과거 scoped 리뷰를 현재 통합 변경의 승인으로 재사용하지 않았다.

- **Comparison Limit:** 옛 classifier·OpenSpec helper의 Bash 본문은 snapshot 범위에 없어 직접적인 본문 동등성은 검증하지 않았다. Baseline workflow·테스트와 승인 계약을 대조했으며, 이 누락이 있어야 해결되는 구체적인 필수 finding은 남지 않았다.
- **Execution Limit:** 리뷰어는 pytest·CLI·Ruff·ty·network와 Git/checksum을 직접 실행하지 않았다. Git identity와 실행 결과는 구현자가 제공한 근거다.
- **Environment Limit:** 리뷰 환경의 CI conftest에는 `pytest` import 미해결 진단이 있었으나 수정된 테스트에는 진단이 없고 실제 suite는 통과했다. 선택 interpreter 원인은 미확인 상태이며 구현 회귀로 분류하지 않았다.
- **Excluded Candidate:** 두 번째 route 출력의 쓰기 실패 시 부분 갱신 가능성은 baseline에도 같아 새 회귀가 아니다. 별도의 전체 transaction 보장은 이번 필수 수정으로 추가하지 않았다.

### Remaining Delivery

단계 4는 아직 수행하지 않았다. 별도 commit·push 승인과 전달 파일 범위를 확정한 뒤 테스트 보완을 현재 PR에 전달하고, 최종 base/head의 새 merge CI 및 PR 본문의 revision·Validation을 갱신해야 한다. Ready 전환·승인·merge는 여전히 사람의 판단 대상이다.
