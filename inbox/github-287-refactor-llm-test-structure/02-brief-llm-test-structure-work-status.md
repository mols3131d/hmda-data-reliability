---
type: brief
title: PR 287 LLM Test Structure Work Status
description: "PR #287의 오프라인 AI 테스트 경계, 검증 근거와 세션 재개 지점을 기록한다."
tags:
  - testing
  - llmops
  - ci
---

# PR 287 LLM Test Structure Work Status

2026-11-18 KST 기준 기본 AI pytest의 오프라인 경계를 실행 중에 검증하도록 보강했다. PR #287은 Draft다. 원격 head, 검증 상태와 검토 준비도는 PR 본문을 확인한다. [PR #287](https://github.com/mols3131d/hmda-data-reliability/pull/287)

## Branch And Evidence

| 항목 | 확인한 상태 |
| --- | --- |
| 작업 브랜치 | `agent/test/refactor-llm-test-structure` |
| 동기화 전 PR head | `fc2d581ccb3d3282413889c6a5c0807fe6e18dbb` |
| 동기화 대상 `main` | `a326d8d9cfb8c7cc477e46b3df67c05e62d093dc` |
| 동기화 전 분기점 | `7efb332c2efd78f77ee724440e28285ebb3ee55f`. 양쪽에 각 3개 커밋이 있었다. |
| `main` 반영 | GitHub에서 충돌 없이 병합했다. 병합 커밋 `7339f7cb68e74d5e7c4e468683b7391cd6030689`의 부모는 기존 PR head와 동기화 대상 `main`이다. |
| 조사 기준 | `2dc27b0d2bb4c415355e1fe53e2e23909a3f17ca`. 이 시점의 PR diff에는 Inbox 문서 3개가 있었다. |

조사 기준의 CI Lite `44265756735`는 문서 변경 분류까지 통과했고 pytest는 건너뛰었다. [이전 CI Lite 실행](https://github.com/mols3131d/hmda-data-reliability/actions/runs/44265756735)

## Current Test Boundaries

- `tests/reliability_ai`와 `tests/runtime_ai`의 현재 사례는 `ScriptedTransport`, 실제 SDK와 `httpx.MockTransport`, Langfuse client 대역 또는 메모리 exporter를 사용한다. 로컬 DuckDB를 쓰는 위임 테스트에도 모의 모델 전송이 주입된다. 조사 기준에서 두 디렉터리의 253개 테스트가 통과했고, 수집과 실행 중 임시 Python audit hook에서 DNS 또는 외부 연결 시도가 관찰되지 않았다. [SDK provider 회귀](../../tests/runtime_ai/test_provider.py), [Langfuse 실험 테스트](../../tests/reliability_ai/test_experiment_runner.py), [위임 실행 테스트](../../tests/reliability_ai/test_execution_service.py)
- 실제 로컬·원격 모델과 원격 Langfuse 실행은 명시적으로 호출하는 `evaluation.experiment`와 `evaluation.setup` CLI가 소유한다. 현재 pytest에서 옮길 실호출 사례가 없어 신규 live·paid marker, 별도 결제 opt-in, CI 필터 변경은 채택하지 않았다. 로컬과 CI의 기본 제외 marker는 `memory`와 `stress`다. [Reliability AI Evaluation](../../docs/development/review-ai-evaluation.md), [테스트 선택 설정](../../pyproject.toml), [CI 실행기](../../scripts/ci/run_checks.py)
- 기본 AI pytest에서는 CPython audit event로 감지한 socket 주소 조회와 IPv4·IPv6 연결을 차단한다. SDK가 오류를 처리하거나 pytest가 `skip`·`xfail`로 분류해도 감지된 시도는 테스트 실패로 보고한다. 검증 범위는 두 AI 디렉터리의 pytest 항목 실행이다. Native 라이브러리의 DNS 해석, import·수집, 별도 프로세스와 실제 원격 CLI는 범위 밖이다. [네트워크 차단](../../tests/conftest.py), [회귀 테스트](../../tests/test_ai_network_guard.py)

## Validation And Resume

- 변경 후보에서 두 AI suite, 네트워크 차단 회귀, CI pytest·Python 분류 계약을 xdist 2개 worker로 실행해 330개 통과를 확인했다. Ruff, 전체 `ty check`, 변경한 테스트 가이드의 Markdown 검사도 통과했다.
- 초기 독립 검토에서 `skip`·`xfail`을 통한 실패 누락과 수집 때 가져온 socket 함수의 차단 우회를 수정했다. `7aec7be0`의 두 관점 재검토는 `clear`였고 당시 CI Lite에서 `1225 passed, 2 skipped`를 확인했다. [이전 CI Lite 실행](https://github.com/mols3131d/hmda-data-reliability/actions/runs/44272773892)
- 초기 후보의 로컬 전체 pytest에서 Git 서명 키, 읽기 전용 도구 저장 경로, 소켓 제한과 Airflow 타임아웃도 확인했다. 현 후보 전체 통과 여부는 GitHub CI 결과를 기준으로 확인한다.
- 공유 `tests/conftest.py`가 변경됐으므로 CI 분류기는 full pytest를 선택한다. 재개 시 PR base/head와 연결된 prospective merge에서 `Run selected tests`의 실제 결과를 확인한다. [CI 분류기](../../scripts/ci/classify_changes.py), [PR #287](https://github.com/mols3131d/hmda-data-reliability/pull/287)
- 실제 LLM·Langfuse 호출, 원격 수집 및 사람 평가는 수행하지 않았다. 이후 실제 호출이 필요한 새 테스트를 제안하면 그 사례를 기준으로 실행 위치, 명시 선택과 예산을 검토한다.

초기 제안과 기존 Review AI 경로에서 변경된 사항은 조사와 인계에 보존돼 있다. [Original Research](00-research-review-ai-llm-test-structure.md), [Main Alignment Handoff](01-brief-llm-test-structure-main-alignment-handoff.md)

## Review Follow-Up

`7aec7be0`을 대상으로 한 후속 리뷰의 F1·F2를 재현하고 수용했다. 혼합 suite의 공유 session fixture 정리 시점은 리뷰 문서에 후속 관찰로 남겨 두었다. 현재 적용 범위는 pytest 항목의 실행이다. [Independent Review](03-review-ai-offline-network-guard.md)

- **F1**은 하위 pytest의 실패 여부와 별도로 주소 조회나 연결 시도가 차단 예외를 받았는지 확인한다. 차단 예외 한 줄을 제거한 사본에서는 차단 사례 5개가 실패하고 허용 대조군 2개가 통과했다.
- **F2**는 `--export-traces`에서 pytest가 새로 구성한 provider의 OTLP/HTTP exporter 전송을 허용한다. 같은 실행의 AI 작업 스레드는 차단된다. 독립 재검토에서 pytest 진입 전에 설치된 provider의 전송까지 허용되는 경우를 발견해 provider 식별 조건을 좁히고 회귀 검증을 추가했다.
- 최종 독립 재검토는 `clear`였다. AI suite·차단 회귀·pytest OpenTelemetry·CI 선택 계약은 xdist 2개 worker에서 `335 passed`였고 Ruff, 전체 타입 검사, Markdown·Inbox 검사도 통과했다. 실제 collector, LLM·Langfuse 및 OTLP/gRPC는 실행하지 않았다. 게시된 head의 전체 CI와 검토 상태는 PR 본문에서 확인한다. [PR #287](https://github.com/mols3131d/hmda-data-reliability/pull/287)
