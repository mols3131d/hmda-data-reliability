---
type: openspec-spec-driven-tdd-design
category: design
title: Native Langfuse Review Evaluation
description: SDK 기본 실행 경로와 원격 프롬프트를 사용하고 도메인 실행과 로컬 원문 보존만 남깁니다.
---

## Technical Delta

[Proposal](proposal.md)과 두 capability의 변경 계약을 전제로 한다. SDK pin은 `langfuse==4.15.6`이며 `get_client()`·`get_prompt()`·`get_dataset()`·`dataset.run_experiment(task=...)`와 native observation을 직접 사용한다.

### D1. Separate Setup From Experiments

`evaluation/setup.py`는 명시적으로 실행할 때만 Markdown 모듈을 native text prompt로 등록하고 composition reference·대화 history placeholder를 갖는 세 chat prompt와 합성 Dataset을 등록한다. 기본 model 예시는 `qwen3.5:4b-8k-local`이다. Score Config·Annotation Queue를 자동 생성하지 않는다.

`evaluation/experiment.py`는 기존 Dataset을 조회하고 task를 연결한 뒤 SDK 결과의 `format()`을 출력한다. `--dataset`, `--name`, 선택적 UTC `--dataset-version`, `--prompt-label`을 받는다. 기본 label은 `production`이다. `max_concurrency=1`, `evaluators=[]`를 사용하며 반복마다 새 experiment run을 만든다. Oracle·controls·검토자 질문은 task의 provider input에 넣지 않는다. 두 module은 기존 도메인의 평가 경로에 두는 작은 실행 예제이며 Langfuse가 강제하는 디렉터리 표준으로 설명하지 않는다.

### D2. Pin Native Prompts For Each Workflow

단계 이름은 `hmda-review-ai/evidence_review`, `hmda-review-ai/draft_critique`, `hmda-review-ai/synthesis`다. Seed text prompt 이름은 `hmda-review-ai/`와 Markdown 상대 경로에서 `.md`를 뺀 문자열이다. Workflow 시작 시 같은 label의 세 chat prompt 객체를 모두 읽고 해당 실행에서 재조회하지 않는다. 공통 model·`max_tokens`·`timeout`은 첫 prompt의 versioned config를 정본으로 사용한다. 일반 API는 기존처럼 명시적인 Runtime 설정을 받는다.

Chat template는 공통 reference의 system 메시지·history placeholder·현재 단계 질문 reference의 system 메시지로 구성한다. History는 canonical JSON user 메시지와 이전 system 질문·assistant 원문을 포함한다. Native compile 뒤 전체 메시지 byte cap·digest는 기존 경계에서 적용한다. 각 StageRecord에는 적용한 `prompt_name`과 `prompt_version`을 기록한다.

기본 service도 이 경로를 사용한다. 원격 조회가 실패하면 모델 호출 전 `unavailable / prompt_unavailable`로 끝내고 로컬 Markdown으로 fallback하지 않는다. SDK cache는 사용하되 별도 cache·동기화 계층을 만들지 않는다. 같은 workflow의 고정은 여러 원격 label 갱신을 하나의 transaction으로 만든다는 뜻이 아니다.

### D3. Instrument Actual Calls And Retain Raw First

각 `_call` 주변에 `get_client().start_as_current_observation(as_type="generation", ...)`을 둔다. 실제 prompt 객체·model을 연결하고 반환된 bounded 원문을 먼저 로컬에 저장한 뒤 허용된 compiled message·output·native usage field와 상태를 갱신한다. 모델 호출이 끝난 뒤 빈 observation을 다시 생성하거나 모든 artifact를 전송 전에 다시 읽는 별도 계층을 두지 않는다.

Metadata에는 workflow·stage·revision·digest·고정 상태만 둔다. Credential·provider 예외 원문·개인 경로·설정 object는 자동 캡처하지 않는다. 최소 context manager가 exporter 실패만 격리하며 관측 장애 때문에 모델을 재호출하거나 보존된 core 결과를 바꾸지 않는다.

### D4. Use Standard Configuration And SDK Lifecycle

SDK는 native `LANGFUSE_*` 환경을 읽고 제공자는 표준 `OPENAI_BASE_URL`·`OPENAI_API_KEY`를 사용한다. 실험의 model·token·읽기 timeout은 첫 Prompt config가 소유한다. 최초 config는 model 예시·`max_tokens=1024`·`timeout=300`을 포함한다. 연결 timeout은 10초, Runtime retry는 0회이고 나머지 한도는 도메인 기본값을 사용한다. `LANGFUSE_TIMEOUT`은 SDK HTTP 설정이며 core timeout과 다르다. 기존 `HMDA_AGENTIC_REVIEW_*`·`HMDA_LANGFUSE_*` 운영 설정과 호환 해석은 제거하고 로컬 artifact root만 유지한다. Runtime의 명시적 설정 객체·transport timeout·retry·단계/전체 예산은 계속 적용한다.

별도 worker·stdin protocol·watchdog·외부 I/O deadline·주기 heartbeat를 제거한다. 단계 시작·종료만 stderr에 표시하며 별도 timer thread를 만들지 않는다. SDK `flush()`는 lifecycle 종료에 사용하되 내부 queue 대기로 프로세스 종료가 늦어질 수 있음을 공개한다. 강제 취소가 필요한 배포는 실행 환경의 job timeout을 사용한다.

### D5. Native Human Evaluation

사람이 UI에서 다섯 기준의 Score Config와 Annotation Queue를 구성하고 experiment compare로 실제 응답을 읽는다. 프로젝트가 Config ID·작성자·사유·모든 점수를 API로 다시 읽어 별도 완료 판정을 하지 않는다. UI 점수·Queue 완료가 채택 의견이나 승인 권한을 자동 생성하지 않는다. 비교 시 Dataset version·prompt version·model·실제 revision을 확인하는 책임은 사람 안내에 남긴다.
