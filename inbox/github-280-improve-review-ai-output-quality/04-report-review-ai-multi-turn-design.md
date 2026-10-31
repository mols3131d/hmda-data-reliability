---
type: report
title: Review AI Multi-turn Composition Assessment
description: 같은 사례의 대화 맥락을 유지하는 단계별 검토와 코드 기반 최종 JSON 취합의 가능성, 현재 구현 제약과 비교 실험안을 검토합니다.
tags:
  - review-ai
  - prompt-engineering
  - conversation-state
---

# Review AI Multi-turn Composition Assessment

**같은 사례의 맥락으로 질문을 나눠 진행하고, 단계별 응답을 코드로 최종 JSON에 취합하는 방식은 구현할 수 있다. 검토할 가치가 있는 후보이며 현재 단회 호출보다 품질이 낫다는 근거는 아직 없다.** 이번 작업은 언어 정책 파일명 변경과 설계 검토까지다. 다단계 실행·모델 호출·기본 경로 전환은 수행하지 않았다.

검토 기준은 `7f74310ad906817f3f36ab4246458dc79e136ad3` 위의 현재 작업 폴더다. 앞선 프롬프트 모듈 재구성도 포함되어 있으며 아직 별도 commit의 실행 증거가 아니다. 이 보고서는 제안과 조사 기록이며 정본 요구사항이나 채택 결정이 아니다.

## Conversation State

