---
type: handoff
title: "PR #171 Review Findings Handoff"
description: "PR #171의 agentic review hardening 변경에서 확인된 safety contract 불일치와 정리 작업을 후속 작업자에게 전달합니다."
tags:
  - reliability
  - agentic-review
  - safety
  - pull-request
---

# PR #171 Review Findings Handoff

## Goal

PR #171 `agent/fix/agentic-review-hardening`을 다시 머지 가능한 상태로 만든다. 이번 handoff는 현재 PR이 해결하려는 safety contract에 직접 연결된 finding과 명백한 변경 오염만 다룬다.

Authoritative contract는 해당 branch의 OpenSpec과 production/test code다. 이 문서는 non-canonical working artifact이며 contract를 대체하지 않는다.

## Current State

- PR: `#171` — `fix(reliability): agentic review 계약 및 안전 경계 강화`
- Reviewed head: `556d4478965d498ed1806fd2b88a7d705ed0d4b2`
- Base: `5ec4085f92190598fee8f1dc032ab9a7e5d78b80`
- GitHub mergeability: conflict 없음
- CI Lite: reviewed head에서 success
- Review verdict: 수정 후 재검토 필요

## Required Work

### F1 — Reject credential-bearing `base_url` query parameters

**Importance:** High

`AgenticReviewSettings._validate_base_url()`은 URL userinfo만 거부한다. 따라서 다음과 같은 query credential은 정상 설정으로 들어간다.

```text
http://localhost:11434/v1?api_key=secret-token&mode=eval
```

`sanitized_configuration()`에서 이를 redaction해 저장 leakage는 줄이지만, `OpenAICompatibleAdapter`에는 원래 `settings.base_url`이 그대로 전달된다. OpenSpec은 `base_url`을 credentials-free configuration으로 정의하므로 현재 구현과 contract가 일치하지 않는다.

**Required change**

- `AgenticReviewSettings` 입력 경계에서 known sensitive query key를 가진 `base_url`을 reject한다.
- 저장 시 redaction은 defense-in-depth로 유지해도 된다.
- userinfo와 sensitive query credential 각각에 regression test를 둔다.
- Spec wording과 implementation이 동일한 invariant를 표현하는지 다시 확인한다.

### F2 — Preserve safe advisory/reference language in forbidden-action policy

**Importance:** Medium

새 forbidden-action regex 중 다음 계열은 마지막 `now|immediately`가 optional이라 명령이 아닌 설명도 잡을 수 있다.

```text
Backfill the 2025 partition after human approval.
Backfill the 2025 partition requires human approval.
```

OpenSpec은 draft action을 인용하거나 backfill을 human approval이 필요한 항목으로 설명하는 것은 violation이 아니라고 명시한다. 따라서 direct imperative와 safe advisory/reference를 구분해야 한다.

**Required change**

- imperative/execution command만 잡도록 overly broad pattern을 좁힌다.
- positive regression뿐 아니라 다음 negative cases를 추가한다.
  - human approval이 필요하다고 설명하는 문장
  - proposed/draft action을 인용하는 문장
  - 실행을 권한 없이 주장하지 않는 analysis 문장
- `forbidden-action-policy-v1`이 bounded heuristic임은 유지하되 false positive로 정상 advisory result가 reject되지 않게 한다.

### F3 — Align cleanup failure semantics across Design, implementation and tests

**Importance:** Medium

`design.md`는 persistence 과정의 filesystem failure에 cleanup까지 포함해 `InvocationEvidenceStoreError`로 정규화한다고 적었다. 반면 구현은 cleanup의 `OSError`를 `contextlib.suppress(OSError)`로 무시하고, 새 test도 temporary-file unlink failure 후 성공을 기대한다.

현재 상태는 Design과 implementation/test가 서로 다른 contract를 가진다.

**Preferred resolution**

Durable final record가 link되고 directory fsync까지 성공한 뒤의 temporary cleanup 실패는 provenance 자체를 잃은 상태가 아니다. 따라서 cleanup을 best-effort hygiene로 명시하고, `design.md`의 "cleanup을 포함한 모든 filesystem failure" 표현을 좁히는 편이 현재 구현과 fail-closed 목적에 더 정확하다.

다른 semantics를 선택한다면 implementation과 tests까지 함께 맞춰야 한다. 어느 쪽이든 세 artifact가 같은 observable contract를 가져야 한다.

### F4 — Preserve IPv6 authority when sanitizing `base_url`

**Importance:** Medium

`_sanitize_base_url()`은 `parsed.hostname`으로 `netloc`을 재조립한다. IPv6 literal은 bracket이 필요한데 현재 방식은 이를 잃는다.

```text
http://[::1]:11434/v1
```

이 URL을 재조립하면 `http://::1:11434/v1` 형태가 될 수 있어 sanitized configuration이 malformed된다. Local OpenAI-compatible endpoint에서 IPv6 loopback은 유효한 입력이다.

**Required change**

- validated authority를 불필요하게 수작업 재조립하지 않는다.
- userinfo는 입력 validator에서 거부하고, query redaction만 필요한 구조를 선호한다.
- IPv6 host + port + path를 보존하는 regression test를 추가한다.

### F5 — Remove accidental root test artifacts

**Importance:** Low

PR diff에 다음 unrelated root files가 포함돼 있다.

- `file.txt` → `hello`
- `tracked.txt` → `v1`

`tests/hmda_data/eda/test_eda_evidence.py`가 temporary git repository에서 만드는 fixture 이름과 내용에 대응하므로 테스트 과정에서 유입된 변경으로 보인다.

**Required change**

- 두 파일을 PR에서 제거한다.
- 다른 unrelated root artifact가 없는지 changed-file list를 한 번 더 확인한다.

## Validation

수정 후 최소한 다음을 다시 확인한다.

1. `uv run pytest tests/reliability/agentic_review/`
2. `uv run pytest tests/hmda_data/eda/test_eda_evidence.py`
3. `openspec validate --all`
4. `uv run ruff check src tests scripts`
5. `uv run ruff format --check src tests scripts`
6. PR changed-file list에 `file.txt`, `tracked.txt`가 남지 않았는지 확인
7. GitHub CI Lite가 새 head에서 성공하는지 확인

전체 suite는 focused validation 결과나 변경 범위가 필요성을 보여줄 때 실행한다. 기존 PR 본문의 pass count는 새 head 검증으로 재사용하지 않는다.

## Done When

- F1~F4의 contract/implementation/test 정합성이 닫힌다.
- F5의 accidental artifacts가 제거된다.
- OpenSpec과 tests가 선택한 semantics를 동일하게 표현한다.
- 새 head의 실제 validation evidence가 확보된다.
- 이후 PR #171을 다시 review한다.
