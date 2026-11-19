---
type: design
title: Provider and Investigation Evidence
description: Codex와 Ollama의 공통 요청·응답 계약, 시간 한도, 로컬 실행 기록과 Langfuse 관측을 정의합니다.
---

# Provider and Investigation Evidence

## Provider Contract

제공자와 모델은 조사 시작에 결정한다. API는 주입한 `provider=`, `RuntimeAISettings`의 호환 연결, 기본 로컬 Codex 순으로 선택한다. 기존처럼 주입 어댑터와 호환 설정을 함께 전달하면 주입한 어댑터가 우선한다. CLI는 명시적 제공자, 명시적 `OPENAI_BASE_URL`, 기본 로컬 Codex 순으로 선택한다. `OPENAI_API_KEY`만 설정해도 기본 선택은 같다. 모델 기본값과 인증 정보는 선택한 제공자에서만 가져온다. 서로 충돌하는 새 명시적 선택은 호출 전에 거절하며 제공자 장애는 해당 실패로 반환한다. [현재 조사 API](../../../src/hmda_reliability/reliability_ai/investigation/service.py#L49), [현재 CLI 설정](../../../src/hmda_reliability/reliability_ai/evaluation/experiment.py#L58)

| 구분 | 공통으로 전달할 값 |
| --- | --- |
| 요청 | 조사·턴 ID, 버전을 고정한 프롬프트로 구성한 입력, 허용 도구와 근거, 종료 시각과 크기 한도 |
| 수신 기록 | 한도 안의 응답 본문과 도구 호출 자료, 시도와 전송 시각, 제공자 호출 ID와 가능한 사용량 |
| 판단 | 순서가 있는 조회 제안과 인자, 근거를 인용한 최종 보고, 또는 실패 상태와 사유 |

그래프는 원문 저장 뒤 응답을 해석하고 도구·인자·근거 ID를 검사한다. 사고 조사에서는 배치 조회를 허용하고 적재 조사는 턴당 한 건을 받는다. 승인된 조회마다 제안 ID와 관찰값을 연결해 다음 턴으로 전달한다. 조회 제안과 결과의 ID가 일치하는지 확인한다. [사고 조사 예산 계약](../../../openspec/specs/reliability-agentic-review/spec.md#requirement-bounded-investigation-budgets), [적재 도구 계약](../02-proposal-ingestion-llmops/decision-contract.md#tool-contract)

### Codex and Ollama

- **Codex**는 조사 중 같은 로컬 App Server와 관리형 ChatGPT OAuth 세션을 사용한다. `account/read`로 `chatgpt` 계정을 확인한다. 모델 호출 시도마다 새 임시 스레드에 그래프가 구성한 이력과 `outputSchema`를 한 번 전달한다. 조사·논리 턴·시도와 App Server 요청·스레드·턴 ID를 연결하고, 일치하는 종료 이벤트와 응답 본문만 해당 시도의 결과로 받는다. [Codex 연동 근거](../04-design-runtime-ai-codex-oauth-provider.md)
- **Codex 실행 환경**은 전용 작업 디렉터리와 어댑터가 고정한 정책을 사용한다. 상속된 MCP·도구·hooks·plugins와 권한 승격을 차단한다. 파일·명령·도구 네트워크의 격리를 확인할 수 있는 환경에서만 근거를 전달한다. OAuth 인증 정보는 Codex가 관리한다.
- **Ollama와 호환 서버**는 기존 호환 전송의 응답 크기·시간 제한과 오류 분류를 활용한다. 호환 요청은 assistant의 호출 ID를 대응하는 tool 메시지까지 유지하고, 선택된 설정을 해당 어댑터에서만 사용한다. [현재 호환 전송](../../../src/hmda_reliability/runtime_ai/provider.py)

### Deadlines and Failures

그래프는 앱이 전달할 전체 이력과 도구 정의를 구성한 뒤 입력 바이트와 조사 기한을 확인한다. 전달한 입력의 digest를 시도별로 기록하고, 어댑터는 수신 본문과 도구 호출 자료의 크기를 제한한다. Codex 내부 문맥과 사용량은 제공자가 보고한 범위까지 알 수 있다.

모델 전송 재시도는 어댑터에서만 수행한다. 연결·대기·백오프에 같은 종료 시각을 적용한다. 호환 연결은 기존 타임아웃·연결 오류·5xx 분류와 설정된 재시도 한도를 적용한다. Codex는 이전 턴이 수락되지 않았다고 확인한 경우에만 예산 안에서 재시도하며, 수락 여부가 불명확하면 그 실패로 종료한다. 기한 소진 시 가능한 경우 `turn/interrupt`를 요청하고 실제 종료와 따로 기록한다. 제한된 종료 처리 중 받은 늦은 응답은 원문으로 보존하며, 이미 닫은 최종 기록과 별도 파일에 연결한다. [호환 전송 오류 분류](../../../src/hmda_reliability/runtime_ai/provider.py#L347)

## Evidence and Replay

1. 조사 ID에 고정 입력, 근거와 코드·그래프·정책 버전을 연결한다. 전송 요청은 프롬프트와 메시지의 순서 있는 참조로 복원할 수 있게 기록한다.
1. 수신 본문과 호출 자료는 파싱·조회·원격 게시 전에 기존 private atomic create-only 방식으로 한 번 저장한다. 도구 관찰값도 다음 턴 입력에 넣기 전에 저장한다. 각 기록은 최종 파일과 독립적으로 조사 ID에서 찾을 수 있게 한다. 본문 없는 전송 장애는 실패 정보만 기록한다.
1. 최종 기록은 원문과 관찰값을 참조한다. 필수 기록의 게시가 기한 안에 완료된 경우에만 `completed`를 반환한다. 쓰기 실패는 오류와 회수 가능한 경로를 반환한다. 공개 `InvestigationResult`와 평가 CLI 결과를 만들 때 기존 본문과 도구 결과 필드를 복원한다. 과거 파일은 당시 형식과 실행 ID로 읽는다.
1. 새 ID의 재현에 고정한 Prompt 또는 실제 구성 입력, 응답·조회 결과, 상대 시각과 종료에 영향을 준 저장 성공·실패를 공급한다. 그래프는 기록된 경계 결과로 종료를 다시 판정한다. 필수 기록 누락·손상·버전 차이는 재현 불가 사유로 반환한다. 실제 Prompt·Dataset 조회, 모델·도구 호출, 원격 관측과 복구의 호출 횟수는 0회다. [현재 원문 보존 계약](../../../openspec/specs/reliability-agentic-review/spec.md#requirement-local-provider-response-retention)

## Langfuse Observation

실제 모델 턴과 도구 실행에 native 관측을 남기고 모델 출력은 로컬 보존 성공 뒤에 게시한다. 자동 본문 수집을 끄고 허용된 합성 사례의 필드만 전송한다. 원격 장애는 관측 기록으로 남기며 이미 계산한 결과를 반환한다. Dataset 항목과 조사·턴·관측 ID를 연결하고 원격에서 같은 실행을 다시 조회한다. [현재 관측·평가 계약](../../../docs/domains/review-ai.md#provenance-and-evaluation)
