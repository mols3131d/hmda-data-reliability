---
type: openspec-spec-driven-tdd-design
category: design
title: Langfuse Projection Boundary
description: SDK 종료 격리와 합성 입력의 field mapping을 결정한다.
---

## Technical Delta

입력 계약은 [delta Spec](specs/reliability-agentic-review/spec.md)을 따른다. SDK 4.15.6의 request timeout은 queue join과 전체 shutdown을 제한하지 못하므로 `subprocess.run`의 timeout으로 단기 child 전체를 제한한다. SDK와 private TracerProvider는 child 안에서만 생성한다. Credential은 argv/stdin payload에 넣지 않고 명시적인 child environment로 전달한다. Child는 `LANGFUSE_MEDIA_UPLOAD_ENABLED=false`를 고정해 base64 data URI의 자동 media 변환과 별도 업로드를 막고 digest 대상 output 문자열을 보존한다. SDK log는 노출하지 않는다.

`review_ai.langfuse_projection`이 projection, child 실행과 integration-local completeness를 소유한다. Harness는 provenance 검증 뒤 현재 synthetic input을 다시 canonicalize하여 record와 비교한다. Public core API와 evidence schema는 그대로 둔다. Child는 local invocation file을 다시 읽지 않고 검증된 payload만 stdin으로 받는다.

| Surface | Mapping |
| --- | --- |
| Accepted input | `incident`, `deterministic_facts`, `draft`, `evidence`, `review_context`; 현재 harness가 만든 canonical input과 완전히 일치해야 한다. Field 값은 fixture의 bounded payload이며 임의 record를 받는 범용 exporter가 아니다. |
| Accepted output | 현재 `AgenticReviewOutput`의 declared fields와 `utility_output_digest()`; extra field는 model contract가 거부한다. |
| Metadata | invocation/revision, prompt template/version/digest, rubric, output digest, status, validation policy/status, model과 numerical limits, recorded_at, latency_ms, attempt_count, usage의 declared counters. |
| Failed record | invocation/revision와 closed status만. `failure_code`는 자유 문자열이므로 전송하지 않는다. |
| Size | JSON UTF-8 65536 bytes; 초과하면 생략하며 truncate하지 않는다. |
| Identity | projection 전체 canonical JSON의 SHA-256 앞 32자리로 trace ID를 결정한다. 변경된 output/config/input이 같은 remote trace를 덮어쓰지 않는다. 같은 projection의 재시도에는 같은 trace ID를 쓴다. |

Observation은 `review-ai-post-hoc-projection` span이며 duration은 export 작업을 뜻한다. 실제 model 시간은 `recorded_latency_ms`에만 둔다. SDK optional extra는 exact version으로 고정한다. SDK init이 root logger 또는 exporter를 구성하더라도 parent에는 전파되지 않는다.

Human score config는 수동으로 만든다. `annotation_complete`는 호출자가 제공한 accepted payload에서 `AgenticReviewOutput`을 다시 검증하고, model 정규화 전후의 output을 canonical JSON 값과 타입까지 비교한 뒤 digest와 고정 rubric, target 및 score shape를 확인한다. Remote fetch, 파일 저장 또는 평가 import는 수행하지 않는다. `RubricScore`를 재사용하되 bool/string/fraction coercion을 사전에 거부한다.
