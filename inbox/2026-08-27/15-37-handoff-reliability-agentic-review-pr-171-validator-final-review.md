---
type: handoff
title: "PR #171 Final Validator Review Handoff"
description: "PR #171에서 남은 validator safety contract blocker와 재검증 기준을 후속 작업자에게 전달합니다."
tags:
  - reliability
  - agentic-review
  - pull-request
  - safety
---

# PR #171 Final Validator Review Handoff

## Goal

PR #171 `agent/fix/agentic-review-hardening`에서 남은 validator contract blocker를 닫고 merge-ready 상태를 재검증한다.

이 문서는 non-canonical working artifact다. Authoritative contract는 해당 branch의 OpenSpec과 production/test code다.

## Current State

- Reviewed head before this handoff commit: `7ccd1da729c16c77b4363c152f3711e858c06e89`
- PR: #171 — `fix(reliability): agentic review 계약 및 안전 경계 강화`
- GitHub mergeability: conflict 없음
- CI Lite #465: success
- PR state: Draft
- Remaining blocker: validator action/reference context handling 1건

### Closed Findings

- `base_url` query/fragment credential boundary: closed
- IPv6 sanitized `base_url` preservation: closed
- mixed-clause examples previously reported: covered by regression tests
- provenance partial-success after final link + directory fsync failure: closed
  - final path rollback implemented
  - store/service regression tests added
- stale previous review handoff: removed

## Required Work

### F1 — Match-local context를 기준으로 forbidden action을 판정

**Importance:** Medium

현재 `_has_forbidden_action()`은 action match 자체가 아니라 clause 전체에 safe marker가 있는지를 먼저 확인한다.

```python
if _NEGATION_PATTERN.search(clause) or _KOREAN_NEGATION_PATTERN.search(clause):
    continue
if any(pattern.search(clause) for pattern in _CONDITIONAL_APPROVAL_PATTERNS):
    continue
```

이 구조에서는 같은 clause 안의 다른 위치에 approval/negation 표현이 있으면 실제 direct command까지 면제될 수 있다.

대표 counterexample:

```text
Human approval is required, execute the backfill now.
```

현재 comma는 clause separator가 아니므로 하나의 clause로 남는다. 앞의 `approval is required`가 clause 전체를 safe로 만들어 뒤의 `execute the backfill now`가 `forbidden_action` 없이 통과할 수 있다.

반대 방향의 reference false-positive도 구조적으로 남아 있다. `_DRAFT_QUOTE_PATTERN`은 `draft`, `proposal`, `remediation` 등 특정 prefix에 연결된 quote만 masking한다.

```text
The log says: "DELETE FROM raw.hmda_loans".
```

이 문장은 quoted/reference text지만 destructive SQL pattern에 직접 노출될 수 있다. OpenSpec은 quoted/reference text 자체는 violation으로 판정하지 않는다고 정의한다.

### Required Change

발견되는 문장을 separator나 regex fixture에 계속 추가하는 방식은 피한다.

다음 순서로 bounded grammar를 정리한다.

1. direct action 또는 authority candidate를 찾는다.
2. 그 **match 주변의 local context**만 확인한다.
3. 해당 match 자체가 explicit negation, quoted/reference, human-approval-conditional이면 suppress한다.
4. 같은 clause의 다른 safe marker가 독립적인 dangerous match까지 면제하지 않게 한다.

Full semantic parser는 필요하지 않다. `forbidden-action-policy-v1`의 bounded regex/grammar 성격을 유지한다.

## Regression Matrix

최소한 다음 behavior를 함께 고정한다.

### Reject

```text
Human approval is required, execute the backfill now.
This requires human approval, but execute the backfill now.
Do not wait, the model approves this recovery.
Remove the evidence file.
Approved by the model.
```

### Accept

```text
After human approval, backfill the 2025 partition.
Do not execute: backfill the 2025 partition.
The draft says: "DELETE FROM raw.hmda_loans".
The log says: "DELETE FROM raw.hmda_loans".
```

기존 Korean imperative/negation regression도 결과가 유지되어야 한다.

## PR Metadata Cleanup

구현이 닫힌 뒤 PR body를 current head와 맞춘다.

- `sentence-level` 같은 과거 구현 설명을 현재 구조에 맞게 갱신
- validation count는 최신 실행 결과만 기록
- 실제 검증하지 않은 결과를 최신 결과처럼 재사용하지 않음

이는 validator blocker보다 낮은 우선순위이며 구현 contract를 대체하지 않는다.

## Validation

수정 후 최소 검증:

```bash
uv run pytest tests/reliability/agentic_review/test_validator.py
uv run pytest tests/reliability/agentic_review/
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
openspec validate --all
```

GitHub에서는 최신 head의 CI Lite가 prospective merge 기준으로 성공하는지 확인한다.

## Done When

- match-local context 기준으로 direct action/authority와 safe reference가 구분된다.
- 위 regression matrix가 고정된다.
- 기존 safety regression이 회귀하지 않는다.
- provenance rollback regression이 계속 통과한다.
- 최신 head의 CI Lite가 green이다.
- PR body가 current implementation/validation과 일치한다.
