---
type: openspec-spec-driven-tdd-design
category: design
title: Reliability AI Investigation Runtime Design
description: 조사 그래프와 제공자 경계, 로컬 기록과 기존 호출부의 전환 방식을 정합니다.
---

## Technical Delta

[제안서](proposal.md)와 [사고 조사 변경 명세](specs/reliability-agentic-review/spec.md)를 기준으로 한다.

### D1. Investigation Graph

- **Decision** 공용 `StateGraph`는 판정, 모델 호출, 원문 보존·검증, 조회 단계 사이를 전이한다. 그래프 상태에는 턴 번호, 현재 턴의 조회 위치, 누적 조회 횟수, 다음 단계가 있다. 실행 컨텍스트는 모드별 단계 함수와 호출 한도, 현재 모델 응답, 종료 결정을 담는다. 각 조사 서비스가 입력, 허용 도구, 기한, 기록을 관리하고 그래프 종료 후 결과를 게시한다. [공용 그래프](../../../src/hmda_reliability/reliability_ai/investigation/graph.py)
- **Rationale** 사고 조사에는 검증된 모델 보고서가 필요하고, 적재 조사는 규칙으로 상태와 조치가 확정될 수 있다. 이 판단을 호출 모드가 소유하면 공통 그래프에 적재기나 복구 실행기를 넣을 필요가 없다.

### D2. Provider Integration

- **Decision** `runtime_ai`에서 요청·수신 기록·정규화된 결과 계약을 정의한다. LangChain Core는 메시지와 도구 스키마에 사용하며 직접 의존성으로 선언한다. 제공자별 형식 변환과 전송은 어댑터에 둔다. API 진입점과 합성 CLI가 설정을 해석해 어댑터를 선택하고, 기존 `provider=` 주입은 같은 계약에 연결한다.
- **Decision** Codex는 고정된 격리 설정의 로컬 App Server 프로세스와 관리형 구독 세션을 재사용한다. `account/read`로 계정을 확인하고 시도별로 새 임시 스레드와 `turn/start`의 `outputSchema`를 사용한다. 설정된 파일·명령·도구 접근 범위를 입증하고 앱이 실제로 보낸 이력을 기록한다. 호환 연결은 현재 Chat Completions 전송·재시도 코드를 어댑터에 둔다. [제공자 설계](../../../inbox/github-291-build-ingestion-agent-harness/07-design-reliability-ai-runtime-replacement/provider-and-evidence.md#codex-and-ollama)
- **Trade-off** 임시 스레드에는 앱이 구성한 제한된 이력을 매번 전달한다. 그 입력은 한도를 계산하고 보존할 수 있다. 전송량과 지연의 변화는 같은 조건에서 측정한다.

### D3. Deadline and Side Effects

- **Decision** 조사 시작에 단조 시계로 종료 시각을 정하고 제공자 시도와 각 도구 실행, 완료 게시가 이를 사용한다. 모델 재시도는 어댑터만 소유한다. Codex 요청을 중단할 때 `turn/interrupt` 요청·응답과 실제 종료를 개별적으로 기록한다.
- **Decision** 모델의 제안은 raw 응답 저장 후 검증하고, 조회 결과와 제안 ID를 연결해 다음 입력을 구성한다. 승인 백필의 연결 누락은 API가 그래프 전에 확정한다. 나머지 승인된 복구 실행은 성공한 조사 결과를 받은 위임 함수가 기존 실행기에 넘긴다. [현재 위임 호출](../../../src/hmda_reliability/reliability_ai/execution/service.py#L120)

### D4. Durable Evidence and Replay

- **Decision** 호출별 create-only 원문·관찰 파일을 조사 ID로 찾게 하고, 버전 있는 최종 기록에는 순서·참조·digest를 둔다. 현재 원자적 게시 방식으로 필수 기록을 기한 안에 확정한다. 기존 `InvestigationResult`와 평가 출력에서 필요한 본문과 도구 결과는 저장 참조에서 조립한다. [현재 근거 저장](../../../src/hmda_reliability/reliability_ai/store.py)
- **Decision** 재현은 새 ID의 동일 그래프에 기록된 프롬프트·입력, 응답과 조회, 상대 시각, 종료에 영향을 준 쓰기 결과를 공급한다. 기록의 입력·그래프·정책 버전과 참조 무결성을 확인한다. 이전 파일은 읽기 경로에서 기존 형식으로 해석한다.
- **Rationale** 조사 중 종료와 완성 파일 실패에서도 앞선 근거를 읽을 수 있다. 참조형 기록으로 공개 결과와 오프라인 재현이 같은 원문을 사용할 수 있다.

### D5. Observation and Cutover

- **Decision** Langfuse는 `reliability_ai`에서 버전이 고정된 native Prompt와 실제 모델·도구 경계를 관측한다. 원격 전송 결과는 최종 로컬 판정과 별도 기록으로 남긴다. 자동 본문 수집을 끄고 명시적 합성 입력 투영을 사용한다. [현재 평가·관측 계약](../../../docs/domains/review-ai.md#provenance-and-evaluation)
- **Decision** 공개 조사 API, 위임 실행, 합성 평가가 같은 그래프를 호출하도록 전환한다. `investigation/service.py`의 옛 루프와 전용 연결 코드가 제거되었는지 확인한다. [전환과 종료 기준](../../../inbox/github-291-build-ingestion-agent-harness/07-design-reliability-ai-runtime-replacement/migration-and-verification.md)
