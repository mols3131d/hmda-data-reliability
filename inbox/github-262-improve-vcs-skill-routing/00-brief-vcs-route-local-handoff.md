---
type: brief
title: "PR 262 Local Continuation"
description: "PR #262의 라우팅 인덱스 갱신과 CI 복구를 위한 로컬 에이전트 인계."
---

# PR 262 Local Continuation

**Target:** [PR #262](https://github.com/mols3131d/hmda-data-reliability/pull/262), `agent/chore/improve-vcs-skill-routing` (인계 전 head: `9b8dbd9e10c2be91babe68b7c856e86f1ab6372c`).

**Current:** `.rulesync/skills/prj-vcs-git-github/SKILL.md`의 활성화 조건·문서 선택 경로는 수정됨. `.agents/route/skills.jsonl`은 미갱신. [CI Lite](https://github.com/mols3131d/hmda-data-reliability/actions/runs/39115311335)는 `Skills CLI hash mismatch: langfuse; upstream snapshot differs from lock` (exit 2)로 인덱스 drift 검사 전에 중단됨.

## Next Actions

1. PR 최신 head·base와 변경 범위를 재확인한다.
2. `langfuse` lock 불일치 원인을 확인하고 **관리 도구의 정상 경로**로 해결한다. `skills-lock.json` 수동 편집 금지. 외부 의존성 갱신으로 범위가 확대된다면 별도 승인을 받는다.
3. `uv run python -m scripts.agent_routes`로 인덱스를 생성하고 `uv run python -m scripts.agent_routes --check`로 검증한다. 생성 JSONL을 직접 편집하지 않는다.
4. 의도한 diff만 남았는지 확인하고 CI를 재실행한 뒤 PR validation과 readiness를 갱신한다.

**Boundary:** 기존 VCS 정책·생성기 변경은 범위 밖이다. Ready 전환·merge는 별도 명시적 요청 없이 수행하지 않는다.
