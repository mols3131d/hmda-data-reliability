---
type: plan
title: PR 231 follow-up F1 F2 hardening
description: PR 231의 ambient Git environment와 cross-scope candidate dedup 회귀를 수정하기 위한 구현 계획입니다.
tags:
  - "domain:software-engineering"
  - "capability:repository-cleanup"
  - "safety"
---

# PR 231 follow-up F1 F2 hardening

## Scope

사용자가 제시한 PR #231 후속 finding F1과 F2만 수정한다. 기존 cleanup target과 보호 경계는 변경하지 않는다.

## Safety contract

| Finding | Change | Observable contract |
| --- | --- | --- |
| F1 | `_load_tracked_index()`가 `GIT_` ambient environment를 제거한 환경에서 `git -C <repo_root> ls-files`를 실행한다. | `GIT_INDEX_FILE` 등 override가 설정되어도 현재 repository의 정상 index에 있는 tracked path가 보호된다. |
| F2 | candidate dedup key와 ancestor suppression을 `candidate.scope`별로 제한한다. | `tmp` candidate가 skip되어도 동일 경로 계층의 `repo` candidate가 보존된다. |

## Regression scenarios

- 정상 repository index에 tracked file이 있고 ambient `GIT_INDEX_FILE`이 빈 alternate index를 가리켜도 cleanup plan이 candidate를 만들지 않는다.
- repository root가 `/tmp/pr123-review/...` 아래 있어 root가 tmp pattern candidate가 되더라도, `scope="all"`에서 내부 `.pytest_cache` repository candidate가 유지된다.

## Validation gates

1. `uv run pytest tests/scripts/test_clean.py`
1. 관련 Ruff, format, type check
1. 변경 diff에서 F1/F2 path와 regression oracle 재검토
1. commit, push 후 Draft PR #231 CI와 head 상태 확인

이 문서는 Inbox working artifact이며 cleanup 구현과 test가 executable contract다.
