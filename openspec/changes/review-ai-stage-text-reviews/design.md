---
type: openspec-spec-driven-tdd-design
category: design
title: Stage Review AI Text Responses
description: 기존 단회 출력과 분리한 고정 세 단계, 원문 저장과 코드 조립 구조를 정의합니다.
---

## Technical Delta

`review_ai/staged/`에 typed collection 계약·프롬프트 렌더러·실행 service·로컬 저장 책임을 둔다. 기존 canonical projection, Runtime AI와 원문 저장소를 재사용한다. 기존 `review_null_spike()`와 v1/v2/v3 bytes·record는 보존한다.

새 공개 실행은 `review_null_spike_staged()`다. `StagedReviewOutput`은 원입력 identity·target·deterministic facts와 `stages[{stage_id,text}]`를 소유한다. Code가 JSON을 직렬화하며 모델 prose에서 기존 finding kind·evidence refs·priority·advisory enum을 추출하지 않는다. `completed`는 수집과 로컬 저장 완료를 의미한다.

## Message And Runtime Boundary

Runtime `ChatMessage`에 assistant를 추가하고 `invoke(..., output_format="text")`를 제공한다. 기본 `json_object`는 유지한다. Text 요청은 wire와 SDK 양쪽에서 response_format을 생략한다.

단계 순서는 evidence_review → draft_critique → synthesis다. 각 단계의 신뢰된 system은 공유 작업·텍스트 출력·자문 정책, 관련 guidance와 고정 질문 모듈로 구성한다. 최초 canonical JSON은 user 데이터, 성공한 이전 응답은 assistant 자료다. 단계 지시는 system이 소유하므로 현재 user 전체가 untrusted라는 작업 정책과 충돌하지 않는다. 각 요청 전체를 canonical 직렬화해 byte cap·digest를 계산한다.

고정 세 단계와 Runtime의 per-call bounded retry만 허용한다. 물리 호출 상한은 `3 * (max_retries + 1)`, 생성 토큰 상한은 그 물리 호출 상한과 per-call cap으로 제한된다. Workflow 자체의 repair/retry loop는 없다. 알려진 `length`, content filter·tool completion과 빈/공백 답변은 원문 보존 후 실패로 종료한다.

## Storage And Failure

단계 raw는 기존 create-only `InvocationResponseStore`를 이용해 run ID와 단계 ID로 분리한다. JSON parsing을 하지 않고 text를 exact 보존한다. Runtime이 본문을 반환하기 전 차단한 oversized·unavailable 응답에는 raw가 없다.

별도 staged manifest에는 canonical input, 설정·revision, 단계별 요청 digest·response digest·상태·원문 경로·usage·attempt·latency와 최종 collection digest/path를 기록한다. Raw text는 최종 collection JSON에만 담고 sanitized manifest에는 넣지 않는다. 두 JSON은 기존 invocation record와 다른 디렉터리/계약이다. Create-only atomic private 저장 구현을 재사용하며 별도 public bounded JSON 저장 entrypoint를 제공한다.

실패하면 후속 단계를 호출하지 않고 완료 단계의 raw와 기록을 보존한다. 결과 JSON 저장이나 manifest 저장 실패도 성공을 반환하지 않으며 생성된 경로를 결과에 남긴다. Manifest는 각 단계가 끝날 때 별도 create-only 단계 기록으로 checkpoint하고 마지막에 run record를 생성한다. 실행 identity 충돌은 호출 전에 거부한다.

## Live Entry

기존 live script에서 mode 생략 시 staged 경로를 선택한다. `HMDA_AGENTIC_REVIEW_MODE=structured`는 기존 흐름을 선택하며 기존 prompt version 설정은 이 경로에 적용한다. Staged는 고정 workflow identity `staged-v1`를 기록한다. 기존 Langfuse projection을 새 collection에 적용하지 않고 명시적인 skipped 상태로 보고한다. 콘솔에는 완료·실패 상태와 파일 경로를 제공하고 원문은 로컬 결과 파일에서 확인한다.
