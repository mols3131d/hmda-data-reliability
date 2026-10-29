---
type: openspec-spec-driven-tdd-design
category: design
title: Retain Provider Responses
description: 기존 원자적 create-only 저장 경계를 재사용하는 응답 보존 구조를 설명합니다.
---

## Technical Delta

`InvocationResponseStore`는 기존 evidence store의 원자적 파일 쓰기를 재사용한다. 기존 invocation JSON schema와 custom evidence writer protocol은 변경하지 않는다. 응답 경로는 invocation identity로 연결하고 `AgenticReviewResult.response_path`에 제공한다. 기존 record에 sidecar가 없으면 임의로 생성하거나 복원하지 않는다.

Service는 provider 반환 직후 응답을 저장한 다음 parse/guard를 수행한다. 별도 response 파일이므로 실패 원문이 Pydantic 진단이나 외부 projection으로 흘러가지 않는다. UTF-8 byte bound와 파일 권한은 기존 evidence 저장 경계와 같게 유지한다. Runtime에서 이미 차단한 oversized 본문은 이 경계에 도달하지 않는다.
