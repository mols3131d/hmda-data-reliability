---
type: report
title: PR 251 Documentation Consistency Report
description: PR #251의 문서, OpenSpec, Inbox evidence와 현재 구현 사이의 정합성 차이를 revision 기준으로 기록한다.
---

# PR 251 Documentation Consistency Report

> [!IMPORTANT]
> 현재 코드, PR 본문과 주요 사용자 가이드는 `review_ai.evaluation` ownership과 `ReviewValue*` API에 맞다. 다만 활성 Langfuse OpenSpec Change에는 리팩터링 전 경로와 API 이름이 남아 있고, 일부 Inbox evidence는 이전 source revision을 여전히 `Current`로 표현한다.

- **Snapshot** — PR #251 head `3749339f3f86e07afbf57f029099b3ee2ce0b029`
- **Base** — `5532dca2fd93696d40ba870471fa2359c5662335`
- **Scope** — PR body, canonical Review AI Spec, active OpenSpec Changes, Review AI/testing guides, PR-owned Inbox evidence, current evaluation/Langfuse module surface
- **Result** — verified gap 2건, unresolved ownership gap 1건

## Findings

| ID | Status | Type | Finding |
| --- | --- | --- | --- |
| C1 | Verified | Stale reference | 활성 `review-ai-langfuse-projection` Change가 제거된 `review_ai.langfuse_projection`, `utility_output_digest()`와 `HumanUtilityEvaluation`을 계속 가리킨다. |
| C2 | Verified | Revision mismatch | completion/resolution Inbox evidence 일부가 resolution source head `724580a7`과 그 CI를 아직 `Current PR head` 또는 `Current PR CI`로 표현한다. |
| C3 | Unresolved | Ownership handoff | Review AI guide는 canonical Spec을 current normative owner로 설명하지만, optional Langfuse projection의 상세 requirement는 아직 active delta Spec에 남아 있다. |

## C1 Active Langfuse Change Uses Pre-Refactor References

현재 refactor contract는 optional adapter를 `review_ai/evaluation/langfuse.py`로 이동하고 digest helper를 `review_output_digest()`로 이름 바꾸며 human evaluation Python API를 `ReviewValueAssessment`로 제공한다. Deprecated alias와 old-module wrapper는 두지 않는다.

반면 활성 [`review-ai-langfuse-projection`](../../openspec/changes/review-ai-langfuse-projection/) Change에는 다음 pre-refactor reference가 남아 있다.

- [`design.md`](../../openspec/changes/review-ai-langfuse-projection/design.md): `review_ai.langfuse_projection`, `utility_output_digest()`
- [`delta Spec`](../../openspec/changes/review-ai-langfuse-projection/specs/reliability-agentic-review/spec.md): `HumanUtilityEvaluation`
- [Langfuse integration plan](../github-248-review-ai-langfuse-evaluation/00-plan-review-ai-langfuse-integration.md): 해당 Change를 `Active` implementation contract로 식별

따라서 이 reference는 단순 historical artifact로만 분류하기 어렵다. 현재 source에는 old module path나 compatibility alias가 없으므로, 활성 contract를 따라가는 독자가 존재하지 않는 경로나 API로 이동할 수 있다.

## C2 Inbox Evidence Uses Stale Current-Revision Labels

현재 PR 본문은 current PR head `3749339f...`와 source head `724580a7...`을 구분하고 current CI를 run `36342361262`에 결합한다.

그러나 다음 Inbox evidence는 `724580a7...`을 resolution source revision으로 기록하면서 일부 문구에서 계속 `Current`라고 표현한다.

- [`01-report-review-ai-evaluation-subdomain-completion.md`](01-report-review-ai-evaluation-subdomain-completion.md): `Current PR CI`
- [`04-review-resolution-review-ai-evaluation-subdomain-high-intensity.md`](04-review-resolution-review-ai-evaluation-subdomain-high-intensity.md): `현재 PR head 724580a7`, `Current-head CI Lite`

검증 결과 자체의 범위는 문서 안에서 대부분 구분되어 있지만, label만 보면 현재 PR head의 evidence로 오인할 수 있다.

## C3 Langfuse Normative Ownership Remains Unclear

[`docs/domains/review-ai.md`](../../docs/domains/review-ai.md)는 current capability의 normative behavior를 canonical [`reliability-agentic-review`](../../openspec/specs/reliability-agentic-review/spec.md) Spec이 소유한다고 설명하고 optional Langfuse projection을 current behavior로 안내한다.

Canonical Spec에는 Review Value evaluation/comparison contract가 반영되어 있지만 optional Langfuse projection과 annotation의 상세 requirement는 아직 [`review-ai-langfuse-projection` delta Spec](../../openspec/changes/review-ai-langfuse-projection/specs/reliability-agentic-review/spec.md)에 남아 있다. 해당 Change의 구현 task는 완료됐지만 remote ingestion과 human proof는 의도적으로 미검증 상태다.

이 상태가 live proof를 기다리기 위한 의도적인 active Change 유지인지, canonicalization/archive가 아직 끝나지 않은 것인지는 현재 문서만으로 확정할 수 없다. 따라서 C3는 verified defect가 아니라 unresolved ownership gap으로 둔다.

## Recommended Order

1. 활성 Langfuse Change의 old module/API reference를 current `review_ai.evaluation` surface와 맞춘다.
1. PR-owned completion/resolution evidence의 `Current` 표현을 `Resolution source` 기준으로 좁힌다.
1. Langfuse Change가 active로 남아야 하는 조건과 canonical Spec으로의 handoff 시점을 명확히 한다.

## Coverage and Limits

- Canonical Review AI Spec, #251 refactor Change, active Langfuse Change, Review AI/testing guide와 PR-owned Inbox evidence를 서로 대조했다.
- Historical review/report는 당시 revision의 기록이라는 이유만으로 stale finding으로 처리하지 않았다.
- 실제 Langfuse remote ingestion, UI와 human annotation은 검토하지 않았다.
- 이 문서는 non-canonical consistency evidence이며 owning OpenSpec, canonical docs나 implementation contract를 대체하지 않는다.
