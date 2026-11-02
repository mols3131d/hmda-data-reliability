---
type: openspec-spec-driven-tdd-design
category: design
title: Unify Current Review Prompt
description: 현재 단계 실행과 평가를 연결하고 과거 구현·기록 reader·선택 설정을 제거합니다.
---

## Technical Delta

일반 공개 API·직접 service·live CLI는 현재의 동일한 세 단계 실행을 사용한다. `staged-v1`은 코드가 조립한 collection의 schema identity이며 prompt version selector가 아니다. Runtime의 범용 출력 모드 기능은 유지하지만 Review AI는 text mode만 요청한다.

기존 legacy service와 prompt/legacy 전체, `PromptIdentity`와 `prompt_identity`, JSON 응답용 output/result/validation 계약·파서·validator 및 `AgenticInvocationEvidence`와 그 reader를 제거한다. Root 공개 API에서도 이 타입을 내보내지 않는다. Immutable input validation·canonical projection·bounded context·sanitized runtime 설정·raw response store·atomic JSON writer는 현재 실행에서 계속 사용한다.

현재 workflow reservation은 현재 workflow directory와 원문 경로의 충돌을 provider 호출 전에 검사한다. 과거 invocation record와의 호환 검사는 제거한다. UTF-8 원문을 공백·개행까지 정확히 저장하고, 실패하면 이전 원문과 checkpoint를 남기며, 시간·시도 수·digest와 적용 설정을 현재 manifest에 기록한다. 현재 manifest에는 실행 예산과 경과 시간이 필수이며 이전 record의 미기록 필드를 받아들이는 loader를 유지하지 않는다.

평가 API는 `StagedReviewOutput`을 직접 사용하고 대상과 비교 대상의 identity를 `workflow_id`로 명시한다. `rubric_v1`의 다섯 criterion·0–2 score·근거·human decision·동일 사례/facts/revision 경계는 유지한다. Output digest는 단계 순서·텍스트·공백·개행을 포함한 canonical JSON을 식별하고 manifest와 동일해야 한다. Invocation 기반 과거 comparison을 읽는 alias·union·변환 loader는 두지 않는다. 독립적인 현재 형식 golden fixture로 serialized contract를 확인한다.

기존 structured 결과 전용 Langfuse projection과 annotation mapping 및 CLI export 분기를 삭제한다. 현재 단계 결과용 projection을 새로 구현하지 않는다. 현재 모델·credential·transport/runtime boundary는 변경하지 않는다.

CLI는 mode·prompt version·과거 export 변수를 읽지 않는다. 삭제된 설정을 해석하는 별도 guard·안내·fallback도 두지 않는다. 현재 활성화·연결/읽기 제한·단계/전체 예산·출력 한도·provenance 검증은 유지한다. 환경 예제와 로컬 설정의 선택 플래그는 제거하되 사용자 credential 값을 문서·로그에 노출하지 않는다.

과거 원문·invocation JSON·Inbox·Git 기록은 삭제하지 않는다. 현재 source가 과거 파일의 replay를 지원하지 않더라도 기록한 revision으로 출처를 조사할 수 있다. 현재 실행의 completed와 offline 회귀 통과를 실제 모델의 언어 준수·정확성·검토 가치의 채택으로 해석하지 않는다.
