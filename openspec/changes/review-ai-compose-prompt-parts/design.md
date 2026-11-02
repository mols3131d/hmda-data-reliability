---
type: openspec-spec-driven-tdd-design
category: design
title: Compose Review AI Prompt Parts
description: 책임별 모듈과 정적 조합을 정의하고 기존 메시지 바이트를 보존해 provider에 전달합니다.
---

## Technical Delta

`prompt/__init__.py`의 `_PROMPT_PARTS`에 version별 Markdown 상대 경로 tuple을 고정한다. Version은 완성된 조합의 식별자이며 각 모듈에 별도 version을 붙이지 않는다. 조합과 canonical input은 최종 `ChatMessage`를 만드는 renderer에서 만난다.

## Module Boundaries

| Area | Responsibility / reuse boundary |
| --- | --- |
| `tasks/` | HMDA `null_spike` 검토 역할·범위·입력 취급. 같은 작업을 하는 조합에서 공유한다. |
| `policies/` | Review AI의 한국어 필드·원문 보존과 자문 경계. 현재 Review AI 조합 사이에서 공유하며 범용 agent 정책으로 승격하지 않는다. |
| `output/` | 동일 typed output 계약에 대한 간략/상세 설명 중 하나를 선택한다. Schema의 정본은 기존 contract다. |
| `guidance/` | 수치, 근거·초안, 검토 가치 등 독립적으로 개선·비교할 판단 지침이다. |
| `examples/` | 선택한 출력 계약을 따르는 형식 예시다. 실제 사례 데이터는 포함하지 않는다. |
| `titles/` | 조합의 표시 제목이다. 작업 규칙과 사례 데이터를 소유하지 않는다. |

기존 `common/role.md`는 `tasks/null_spike.md`, `common/language.md`와 `common/advisory.md`는 `policies/`, 형식 예시는 `examples/utility_contributions.md`로 옮긴다. 작업·출력 필드에 결합된 모듈을 '모든 agent에 공통'이라고 해석하지 않도록 책임을 경로로 드러낸다.

짧은 문장을 기계적으로 분리하지 않는다. 수정 이유, 적용 범위 또는 조합 선택이 독립적일 때 모듈을 나누고, 의미와 입력 전제가 같을 때 같은 파일을 참조한다. 모듈 안의 include, 중첩 조합, 파일 자동 탐색이나 외부 입력이 선택하는 경로는 도입하지 않는다.

## Assembly And Handoff

제목 → 작업 → 언어 정책 → 출력 설명 → 선택한 지침·예시 → 자문 정책 순서로 명시한 조각을 한 번씩 읽는다. 출력 설명은 조합마다 하나이며 지침과 예시는 그 출력 필드·열거값을 전제로 한다. 충돌은 조합 작성 시 해결하며 뒤의 조각이 앞의 규칙을 덮어쓰는 관례를 두지 않는다.

각 조각은 기존 섹션에서 추출해 마지막 LF 하나를 유지한다. 로더는 원문 사이에 LF 하나를 넣어 기존 섹션 사이의 빈 줄을 재현한다. 본문을 `strip()`하거나 Markdown을 변환하지 않는다. 기존 세 메시지 digest를 변경하지 않고 조립 전후의 전체 문자열도 대조한다.

조립된 Markdown 전체는 system 메시지 하나가 된다. 사례별 `Incident`, `Evidence`, `RemediationDraft`는 bounded canonical projection을 거쳐 `UNTRUSTED_CANONICAL_INPUT_JSON`으로 시작하는 별도 user 메시지가 된다. 데이터로 조합·경로·지시문을 선택하거나 system 본문을 치환하지 않는다.

Renderer는 두 메시지의 canonical 직렬화에 byte cap과 digest를 적용한다. `review_null_spike()`는 반환된 `messages`를 `ReviewProvider.invoke()`에 전달하고 Runtime AI가 provider 요청으로 변환한다. Provider가 Markdown 파일이나 README를 읽는 구조가 아니다. 현재 조각은 import 시 로드하므로 수정 후 새 process에서 렌더링한다.

## Documentation Ownership

모듈·조립 불변 조건은 `review-ai-prompt-engineering` Spec이 소유한다. `docs/development/review-ai-prompts.md`는 분할 이유, 재사용 판단, 실제 메시지 확인과 수정 절차를 설명한다. `prompt/README.md`는 편집 진입점과 owning source 링크를 제공하고 정확한 조합 목록은 `_PROMPT_PARTS`에만 둔다.

## Lifecycle

단일 active 기본값은 채택 변경이 충족해야 할 lifecycle이다. 이번 구조 분리에서는 현재 API v1과 live v2를 유지한다. 과거 실행의 명시된 identity와 revision은 미래 기본값과 분리한다.
