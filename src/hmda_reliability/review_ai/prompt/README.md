# Review AI Prompt Parts

프롬프트를 수정할 때는 아래 책임별 Markdown 조각을 편집한다. 이 안내서는 모델에 전달되지 않는다. 실제 조립 순서는 [__init__.py](__init__.py)의 `_PROMPT_PARTS`가 정의한다.

## Parts

| Directory | Responsibility |
| --- | --- |
| [titles/](titles/) | version별 제목 |
| [common/](common/) | 공유하는 [역할·범위](common/role.md), [한국어 출력·원문 보존](common/language.md), [자문 경계](common/advisory.md) |
| [output/](output/) | v1의 [간략 출력 계약](output/compact.md), v2/v3의 [상세 출력 계약](output/structured.md) |
| [guidance/](guidance/) | [v2 형식 예시](guidance/utility_examples.md), v3의 [수치 보존](guidance/numeric_fidelity.md)·[근거와 초안 검토](guidance/evidence_review.md)·[검토 가치](guidance/review_value.md) |

## Composition

모든 version은 **제목 → 공통 역할 → 공통 언어 → 아래 version별 부분 → 공통 자문 경계** 순서로 조립한다.

| Version | Version-specific parts |
| --- | --- |
| `v1` | 간략 출력 계약 |
| `v2` | 상세 출력 계약 → 기여의 형식 예시 |
| `v3` | 상세 출력 계약 → 수치 보존 → 근거와 초안 검토 → 검토 가치 |

각 조각은 마지막 LF 하나를 포함한다. 로더는 원문 사이에 LF 하나를 넣어 섹션 사이의 빈 줄을 만든다. 공백을 제거하거나 Markdown을 변환하지 않으며, 조립한 전체 본문이 system 메시지와 digest의 기준이다. 공통 조각을 수정하면 이를 참조하는 모든 version에 반영되므로 영향받는 조합을 함께 검증한다.

User 메시지에는 별도로 canonical input JSON을 넣는다. 모델 응답은 기존 JSON 객체 하나이며, 프롬프트의 Markdown 형식과 구별한다.

## Lifecycle

현재 v1·v2·v3는 개발 단계의 기존 동작·비교 기준·개선 후보를 구분한다. 검증·채택 이후에는 API와 live harness의 기본 경로를 하나의 active version으로 통일해야 한다. 이전 version은 명시적 비교·과거 실행 재현용으로 관리한다.

지금은 채택 판단 전이므로 API 기본 v1과 live 기본 v2를 유지한다. 채택과 기본값 전환의 정본은 [Prompt lifecycle and active default](../../../../openspec/specs/review-ai-prompt-engineering/spec.md#requirement-prompt-lifecycle-and-active-default)이며, 실제 출력의 비교·평가 절차는 [Review AI Evaluation](../../../../docs/development/review-ai-evaluation.md)을 따른다.
