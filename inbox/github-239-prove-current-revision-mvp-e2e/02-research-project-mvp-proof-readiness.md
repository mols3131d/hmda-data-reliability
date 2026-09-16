---
type: research
title: "MVP Proof Readiness"
description: "PR #239 인계 시점의 실행 가능성, canonical contract와 evidence gap을 확인한다."
---

# MVP Proof Readiness

> [!IMPORTANT]
> `9332509774262311916a912a342a86d8c6ed0517`에서 기존 executable boundary를 사용할 수 있다. 여섯 acceptance의 실행 증거는 아직 없고 live provider 설정은 미제공이다.

## Question

기존 contract를 변경하지 않고 current-revision MVP proof를 실행할 수 있는가?

## Scope

PR #239의 proposal/checklist, `docs/mvp.md`, 관련 canonical Specs, 기존 pytest 및 live entrypoint, 로컬 실행 환경을 확인했다. 새 capability와 production 데이터 변경은 범위 밖이다.

## Findings

### Existing Entry Points Cover Distinct Boundaries

- `tests/data_operations/test_system_recovery_e2e.py`: real dbt, deterministic incident/recovery/replay 및 rejected/mismatched approval의 zero-mutation oracle.
- `tests/orchestration/test_airflow_dagrun.py`: actual Airflow CLI DAGRun, task/Asset evidence, gate/dbt failure. Scheduler/distributed executor proof는 아니다.
- `tests/review_ai`, `tests/runtime_ai`: evidence/identity/structured-fact validation, invocation provenance 및 advisory authority separation.
- `scripts/run_agentic_review_live.py`: detector와 draft factory가 만든 동일 incident/evidence/draft를 실제 provider에 전달한다. Auto revision은 clean tracked worktree를 요구하며 `accepted`만 exit 0이다.

Canonical owners는 `openspec/specs/data-operations-stage-execution`, `orchestration-pipeline`, `reliability-recovery-backfill`, `reliability-agentic-review`와 `docs/mvp.md`다. 하나의 universal case나 Git SHA 기반 approval authorization을 새로 만들지 않는다.

### Current CI Does Not Establish Runtime Acceptance

[CI Lite run 35089344700](https://github.com/mols3131d/hmda-data-reliability/actions/runs/35089344700)은 Markdown과 Inbox validation만 실행했다. Tests/runtime smoke는 skipped다. 인계 시 local HEAD와 PR head는 일치했고 tracked worktree는 clean이었다.

### Environment Is Partially Ready

`uv sync --locked`가 Python 3.13.13과 lockfile dependency 설치에 성공했다. `.env`가 없고 `HMDA_AGENTIC_REVIEW_LIVE`, `BASE_URL`, `API_KEY`, `MODEL` 환경 변수도 설정되지 않았다. Credential 값은 조회하거나 기록하지 않았다. User에게 provider와 환경 파일 경로를 요청했다.

### Proof Records Must Not Move the Proven Revision

Tracked checklist에 실행 후 SHA와 결과를 채우면 HEAD가 바뀐다. Final execution record는 ignored `.local/pr239/proofs/<SHA>/`와 PR metadata에서 관리한다. Tracked artifacts는 실행 전 준비를 소유하고, 실행 이후 수정 시 새 SHA의 proof로 구분한다.

### Typed Failure Is Diagnostic Evidence

`reliability-agentic-review` Spec은 typed failure 보존을 허용하지만 `docs/mvp.md`의 Live Agentic proof는 실제 structured review 생성을 요구한다. 이 작업은 `accepted`와 검증 가능한 provenance가 있어야 live `PASS`로 판정한다. Provider 환경 문제는 `BLOCKED`, schema/guard contract 위반은 `FAIL`로 기록한다.

## Implications

Active OpenSpec Change가 없으므로 spec-level behavior를 바꾸지 않는 proof preparation Change를 생성한다. 실행 결과는 기존 checklist에 연결하고, 직접 재현된 기존 contract 위반만 최소 remediation으로 검토한다.

## Open Questions

- Live provider의 base URL, model과 credential을 제공할 환경 파일은 무엇인가?
- 실제 baseline과 boundary 실행에서 revision-specific failure가 발생하는가?
