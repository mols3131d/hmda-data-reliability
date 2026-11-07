---
type: research
title: LLM Test Structure And Execution Cost Assessment
description: 실제 LLM·외부 서비스 호출 비용을 기본 테스트에서 분리하면서 pytest 선택성과 CI 병합 검증을 유지할 수 있는지 조사하고 구조 변경 범위를 판단한다.
tags:
  - testing
  - review-ai
  - llmops
  - pytest
  - ci
---

# LLM Test Structure And Execution Cost Assessment

> [!NOTE]
> **권고:** 기존 `unit`·`component`·`integration` 테스트 수준은 유지하고, 모델/원격 서비스 **실호출 여부와 비용을 별도 marker 및 실행 guard로 분리**한다. 기본 PR 검증에는 기존 fake transport·실제 SDK의 in-memory 경계 테스트를 유지하고, 명시적 live smoke와 Langfuse 품질 평가는 목적에 따라 선택적으로 실행한다. **이 PR의 완료 목표는 보고서 작성이 아니라 해당 테스트 구조 변경 및 검증이다.** 아래 신규 marker와 guard는 아직 구현되지 않은 제안이다.

## Question

현재의 Review AI·Runtime AI 테스트를 저비용으로 재현 가능하게 유지하면서, 실모델/실서비스 테스트를 안전하게 명시적으로 선택할 수 있도록 어떤 구조와 CI 계약을 변경해야 하는가?

## Scope

