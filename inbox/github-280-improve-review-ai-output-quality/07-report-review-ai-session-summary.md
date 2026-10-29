---
type: report
title: Review AI Session Summary
description: 이번 채팅에서 진행한 Review AI 개편, 실행 결과와 남은 확인 사항을 간결하게 정리합니다.
---

# Review AI Session Summary

작성일: 2026-10-29. 구현 기준: `a6d299e64596de88487e1708acabbba992a0f7e0`. [PR #280](https://github.com/mols3131d/hmda-data-reliability/pull/280)은 Draft 상태다.

**합성 컨텍스트를 모델에 전달해 검토 답변을 확인하는 실험 경로를 개편했다. 모델은 한국어 텍스트로 단계별 답변을 만들고, 결과 JSON은 코드가 생성한다.** 이 실행은 실제 HMDA 데이터를 적재하지 않는다.

## Completed Work

| Area | Result |
| --- | --- |
| 실패 원인 조사 | JSON 파싱·출력 계약 실패와 사실 검증 실패를 구분했다. 호출 기록만으로는 원래 답변을 확인할 수 없던 문제를 확인했다. |
| 응답 원문 보존 | Runtime이 반환한 bounded 본문을 검증 전에 UTF-8 그대로 저장한다. 검증 실패·늦은 응답도 보존하며, 본문 없는 네트워크 실패에는 원문이 없다. |
| 프롬프트 정리 | 단일 Python 파일의 지시문을 [prompt/](../../src/hmda_reliability/review_ai/prompt/)의 한국어 Markdown으로 옮기고 작업·언어·자문 정책·출력·지침·예시·단계 질문으로 나눴다. 언어 정책 이름은 `language.md`로 통일했다. |
| 조립·재사용 규칙 | 모듈을 고정 순서로 조립하고 사례 데이터와 분리한다. OpenSpec과 개발 가이드에 책임·재사용 전제 및 검증·채택 후 기본 조합을 하나로 통일하는 원칙을 명문화했다. 기존 `v1~v3`는 structured 비교·재현용으로 보존한다. |
| 단계별 실행 | 같은 원입력과 이전 답변을 유지해 **근거 검토 → 초안 비판 → 종합**을 수행한다. 모델에 JSON 생성을 요구하지 않고 코드가 원입력 facts와 세 원문을 취합한다. 기본 live 모드는 `staged`, 기존 방식은 명시적 `structured`로 제공한다. |
| 환경 설정 | 로컬 `.env`와 예제를 정리하고 연결·읽기 대기, 단계·전체 시간 예산을 분리했다. timeout·연결 오류·예산 소진을 구분하고 실제 시도 수와 경과 시간을 기록한다. |

로컬 설정은 **연결 10초 / 읽기 대기 300초 / 단계 예산 360초 / 전체 예산 1,200초 / 추가 재시도 0회**다. 예산은 후속 호출과 성공 채택을 제한하며 진행 중 동기 요청을 강제 종료하지 않는다.

## Verification And Delivery

- 최종 구현의 Review AI/Runtime AI 회귀: **400 passed, 1 skipped**. 생략은 선택적 Langfuse SDK 테스트다.
- Pre-push: **228 passed, 49 deselected**. OpenSpec strict: **31 passed, 0 failed**. 정적·문서·패키지 검증도 통과했다.
- 주요 커밋 `7f74310a` → `77761a75` → `fa064505` → `a6d299e6`을 푸시했고 원격 HEAD와 PR 설명을 갱신했다. 이 요약 보고서는 그 이후 작성했다.

## Actual Model Runs

| Run | Observed Result | Limit |
| --- | --- | --- |
| `ar-20261028-4fa304794462` | 기존 structured v3 실행에서 `accepted`, 약 92.4초·1회 호출 | `local-korean-prompt-worktree`의 로컬 실험이다. 최종 commit의 staged 성공이나 사람의 품질 평가를 증명하지 않는다. |
| `sr-20261028-6543e4292f04` | staged 첫 요청이 `unavailable / provider_connection_error`로 종료. 본문 없이 1회 호출 | 당시 60초 제한의 실패 기록이다. 새 시간 설정으로 재실행하지 않았으며 과거 실패를 새 timeout 코드로 소급 분류하지 않는다. |

## Remaining Checks

새 설정으로 실제 모델의 세 단계 완료·저장 결과를 확인하고, 같은 사례에서 답변의 사실성·유용성·지연시간을 사람이 평가해야 한다. `completed`는 수집·저장 완료를 뜻한다. 현재 구현 commit의 hosted CI는 이번 작업에서 확인하지 않았다.

## Run And Read

```bash
uv run --env-file .env python scripts/run_agentic_review_live.py
```

`output_path`는 코드가 취합한 결과 JSON, `workflow_path`는 실행 기록, 각 단계의 `response_path`는 모델 원문을 가리킨다. 부분 실패 시 이전 원문·checkpoint를 확인한다.

상세 내용은 [프롬프트·실행 설정 가이드](../../docs/development/review-ai-prompts.md), [단계 실행 보고서](05-report-review-ai-staged-text-delivery.md), [시간 예산 보고서](06-report-review-ai-execution-budgets.md)에 정리했다.