현재 사용하는 Chat Completions 방식에서는 애플리케이션이 이전 메시지와 응답을 다음 요청에 포함해 대화 맥락을 유지할 수 있다. 이는 서버의 같은 세션 ID가 알아서 내용을 기억한다는 전제가 아니다. [OpenAI 공식 대화 상태 문서](https://developers.openai.com/api/docs/guides/conversation-state)는 이런 클라이언트 이력 관리 방식을 설명한다. 현재 Ollama 환경의 호환성과 실제 맥락 활용 품질은 별도 실행으로 확인해야 한다.

한 사례마다 불변 canonical input과 독립된 실행 identity를 고정한다. 다음 요청에는 원본 입력과 검증된 이전 단계의 응답을 포함한다. 사례가 바뀌면 새 실행을 시작한다. 이전 모델 답변은 검토 자료이며 새로운 Evidence나 확인된 사실로 승격하지 않는다.

전체 이력이 누적되면 입력 토큰과 context 사용량이 늘어난다. 같은 대화라는 이유로 이전 맥락의 처리 비용이 사라지지 않는다. 실제 context 크기, 입력·출력 예산과 완료 상태를 함께 확인해야 한다. [OpenAI 공식 context 설명](https://developers.openai.com/api/docs/guides/conversation-state#managing-the-context-window)

## Recommended Candidate

초기 후보는 고정된 세 단계다. 모든 단계에서 최종 JSON 전체를 다시 생성하지 않고 각 단계가 소유하는 필드만 반환한다.

| Step | Question focus | Owned output |
| --- | --- | --- |
| `evidence_review` | 제공된 근거로 확인되는 사항과 남은 불확실성은 무엇인가? | `findings`, `uncertainties`, `evidence_used` |
| `draft_critique` | 실제 초안의 부족한 점과 다음 조사 우선순위는 무엇인가? | `utility_contributions` |
| `synthesis` | 앞선 검토를 바탕으로 사람이 판단할 핵심과 자문 결론은 무엇인가? | `review_summary`, `advisory_recommendation` |

각 단계의 입력에는 같은 원본 사례가 유지된다. 명시적인 구조 충돌은 단계 실패·불일치로 기록하고 조용히 다른 필드로 덮어쓰지 않는다. 자연어 판단 사이의 모순은 현재 fact validator로 탐지할 수 없으므로 사람 평가에 포함한다. 초기 후보에서는 자동 수정 대화와 무제한 반복을 추가하지 않는다.

코드는 다음 원칙으로 최종 [AgenticReviewOutput](../../src/hmda_reliability/review_ai/contracts.py)을 조립한다.

- `incident_id`, `incident_type`, `target_column`과 `deterministic_facts`는 처음 고정한 입력에서 복사한다.
- 단계별 구조·열거값·근거 ID와 상한을 검증한 후 해당 단계의 소유 필드에 대입한다. 같은 필드의 임의 merge와 마지막 응답 우선 규칙을 두지 않는다.
- 최종 `evidence_used`는 근거 단계의 선언과 모든 finding·기여의 실제 참조를 허용 ID 안에서 합쳐 안정적으로 정렬한다. 입력에 있다는 이유로 모든 근거를 사용했다고 채우지 않는다.
- 세 단계를 모두 성공한 경우에만 최종 output을 구성하고 기존 [structured-fact validator](https://github.com/mols3131d/hmda-data-reliability/blob/24b5f26833121de853ce0787c0bb67c3ad25673d/src/hmda_reliability/review_ai/validator.py)를 적용한다.
- 필수 단계가 실패하면 성공한 단계의 내용은 진단 자료로 보존하고 완성된 accepted output으로 취급하지 않는다.

원본 수치를 코드로 넣으면 모델의 구조화된 수치 복사 오류를 줄일 수 있다. 설명문 안의 잘못된 비율·단위·원인까지 교정되는 것은 아니므로 그 품질은 계속 평가해야 한다.

## Mechanical Collection

자유문 답변을 `{"question": "...", "answer": "..."}`처럼 JSON 문자열로 감싸는 것은 코드만으로 가능하다. 다만 이것은 질의응답 기록이다. 현재 소비자가 요구하는 `kind`, 근거 ID 배열, 조건부 `priority`까지 의미적으로 분류해 주지는 않는다.

현재 계약을 유지하는 첫 후보에는 **단계별 작은 typed JSON → 코드 취합**을 권장한다. 마지막 모델 호출이 전체 JSON을 다시 작성하도록 맡기면 앞서 검증한 필드가 다시 바뀔 수 있다. 단계별 출력을 마지막에 그대로 대입하는 코드가 취합을 소유한다.

현재 Runtime AI는 `json_object`를 요청한다. JSON mode는 구문상 JSON과 schema 준수가 다르며, schema를 강제하는 Structured Outputs의 지원은 provider·모델별로 확인해야 한다. 현재 로컬 모델의 지원을 OpenAI 문서만으로 확정하지 않는다. [OpenAI 공식 구조화 출력 설명](https://developers.openai.com/api/docs/guides/structured-outputs#json-mode)

## Current Implementation Gaps

| Current source | Finding / required change |
| --- | --- |
| [runtime_ai/contracts.py](../../src/hmda_reliability/runtime_ai/contracts.py) | `ChatMessage.role`은 `system`·`user`만 허용한다. 이전 답변을 대화로 유지하려면 `assistant` 지원이 필요하다. |
| [runtime_ai/provider.py](../../src/hmda_reliability/runtime_ai/provider.py) | `invoke()`는 전달된 메시지로 한 번의 논리 호출을 처리한다. 세션 관리나 workflow loop가 없다. |
| [tasks/null_spike.md](../../src/hmda_reliability/review_ai/prompt/tasks/null_spike.md), [output/](../../src/hmda_reliability/review_ai/prompt/output/) | 현재는 user 전체를 신뢰하지 않는 데이터로 취급하고 응답마다 최종 출력 전체를 요구한다. 기존 system에 질문만 덧붙이면 충돌한다. |
| [prompt renderer](../../src/hmda_reliability/review_ai/prompt/__init__.py) | 현재 두 메시지의 byte 한도와 digest를 계산한다. 확장 시 누적 이력 전체에 매 단계 호출 직전 동일 검사를 적용해야 한다. Byte 한도는 모델의 token context 한도와 별개다. |
| [service.py](../../src/hmda_reliability/review_ai/service.py), [evidence.py](../../src/hmda_reliability/review_ai/evidence.py), [store.py](../../src/hmda_reliability/review_ai/store.py) | 현재 호출당 하나의 응답과 최종 typed output을 기록한다. 중간 응답·부분 계약·단계 실패를 같은 record에 덮어쓸 수 없다. |

질문과 부분 출력 계약은 애플리케이션이 선택한 신뢰된 단계 지시문으로 제공하고, 원본 입력과 이전 모델 응답은 별도 자료로 유지한다. 기존 전체 출력 설명을 각 단계에서 그대로 재사용하지 않는다. 공유 정책과 작업 범위에 단계 전용 질문·출력 모듈을 조합하는 방식으로 확장한다. 사례 데이터 안의 문자열이 단계나 모듈 경로를 선택해서는 안 된다.

실행 전체의 ID 아래에 단계별 ID·순서·상태·요청 digest·원문 경로·부분 출력 digest·정제된 진단·usage·latency를 연결하는 기록이 필요하다. 코드로 조립한 최종 output의 digest는 각 단계 결과와 연결하고, 이를 모델이 한 번에 반환한 원문으로 기록하지 않는다.

Runtime이 반환한 본문은 각 단계 검증 전에 성공·실패 모두 보존한다. 다음 단계가 실패해도 이전 단계의 원문과 실패 단계의 반환된 원문을 남긴다. 각 단계 재시도 횟수와 단계 수를 구분하고, 총 물리 호출 수·전체 시간·전체 생성량의 상한을 둔다. 이후 재시도를 지원할 경우 앞 단계의 출력이 바뀌면 그에 의존한 후속 단계도 무효화한다.

## Comparison Before Adoption

프롬프트 파일의 모듈 분할과 모델 호출의 단계 분할은 독립적인 선택이다. 구조가 모듈화됐다는 이유로 다단계 호출의 품질이 보장되지는 않는다.

동일 합성 사례, 모델·양자화, 실제 active context와 Thinking 설정을 고정하고 아래 후보를 비교한다. 기존 [합성 품질 corpus](https://github.com/mols3131d/hmda-data-reliability/blob/24b5f26833121de853ce0787c0bb67c3ad25673d/tests/review_ai/evaluation/fixtures/output_quality_v1.json)와 [사람 평가 절차](../../docs/development/review-ai-evaluation.md#baseline-and-candidate-comparison)를 재사용한다.

| Candidate | Purpose |
| --- | --- |
| 현재 단회 호출 | 현재 동작의 기준 |
| 단회 검토 + 입력 식별자·수치의 코드 조립 | 모델의 복사 부담을 없앤 효과를 분리해 확인 |
| 고정 세 단계 + 코드 조립 | 작업 분리와 대화 이력 활용의 추가 효과를 확인 |

초기 응답의 오류가 후속 판단에 반복되는 현상, 근거 없는 원인, 실제 초안에 없는 비판과 전 단계 성공률을 평가한다. 한 번의 논리 review에 사용된 전체 물리 호출 수·토큰·시간과 원문을 모두 기록한다. 성공한 단계만 골라 최종 성공으로 집계하지 않는다. 비교 전에 반복 횟수와 각 후보의 전체 실행 예산을 정한다.

검토 결론은 **고정 단계 + 코드 취합을 실험 후보로 두되, 단회 + 코드 취합을 함께 비교하는 것이 적절하다**는 것이다. 첫 구현은 명시적인 실험 harness, 세 부분 schema, 순수 조립 함수와 단계 기록으로 한정할 수 있다. 구현에 착수할 때 Review AI의 workflow·부분 출력·provenance 계약과 Runtime AI의 message 역할 변경을 소유하는 별도 OpenSpec Change가 필요하다. 현재 기본 실행과 과거 invocation replay 계약을 자동으로 전환하지 않는다.
