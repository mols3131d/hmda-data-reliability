---
type: plan
title: "MVP Proof Execution Control"
description: "인계된 PR #239의 Research, Plan, Work, Review와 exact-revision evidence 기록 경계를 고정한다."
---

# MVP Proof Execution Control

## Active Scope

- **Goal:** `docs/mvp.md`의 여섯 acceptance를 같은 clean revision에서 실행하고 근거에 따라 판정한다.
- **Owner:** PR #239, remote `mols/test/prove-current-revision-mvp-e2e`; local checkout branch의 `-2` suffix는 별도 work unit을 만들지 않는다.
- **In Scope:** 기존 executable proof, evidence 보존·검증, direct contract failure의 최소 remediation.
- **Out of Scope:** 새 capability/dependency/architecture, production mutation, autonomous approval, merge 또는 Ready 전환.
- **Acceptance:** 여섯 항목 모두 `PASS`일 때만 MVP 완료. `FAIL`/`BLOCKED`와 미검증을 숨기지 않는다.

## Prepare

`READY WITH LIMITS`: locked environment 설치 완료, provider 설정 미제공. Existing proposal/checklist와 [Research](02-research-project-mvp-proof-readiness.md)를 입력으로 사용한다. Outer controller는 `mols-loops`, ceiling은 30, intensity는 standard다. Implementation defect가 실제로 재현되어 OpenSpec Apply에 들어가면 `prj-spec-driven-tdd-rpi`가 해당 implementation lifecycle을 소유한다.

## Plan

1. OpenSpec `data-operations-prove-current-revision-mvp`의 spec-free preparation 산출물을 검증한다. 새로운 Requirement나 canonical Spec 변경은 만들지 않는다.
1. Checklist의 live success 및 revision-recording ambiguity를 해소하고 independent planning review를 반영한다.
1. 모든 tracked 준비 변경을 commit하고 exact SHA를 고정한다. `.local/pr239/proofs/<SHA>/`에 environment, command, timestamp, exit code, pytest JUnit/log와 basetemp evidence를 보존한다.
1. `uv run pytest` default baseline을 먼저 실행한다. Default의 `not memory and not stress` 제외를 보고하고 full-resource coverage로 표현하지 않는다.
1. Baseline에서 실행된 recovery/Airflow/Review AI/Runtime AI tests를 acceptance와 연결하고 persisted state를 확인한다. 성공 후 focused suite를 같은 SHA에서 다시 실행하여 reproducibility를 비교한다.
1. Provider 설정이 제공되면 deterministic baseline 통과 이후 existing live script를 opt-in 실행하고 persisted provenance를 대조한다. 미제공이면 live `BLOCKED`; 전체 reproducibility 중 live evidence 보존 부분도 완료로 처리하지 않는다.
1. Independent review를 `review-lead`에 위임한다. Lead가 quality/adversarial을 분리 검토하며 caller는 reconciliation을 반영한다. 결과와 runtime evidence를 PR에 연결하고 Draft 상태로 전달한다.

## Evidence Contract

Runtime record는 proof SHA, clean tracked state, environment versions, command/exit/timing, JUnit counts, retained test artifacts, acceptance mapping, limitation을 포함한다. Airflow fixture는 teardown에서 임시 directory를 삭제하므로 ignored observer plugin이 call 종료 후 teardown 전에 SQLite state를 read-only 조회하고 test runtime 파일을 proof root에 복사한다. Fixture, production function, assertion, result와 cleanup을 대체하지 않는다. Observer source와 digest를 실행 evidence에 보존하고 capture failure는 acceptance gap으로 처리한다. Credential과 raw provider response/log는 게시하지 않는다. Local evidence는 이 workspace에만 존재한다는 한계를 명시하고 PR에는 검토 가능한 요약과 digest를 남긴다.

실행 후 tracked file을 변경하면 이전 proof를 historical로 보존하고 최종 SHA에서 baseline, focused rerun과 live invocation을 포함한 여섯 acceptance 근거를 모두 다시 확보한다. 영향받는 proof만의 재실행은 중간 진단에 한정한다. Result를 기록하기 위해 tracked preparation의 checklist나 OpenSpec Tasks를 계속 수정하지 않는다. OpenSpec Tasks는 preparation deliverable만 소유하며 runtime acceptance 완료 여부는 소유하지 않는다.

## Loop State

- **Phase:** RPI Main Loop
- **Loop:** 0/30
- **Research:** readiness artifact 완료
- **Plan:** 이 문서와 OpenSpec preparation artifacts
- **Work:** 준비 변경 및 실행 대기
- **Acceptance:** open
- **Material gaps:** runtime proof 미실행, live provider 설정 미제공
- **Next:** preparation review 후 clean revision 실행

후속 Review/Finalize 결과는 proof directory의 `review.md`와 PR metadata에 기록한다. Tracked control record는 실행 전 계획이며 current completion dashboard가 아니다.