- 조사 기준: `main` `7efb332c2efd78f77ee724440e28285ebb3ee55f`, 2026-11-08(KST). 저장소 정본과 [Notion 원본 조사](https://app.notion.com/p/41113d7e58b981f1bbf4c888d62fd043)를 대조했다.
- 범위: pytest level/resource/비용 marker, Review AI·Runtime AI 테스트 경계, CI runner의 선택 규칙, 원격 호출 방지와 Langfuse 실험의 책임 구분.
- 제외: production model/provider 변경, 신규 유료 계정/secret 설정, 실제 결제, Langfuse Dataset·Prompt·Experiment 실행, 프롬프트 품질 개선, 전체 프로젝트 테스트 리팩토링.
- 근거 한계: 코드를 읽어 확인했으며 전체 pytest, 실제 모델 요청, 유료 호출과 latency/비용 계측은 실행하지 않았다.

## Findings

### Existing Markers Already Express Test Levels And Resource Costs

- [`pyproject.toml`](https://github.com/mols3131d/hmda-data-reliability/blob/7efb332c2efd78f77ee724440e28285ebb3ee55f/pyproject.toml)은 `unit`, `component`, `integration` primary marker와 `memory`, `stress` resource marker를 등록하고 `--strict-markers`를 활성화한다. 기본 `addopts`는 resource test만 제외한다.
- [Testing Guide](https://github.com/mols3131d/hmda-data-reliability/blob/7efb332c2efd78f77ee724440e28285ebb3ee55f/docs/development/testing.md)는 가장 낮은 유효 테스트 경계 하나를 primary marker로 선택하며, `memory`/`stress`를 직교하는 resource marker로 정의한다.
- 따라서 `llm_live` 등을 `integration`의 대체 marker로 만들면 기존 의미가 깨진다. **실행 비용과 테스트 경계를 직교 분리하는 구조**가 적절하다.

### Offline Review AI Tests Preserve Important Real Contracts

- [Runtime AI provider tests](https://github.com/mols3131d/hmda-data-reliability/blob/7efb332c2efd78f77ee724440e28285ebb3ee55f/tests/runtime_ai/test_provider.py)는 recording transport, fake clock, `httpx.MockTransport`로 wire payload·retry·timeout·실패 코드를 검증한다.
- [Staged runtime integration tests](https://github.com/mols3131d/hmda-data-reliability/blob/7efb332c2efd78f77ee724440e28285ebb3ee55f/tests/review_ai/test_staged_runtime_integration.py)는 실제 OpenAI SDK 경로를 모의 HTTP로 구동하고 stage history·raw response·output을 확인한다. `integration`이라도 외부 API에 과금되지 않는 실질적인 회귀 테스트다.
- [Evaluation SDK tests](https://github.com/mols3131d/hmda-data-reliability/blob/7efb332c2efd78f77ee724440e28285ebb3ee55f/tests/review_ai/evaluation/test_native_sdk.py)는 Langfuse SDK와 in-memory exporter를 활용해 remote 없이 계약을 검증한다.
- 그러므로 **모든 LLM 관련 테스트를 live나 느린 테스트로 묶어 배제하면 회귀 방어가 약화**된다. 기존 fake/SDK 테스트를 기본 실행에 보존해야 한다.

### CI Has A Separate Explicit Marker Filter Contract

- [`scripts/ci/run_checks.py`](https://github.com/mols3131d/hmda-data-reliability/blob/7efb332c2efd78f77ee724440e28285ebb3ee55f/scripts/ci/run_checks.py)의 `pytest()`는 full과 scoped 양쪽에 `-m "not memory and not stress"`를 직접 전달한다.
- [`tests/scripts/ci/test_ci_pytest.py`](https://github.com/mols3131d/hmda-data-reliability/blob/7efb332c2efd78f77ee724440e28285ebb3ee55f/tests/scripts/ci/test_ci_pytest.py)는 위 argv와 parallel threshold·boundary 제외 조건을 명시적으로 고정한다. `pyproject.toml`만 수정해선 CI 선택 계약이 끝나지 않는다.
- [CI Change Impact](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/development/ci/change-impact.md)는 영향이 불명확하면 검사 범위를 넓히거나 선택을 실패시키도록 요구한다. [CI Admission](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/development/ci/admission.md)은 prospective merge의 필수 검증을 비용만으로 post-merge에 미루지 못하도록 한다.

### Live Model Evaluation Has A Different Evidence Owner

- [Review AI Evaluation Guide](https://github.com/mols3131d/hmda-data-reliability/blob/7efb332c2efd78f77ee724440e28285ebb3ee55f/docs/development/review-ai-evaluation.md)는 일반 pytest와 구별하여 `hmda_reliability.review_ai.evaluation.setup`의 원격 등록 및 `experiment`의 실제 모델 실험을 명시적으로 실행한다. 현재 `langfuse==4.15.6`을 사용한다.
- **Fake 통과**는 protocol/flow 보증이지 LLM 답변의 사실성·유용성 증거가 아니다. **저렴한 모델 통과**도 운영 대상 모델의 품질 보증이 아니다. 비교 가능한 모델·프롬프트·Dataset 버전과 사람 평가를 그대로 유지해야 한다.
- [Human Evaluation Baseline](https://app.notion.com/p/40d13d7e58b98151bc7de1e19932d49f)은 실제 응답 수집과 사람 품질 판단을 구분한다. 본 PR은 기존 Langfuse-native 평가 로직을 pytest로 이식하거나 자체 evaluator를 새로 만들 필요가 없다.

### Markers Alone Do Not Provide A Cost Safety Boundary

- 일반 `-m` 지정, `-k`, test node 직접 실행과 IDE 실행에서는 선택 정책이 달라질 수 있다. 실행 marker가 특정 호출 경로를 기본 제외하더라도 **실제 모델/유료 서비스 접근에 대한 별도 명시적 허용 검사**가 필요하다.
- 전체 소켓 차단은 Airflow/dbt/local-service 테스트에 부작용이 있을 수 있다. 먼저 실제 외부 provider·Langfuse 경계에서 최소한의 guard로 막고, 더 넓은 네트워크 차단은 영향이 확인될 때만 검토한다.
- 안전한 실행의 조건은 marker 등록뿐 아니라 **잘못 분류된 test·실수로 직접 실행된 test도 의도치 않은 비용 없이 실패하도록** 테스트로 확인하는 것이다.

## Options

| 구조 | 장점 | 한계 | 판단 |
| --- | --- | --- | --- |
| 기존 level marker만 사용 | 추가 관리 부담 없음 | `integration`에 가짜/실제 요청이 섞일 수 있고 비용 의도를 표현하지 못함 | 보완 필요 |
| 비용/실호출 marker + 별도 runtime guard | 기존 level 의미 유지, 기본 경로 무료, opt-in 경계 명확 | marker 정합성과 guard의 회귀 테스트 필요 | **권고** |
| 모든 LLM 테스트를 별도 디렉터리·프레임워크로 이전 | 물리적 분리 | 기존 도메인 소유권·test selection 복잡화, 중복 운영 가능 | 현 근거로는 과잉 |

제안하는 최소 marker는 다음과 같다. 채택 여부와 이름은 실제 테스트 수집/요구를 확인한 뒤 결정한다.

| Marker | 의미 | 관계 |
| --- | --- | --- |
| `llm_live` | 실제 로컬/원격 모델 inference 수행 | 기본 제외, level marker와 함께 사용 |
| `llm_paid` | 요금이 발생할 수 있는 provider 호출 | `llm_live`의 subset, 독립 결제 opt-in 필요 |
| `service_live` | inference와 무관한 실제 외부 Langfuse 등 접속 | 기본 제외, 실제 필요 사례가 있을 때만 사용 |

기본 제외식 후보: `not memory and not stress and not llm_live and not service_live`. `llm_paid`는 `llm_live`에 반드시 포함되므로 별도 기본 제외 표현은 중복이지만, 잘못된 단독 부착을 발견하는 테스트가 필요하다.

## Implications

**이 PR의 구현 완료 기준:** 비용 관련 설정만 추가하는 것이 아니라, 기존 테스트 구조에서 결정론적 계약 검증과 실제 모델/서비스 경계를 명확하게 분류하고 실행·CI 선택을 일관되게 만드는 것이다.

권고 구현 순서:

1. **Inventory and contract mapping.** `tests/review_ai`, `tests/runtime_ai`, 외부 SDK/HTTP/fixture 사용을 검토해 offline/실서비스 호출을 실증적으로 분류한다. 실제 외부 호출이 없는 테스트는 level marker를 유지하고 불필요하게 live로 이동하지 않는다.
2. **Tests first.** 잘못된 `llm_paid` 단독 표기, 무단 live 실행, mock transport의 정상 실행, 명시적으로 허용된 local/live 실행과 credential 누락을 observable outcome으로 검증하는 focused contract tests를 설계한다. 무조건 skip으로 잘못된 접근을 PASS 처리하지 않는다.
3. **Marker + guard integration.** `pyproject.toml`과 필요한 pytest fixture/test만 최소 수정한다. 단순 `-m` 직접 지정으로 guard가 우회되지 않아야 한다. `llm_live`에는 별도 explicit opt-in, `llm_paid`에는 추가 opt-in·허용 provider/endpoint·비용 상한이 필요하다. `service_live`도 독립 외부 접속 허용 정책을 갖는다.
4. **CI routing and docs.** `scripts/ci/run_checks.py`의 full/scoped 필터 및 `tests/scripts/ci/test_ci_pytest.py`의 argv 계약을 함께 변경한다. 필요 시 `scripts/ci/classify_changes.py`의 변경 영향 전파와 CI 계약 테스트를 수정한다. `docs/development/testing.md`에 실행 명령과 marker 의미를 설명한다.
5. **Optional smoke.** 실제로 검증 가치가 입증된 최소 로컬 모델 smoke부터 만들고, 유료 호출은 별도 명시적 승인·상한·trusted runner가 확인된 경우에만 추가한다. 품질 평가는 현재 Langfuse Dataset Experiment를 재사용한다.

**Acceptance conditions — 실제 증거로 확인할 것**

- 일반 `uv run pytest`, CI full/scoped 검사, 테스트 파일 직접 실행에서 무의도한 외부 LLM/유료 API/원격 Langfuse 요청이 발생하지 않는다. 직접 실행이 live guard에 의해 차단되는 경우 해당 의도와 실패 메시지가 명확하다.
- `unit`·`component`·`integration`의 primary 의미는 유지하고 기존 mock/SDK 계약 테스트가 기본 suite에서 계속 실행된다.
- 새 marker의 의도·조합·기본 제외·opt-in 조건을 자동 테스트가 검증한다. 비용 guard는 marker selection에만 의존하지 않는다.
- 기존 CI 변경 영향 라우팅, prospective merge 검증, 필수 검사는 유지한다. scope가 불확실하면 fail-safe로 넓히거나 선택 실패를 드러낸다.
- 실제 모델 테스트를 도입한다면 호출 수·입출력 토큰·재시도·timeout·비용 한도를 사전 구성하고 확인한다. 선택하지 않은 유료 provider에는 키나 비용이 소모되지 않는다.
- Langfuse 실험·사람 평가를 단순 pytest PASS와 혼동하지 않는다. 실제 변경 후 focused→관련 domain→필요한 CI 계약 검사 결과를 기록한다.

**Scope guard:** production behavior 변경, prompt/model 교체, test 효과를 저하하는 무차별 mock, 새 유료 provider 가입, secret 저장소 추가, 전역 테스트 디렉터리 재배치, 기존 Langfuse-native 평가 대체는 범위 밖이다.

## Open Questions

- 현재 pytest 안에 실모델 또는 실제 외부 서비스 호출이 있는지 전수 코드 검색/collection과 가장 작은 실행으로 확정해야 한다. 이 결과에 따라 신규 live test와 marker의 실제 적용 대상이 달라진다.
- `service_live`에 해당하는 pytest 사례가 없다면 당장 marker를 등록하지 않고 필요 시 도입해도 된다. 사용 사례 없는 표준 확장을 피한다.
- 어떤 변경이 live 검증 없이는 `main`에 적합하지 않은지(merge-critical)를 결정해야 한다. 단순히 비싸다는 이유로 필요한 검증을 optional 처리하지 않는다.
- 유료 smoke가 필요하면 **테스트 대상의 실제 provider 호환성**과 provider/model별 가격·상한·신뢰 경계를 그때 확인한다. 현 단계에서는 서비스나 모델을 확정하지 않았다.

## References

- [Notion Research — LLM Testing Cost & Marker Strategy](https://app.notion.com/p/41113d7e58b981f1bbf4c888d62fd043)
- [Testing Guide](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/development/testing.md)
- [Test Design](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/development/test-design.md)
- [CI Design and Admission](https://github.com/mols3131d/hmda-data-reliability/blob/main/docs/development/ci/README.md)
- [Pytest marker documentation](https://docs.pytest.org/en/stable/how-to/mark.html)
- [Langfuse Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
