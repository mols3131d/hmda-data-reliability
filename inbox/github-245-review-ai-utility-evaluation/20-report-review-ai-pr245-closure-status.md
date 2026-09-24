---
type: report
title: "PR #245 Closure Work Status"
description: "PR #245 closure plan에 따른 F1–F3 수정, 로컬 검증 결과, 현재 PR 상태와 미완료 closure gate를 기록합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
  - "closure"
---

# PR #245 Closure Work Status

## Executive Summary

18번 high-confidence review의 F1–F3 correctness 결함을 현재 작업 트리에서 수정하고 회귀 검증했다. Review AI 및 관련 runtime/script 테스트 172개가 통과했으며, 오프라인 utility proof, Python lint/format, Markdown, OpenSpec strict validation도 통과했다.

이 결과만으로 PR #245 closure가 끝난 것은 아니다. 수정은 아직 commit/push되지 않았고, 원격 PR은 Draft 상태로 기존 head `e485a32d6ddc94628fc270794775aad9ed3a5018`을 가리킨다. PR 설명 갱신, exact frozen revision에서의 fresh independent review, readiness assessment와 이후 lifecycle 결정이 남아 있다. 따라서 검증 결과는 원격 PR head가 아니라 현재 로컬 작업 트리에 적용된다.

## Completed Remediation

| Finding | 수정 및 회귀 보호 |
| --- | --- |
| F1 — bounded context overflow | 전용 `ReviewContextTooLargeError`를 추가하고 service가 `INPUT_REJECTED/context_too_large`로 반환하도록 했다. 이 경로에서 provider와 evidence store는 호출하지 않으며 일반 `ValueError`는 넓게 변환하지 않는다. |
| F3 — prompt/validator evidence ID 불일치 | Prompt의 draft `evidence_refs`를 bounded context에서 선택된 evidence ID로 제한해 provider-visible ID와 validator allowlist를 일치시켰다. |
| F2 — durable quality basis 불완전 | `positive`, `restatement_negative`, `hedging_negative` 역할과 기대 결과 `PASS/FAIL/FAIL`을 같은 case/revision에서 검증한다. Proof bundle은 valid basis를 요구하고, comparison은 다섯 rubric criterion의 완전성과 점수 합계 정합성을 확인한다. Store는 쓰기 전에 JSON 왕복 재검증해 `model_copy(update=...)`로 우회된 변조 인스턴스를 거부한다. |

관련 소스와 회귀 테스트는 [Review AI implementation](../../src/hmda_reliability/review_ai/) 및 [utility evaluation tests](../../tests/review_ai/test_utility_evaluation.py)에 있다. OpenSpec delta와 design은 구현된 계약에 맞게 갱신했고, task 6은 원격 PR 설명과 현재 validation 기록이 아직 반영되지 않아 미완료로 유지했다.

## Validation Evidence

| Check | Result |
| --- | --- |
| `uv run python -m pytest tests/review_ai tests/runtime_ai tests/scripts/test_review_ai_utility_proof.py -q` | **172 passed** |
| Offline representative utility proof runner | 성공. 고정 fixture의 proof bundle 생성 및 저장·재로드를 확인했다. |
| Targeted Ruff lint and format checks | 통과; 17개 Python 파일이 이미 format 상태였다. |
| `rumdl check` on existing changed Markdown/OpenSpec files | 통과. 이 보고서 작성 후 20번 보고서와 인덱스를 다시 검사한다. |
| `uv run openspec validate review-ai-utility-evaluation --strict` | 통과 |
| `git diff --check` | 통과 |

테스트와 오프라인 runner는 현재 로컬 작업 트리에서 실행했다. 이들은 결정론적 계약, fixture 및 저장 증적의 무결성을 검증하며 실제 모델 호출이나 사람의 유용성 평가를 대신하지 않는다.

## Current State and Remaining Gates

- 원격 PR #245: `OPEN`, Draft. 원격 head는 `e485a32d6ddc94628fc270794775aad9ed3a5018`, base는 `e2e012d845c797ca9d3df93763bb5b7874083478`이다. 확인 시점에 로컬 `HEAD`는 원격 head와 같았고 `origin/main`과의 merge-base는 base와 같았다.
- 로컬 작업 트리: 구현, 테스트, OpenSpec 및 Inbox 인덱스의 16개 tracked 파일이 수정되어 있고, 이 보고서가 새로 추가된다. 변경 사항은 아직 원격 PR에 게시되지 않았다.
- OpenSpec progress: task 1–5 완료, task 6 미완료. task 6의 PR 설명 갱신 및 validation 기록 조건이 남아 있다.
- Stage 3–4 closure: tracked 작업이 미게시 상태이므로 frozen published candidate가 없다. PR 설명 갱신과 fresh review가 완료되지 않았으며 readiness/merge 판정도 하지 않았다. 별도 review-lead 실행은 diff/status 접근 문제로 `Assessment: blocked`였으므로 독립 검토 통과로 취급하지 않는다.
- Live utility: 실제 provider 호출, live human scoring 및 운영 환경 효용은 검증하지 않았다. Offline fixture의 `accept` 결과는 fixture 계약 검증이지 실제 유용성 승인 근거가 아니다.
- 권한 경계: commit/push, PR Draft 해제, merge는 수행하지 않았다. 다음 단계의 원격 게시와 lifecycle 변경은 사용자 승인을 기다린다.

다음 작업 순서와 gate는 [19번 PR closure plan](19-plan-review-ai-pr245-closure/README.md)을 따른다. 특히 PR 설명과 fresh review는 exact published revision을 기준으로 갱신해야 하며, 수정 사항 게시 후 필요한 validation을 다시 실행해야 한다.
