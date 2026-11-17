---
type: brief
title: PR 287 Main-Aligned LLM Test Structure Handoff
description: 최신 main의 Reliability AI 리팩토링을 먼저 검토하고 PR 287의 테스트 구조 변경 계획을 재수립하도록 로컬 작업자에게 인계한다.
tags:
  - testing
  - llmops
  - ci
  - handoff
---

# PR 287 Main-Aligned LLM Test Structure Handoff

> [!IMPORTANT]
> **우선 작업은 최신 `main`과의 차이를 검증하고 구현 계획을 다시 세우는 것이다.** 과거 조사 보고서의 파일 경로·테스트 사례·marker 제안을 그대로 구현하지 않는다. PR #287의 완료 목표는 **LLM 테스트 구조 변경 및 검증**이며, 보고서 작성만으로 완료하지 않는다.

## Goal And Scope

- 대상: [PR #287](https://github.com/mols3131d/hmda-data-reliability/pull/287), 작업 브랜치 `agent/test/refactor-llm-test-structure`.
- 목표: 기본 pytest와 PR CI에서 실제 LLM·원격 서비스·유료 호출을 의도하지 않게 실행하지 않으면서, 기존 deterministic fake·실제 SDK/모의 HTTP의 회귀 검증을 보존한다.
- 이번 인계의 **첫 산출물은 최신 `main` 기준 조사와 실현 가능한 구현 계획**이다. 계획을 현재 소스·테스트·CI 계약에 대조한 뒤 승인된 PR 범위에서 구현·검증을 진행한다.
- 운영 모델·프롬프트 교체, 신규 provider 가입/secret, Langfuse-native 품질 평가 대체, 무관한 테스트/아키텍처 변경은 범위 밖이다.

## State Basis And Freshness

- 확인 시점: **2026-11-17 (KST)**.
- 확인 당시 `main`: `a326d8d9cfb8c7cc477e46b3df67c05e62d093dc`.
- 확인 당시 PR head: `9c9a83f60ec4209d76e0b78a4ab8017fe50551f4` (Open / Draft, 기존 변경은 조사 Markdown 1개).
- [기존 조사](00-research-review-ai-llm-test-structure.md)는 `main`의 `7efb332c2efd78f77ee724440e28285ebb3ee55f`를 기준으로 했다. **현재 설계·구현의 정본이 아니라 재검증 대상**이다.
- 작업 재개 시 `main`·PR head·local working tree·관련 commit/diff를 다시 확인한다. 이 문서의 SHA는 검토한 스냅샷이지 미래 상태 보증이 아니다. Branch 반영 방식은 충돌·소유권을 먼저 판단하고 repository VCS 절차를 따른다. History rewrite 또는 임의 merge는 별도 승인 없이 진행하지 않는다.

## Verified Architectural Delta

| 기존 조사에서 가정한 경계 | 현재 `main`에서 확인한 경계 | 계획에 미치는 영향 |
| --- | --- | --- |
| `src/hmda_reliability/review_ai/`, `tests/review_ai/` | `src/hmda_reliability/reliability_ai/`, `tests/reliability_ai/` | 이전 경로·staged 테스트에 대한 구현 지시를 폐기하고 현재 공개 계약을 기준으로 다시 분류 |
| Staged review service | `reliability_ai/investigation/`, `execution/`, `evaluation/` | 조사·위임 실행·실험의 각 외부 호출 및 테스트 책임을 별도로 추적 |
| 이전 Langfuse 평가 예시 | `reliability_ai/evaluation/experiment.py`와 `tests/reliability_ai/test_experiment_runner.py` | 실제 Dataset 실험은 명시적 별도 실행; pytest의 모의 SDK 계약 검증과 혼동 금지 |
| 기존 Provider 검증 | `runtime_ai/provider.py`, `tests/runtime_ai/test_provider.py`, `test_provider_tools.py` | injected transport / `httpx.MockTransport` 경계를 보존하고 실제 SDK 생성·호출 경로를 구분 |
| 기존 CI 선택 규칙 | `scripts/ci/run_checks.py`, `classify_changes.py`, `tests/scripts/ci/test_ci_pytest.py` | full/scoped 필터·변경 영향 분류·boundary 검증 재사용 조건을 함께 점검 |

정적 확인: `tests/reliability_ai/conftest.py`는 native Prompt client를 fixture로 대체하고, 조사/Provider 테스트는 `ScriptedTransport` 또는 `httpx.MockTransport`를 사용한다. `pyproject.toml`과 CI pytest 실행자는 아직 `memory`, `stress`만 기본 제외한다. **전체 테스트 수집·실행·외부 요청 관찰은 수행하지 않았다.** 일부 테스트가 실제 원격 호출을 수행하는지는 추가 확인이 필요하다.

## Next Actions For Local Agent

1. **Rebase assumptions, not history.** 최신 `main`의 canonical architecture·testing·CI 문서, spec, 실제 코드와 현재 PR head를 확인한다. 기존 조사에서 살아남는 사실·폐기할 경로·새로운 위험을 근거와 함께 정리한다. 이 인계를 무조건 수용하지 않고 틀린 가정은 버린다.
2. **Inventory actual execution boundaries.** `tests/reliability_ai`, `tests/runtime_ai`, 연결된 `tests/scripts/ci`와 fixture를 collection 및 정적 추적으로 분류한다. 각 호출에 대해 **offline fake**, **real SDK + mocked HTTP**, **local live model**, **remote service**, **potentially paid provider**를 구분하고, 실제 network 가능 경로·호출 주체·현재 차단 조건을 기록한다. `integration`이라는 이유만으로 live로 분류하지 않는다.
3. **Decide the minimum contract.** `unit`/`component`/`integration` 수준과 `memory`/`stress` 자원 marker는 유지한다. 신규 `llm_live`, `llm_paid`, `service_live`는 **사용 사례와 safety gap이 확인된 경우에만** 도입한다. 특히 현재 live pytest 사례가 없다면 marker만 미리 늘리는 접근을 재검토한다. 직접 node 실행·`-m` 재정의·잘못 분류된 테스트에서 marker만으로 비용을 막을 수 없다는 점을 검증한다.
4. **Design testable guards and CI routing.** 실제 호출을 허용하는 경우 기본 거부, 명시적인 opt-in, provider/endpoint 허용 범위, 비용·재시도·timeout 상한, credential 누락 및 거부 시 관찰 가능한 실패를 정의한다. Production Provider 계약이나 기존 모의 HTTP 검증을 깨뜨리는 전역 socket 차단·무조건 skip은 피한다. 필요하면 `pyproject.toml`, `scripts/ci/run_checks.py`, `tests/scripts/ci/test_ci_pytest.py`, `classify_changes.py`를 **서로 일관된 한 변경 단위**로 계획한다.
5. **Plan verification before implementation.** 최소 정상·부정 경로 테스트, 기존 SDK/모의 전송 회귀, full/scoped 선택 계약, change-impact fail-safe, `main`과의 prospective merge 검증을 매핑한다. 실제 LLM·Langfuse 실험과 사람 평가는 별도 evidence tier이며 pytest PASS로 대신하지 않는다. 외부·유료 호출은 별도 권한과 준비된 안전 경계 없이 실행하지 않는다.
6. **Document the decision and then proceed.** 현재 증거, 선택한 구조, 변경 예정 파일, 제외할 제안, acceptance와 미확인 사항을 PR 소유 작업 문서에 정리하고 실제 구현 전 검토한다. 구현 뒤 focused → 관련 domain → CI contract → 필요한 prospective merge 검증 결과를 revision과 함께 기록하고 PR 설명·readiness를 다시 판단한다.

## Acceptance And Questions

- 기본 pytest / scoped·full CI / 직접 test 실행에서 **의도하지 않은 실제 provider 또는 원격 Langfuse 호출이 없어야 한다**. Marker 필터 통과와 실제 호출 차단은 다른 주장이다.
- 기존 OpenAI SDK+모의 HTTP, Langfuse SDK mock, 조사·도구·위임 실행의 회귀 검증을 기본 suite에 보존한다.
- 실호출을 설계한다면 명시적 opt-in 및 실패·누락·한도 초과의 negative path를 재현 가능한 oracle로 검증한다. 테스트 실패를 skip이나 broad mock으로 숨기지 않는다.
- CI는 `main` 입장에 필요한 검증을 pre-merge에서 유지하고, 변경 영향이 불분명할 때 범위를 넓히거나 실패한다. CI selector만 통과한 것을 domain runtime PASS로 표현하지 않는다.
- 미확인 질문: 실제 live pytest case가 존재하는가? 유료 smoke가 현재 필요한가? live 검증이 merge-critical인 계약은 무엇인가? Mock 실행이 실제 호출을 차단한다고 어떤 관찰로 증명할 것인가?
- 종료 조건: 최신 `main` 기반 계획과 검증 가능한 acceptance가 확보되고, 구현·검증이 완료된 경우에만 review readiness를 재평가한다. Draft 해제·승인·병합은 별도 권한 판단을 따른다.

## Reference Owners

- [PR #287](https://github.com/mols3131d/hmda-data-reliability/pull/287), [기존 조사](00-research-review-ai-llm-test-structure.md)
- [Testing Guide](../../docs/development/testing.md), [Test Design](../../docs/development/test-design.md), [CI Admission](../../docs/development/ci/admission.md), [CI Change Impact](../../docs/development/ci/change-impact.md)
- [Reliability AI Evaluation](../../docs/development/review-ai-evaluation.md), [Architecture](../../docs/ARCHITECTURE.md)
