---
type: review
title: PR 251 High-Intensity Review
description: PR #251의 evaluation subdomain 리팩터링을 계약 보존, 실패 경계, 회귀 검출력과 최신 review evidence 관점에서 심층 검토한다.
---

# PR 251 High-Intensity Review

> [!IMPORTANT]
> **Revise** — 핵심 runtime·serialization 회귀는 찾지 못했다. 다만 reviewed source head가 기존 독립 리뷰 기준점을 지난 뒤 변경됐는데 PR 본문과 완료 보고서는 이를 문서 변경으로만 설명해 review evidence를 과도하게 적용한다. 두 source docstring도 실제 계약과 다르다.

- **Target** — [PR #251](https://github.com/mols3131d/hmda-data-reliability/pull/251) 전체 diff와 최신 review/readiness evidence
- **Revision** — base `5532dca2fd93696d40ba870471fa2359c5662335`, reviewed source head `6ccc1b893b7f5ac71e73dcb9c291654674d51bbc`; 이 review artifact의 후속 commit은 documentation-only다.
- **Scope** — Python/wire compatibility, Langfuse child·failure boundary, consumer migration, test false-green, review evidence freshness

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 Major | PR 본문과 완료 보고서가 `5bde8a4` 이후를 문서 변경으로만 설명하지만 `a2d85c1`은 Python 5개를 수정했다. 본문상 `5bde8a4`의 독립 리뷰와 full-suite 근거가 최신 source에도 적용되는 것처럼 읽힌다. | PR state basis를 최신 head/CI로 갱신하고, 기존 독립 리뷰·full-suite의 적용 범위를 `5bde8a4`로 제한한다. 최신 source에 독립 리뷰가 필요하면 다시 수행한다. |
| F2 | 🟡 Minor | `_project_revision()`은 전체 작업 폴더가 깨끗해야 한다고 설명하지만 실제 검사는 untracked file을 제외한 tracked worktree만 확인한다. | 독스트링을 tracked worktree 조건으로 좁힌다. |
| F3 | 🟡 Minor | `evaluation` package 독스트링은 기준표와 비교 모델만 공개한다고 하지만 enum, score type, 비교·렌더링·digest helper도 `__all__`로 공개한다. | 독스트링을 실제 public surface에 맞춘다. |

## Details

### F1 · Review Evidence Is Stale

#### Locations

- [PR #251 body](https://github.com/mols3131d/hmda-data-reliability/pull/251)
- [`01-report-review-ai-evaluation-subdomain-completion.md`](01-report-review-ai-evaluation-subdomain-completion.md)
- [`a2d85c1`](https://github.com/mols3131d/hmda-data-reliability/commit/a2d85c187f03152e20144b35afd8289a0cfb667b)

#### Evidence

기존 독립 `review-lead`와 전체 pytest 근거는 code head `5bde8a45...`에 결합돼 있다. 이후 `a2d85c1`은 `scripts/run_agentic_review_live.py`와 `review_ai` Python module 4개를 수정하고 DEBUG logging도 추가했다. Reviewed source head `6ccc1b89...`의 [CI Lite #1096](https://github.com/mols3131d/hmda-data-reliability/actions/runs/36337664204)은 prospective merge에서 build, Tach, Ruff/format, type check와 selected tests `186 passed, 1 skipped`를 통과했지만, 이는 과거 독립 리뷰를 최신 source에서 다시 수행했다는 뜻은 아니다.

#### Impact

Review readiness를 판단하는 사람이 최신 source가 이전 독립 리뷰와 전체 suite에 포함됐다고 오인할 수 있다. 코드 자체의 중대한 회귀는 확인되지 않았지만 evidence attribution이 reviewed revision과 맞지 않는다.

#### Action

PR 본문의 revision, CI 링크와 검증 범위를 최신 상태로 갱신하고 `5bde8a4` 이후 source delta를 명시한다. 기존 독립 리뷰는 해당 code head의 evidence로만 유지한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Contract and wire review | `ReviewValue*` rename은 model field, enum value, rubric identity와 digest 알고리즘을 보존하며 pre-refactor static golden이 전체 comparison JSON을 고정한다. |
| ✅ Pass | Failure-boundary review | Langfuse는 opt-in child process, bounded payload, environment allowlist, timeout, media-disable와 sanitized failure를 유지하고 projection failure가 review result를 대체하지 않는다. |
| ✅ Pass | Consumer and false-green review | active source/docs/tests의 old symbol·module path는 새 owner로 이동됐고, nested serialization mutation을 golden test가 검출한다. 남은 old reference는 historical artifact 범위다. |
| ✅ Pass | Reviewed-source CI | CI Lite #1096이 `6ccc1b89...`의 prospective merge에서 selected tests `186 passed, 1 skipped`와 static/architecture checks를 통과했다. |
| ⚪ Not Verified | Current-source independent review | 이 runtime에서는 `review-lead` subagent orchestration을 실행할 수 없다. 기존 independent clear는 `5bde8a4` 기준이며 reviewed source head의 독립 리뷰로 간주하지 않는다. |

## Risks and Limits

Reviewed-source CI는 optional Langfuse SDK integration test 1개를 dependency 부재로 skip했다. 실제 remote Langfuse ingestion, 외부 Python consumer와 human utility 평가는 이 리팩터링의 검증 범위 밖이다.
