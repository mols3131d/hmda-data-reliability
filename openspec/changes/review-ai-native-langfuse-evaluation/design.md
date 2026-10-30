---
type: openspec-spec-driven-tdd-design
category: design
title: Native Langfuse Review Evaluation
description: 기존 검토를 SDK task로 감싸고 외부 I/O를 격리하며 native annotation에 연결할 최소 무결성 경계를 둡니다.
---

## Technical Delta

[Proposal](proposal.md)과 [변경 계약](specs/reliability-agentic-review/spec.md)을 전제로 한다. SDK 계약은 실제 설치해 확인한 `langfuse==4.15.6`으로 고정한다. 최신 v5 API로 전환하거나 기존 JSON 전용 projection을 복원하지 않는다.

### D1. Opt-In Experiment Boundary

새 `evaluation/experiment.py`는 명시적 두 opt-in과 SDK 연결 설정을 검사한 뒤 native 실행을 시작한다. 기존 `evaluation/live.py`는 단일 합성 사례의 실행 진입점으로 남긴다. 일반 import에서 SDK를 로드하지 않으며 대상 서버의 인증·기능을 로컬 SDK 설치 성공으로 추정하지 않는다.

SDK Dataset task의 본체는 현재 `review_null_spike()`다. `max_concurrency=1`, `evaluators=[]`로 사례를 직렬 실행한다. 자동 evaluator나 별도 model client를 추가하지 않는다. 실제 SDK task가 호출됐는지는 fake 결과만 반환하는 검사와 구분해 검증한다.

### D2. Native SDK Process And IO Budgets

SDK 4.15.6의 flush는 내부 queue join이 무한히 기다릴 수 있어 client HTTP timeout만으로 외부 I/O 대기 한도를 보장하지 못한다. SDK lifecycle 전체를 child process에 둔다. 검증한 private JSON을 stdin으로 보내고 필요한 SDK·Runtime environment만 allowlist로 전달한다. SDK stdout·stderr·traceback은 직접 노출하지 않고 본문 없는 정제된 제어 protocol만 부모가 받는다.

Child task의 core 시작·종료 신호로 실행 구간을 구분한다. 부모는 SDK 시작·task 사이·최종 flush에서만 외부 I/O deadline을 감시하고 소진 시 child를 종료한다. Core 구간에는 기존 Runtime timeout·단계/전체 예산을 적용하고 30초 외부 한도를 모델 생성의 총 한도로 사용하지 않는다. 부모는 종료 후에도 이미 원자적으로 저장된 원문과 workflow를 회수해 core 상태와 외부 상태를 따로 제공한다.

### D3. Case And Artifact Integrity

비교용 사례 digest는 고정된 `incident`·`evidence`·`draft` 자료에서 실행 출처를 제외해 산출한다. Dataset item/version과 case/version을 이 digest에 연결하고, item upsert를 현재 사례의 변경 수단으로 사용하지 않는다. 반복마다 새로운 run identity를 사용한다.

Task는 Dataset의 허용된 input만 input 계약에 넣고 실제 실행 SHA를 별도 provenance로 전달한다. Oracle·검토 질문은 검토자 자료로만 사용하고 controls는 provider 자료에 섞지 않는다. 현재 canonical projection에는 project revision이 없다. Canonical input digest는 실제 projection bytes에 대해 계산하며 revision을 새로 주입하거나 양쪽 digest를 인위적으로 다르게 만들지 않는다.

얇은 artifact 검증은 현재 manifest·stage record·raw UTF-8 bytes·collection을 다시 읽고 ID·status·순서·본문 digest·output digest와 실제 input을 대조한다. 이 검증을 통과한 bounded canonical input·이전 답변·실응답만 원격 IO에 연결한다. System prompt는 digest로만 식별한다. 본문 없는 progress event의 역할은 바꾸지 않는다.

### D4. Native Human Annotation And Minimal Local Checks

다섯 criterion과 별도 채택 의견은 고정 Score Config ID·category schema·설정 snapshot에 연결한다. Categorical `0`·`1`·`2`의 서버 반환 값과 native annotation의 source·작성자·시각은 pin에 맞는 실제 read API로 확인하고 고정 mapping으로 해석한다. Config가 이름만 같거나 type·category가 다르면 재사용하지 않는다.

프로젝트에는 서버에서 읽은 annotation의 완비와 대상 연결을 검사하는 작은 경계만 둔다. 동일 reviewer·workflow/output·rubric의 다섯 criterion, non-empty comment, 고정 Config, 사람 annotation provenance를 확인한다. 중복을 임의로 최신 값 하나로 덮거나 여러 사람의 일부 점수를 합쳐 한 사람의 완비 평가로 만들지 않는다. 채택 의견은 candidate와 양쪽 run/output에 연결한다.

기존 `value.py`의 평가·비교·delta·합계·Markdown 렌더링 모델과 전용 재수출·golden은 제거한다. 같은 기능의 alias·loader를 다른 module에 다시 만들지 않는다. 독립 수치 oracle·세 사례 corpus·workflow 충돌·원문 digest 회귀는 현재 얇은 검사와 collection 경계에서 유지한다. 점수 관리·집계·대조 화면은 Langfuse가 소유한다.

### D5. Current Contract Synchronization

구현과 검증 후 정본 Purpose의 현재 외부 연동 설명과 delta의 네 수정 요구사항·세 추가 요구사항을 함께 반영한다. 현재 계획 작성만으로 기존 raw 전송 금지가 구현된 사실이라고 바꾸지 않는다. 실제 원격 조회·UI와 사람이 입력한 평가의 검증 상태는 로컬 구현 검사와 별도로 남긴다.
