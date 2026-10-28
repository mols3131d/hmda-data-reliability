# Review AI Prompt Parts

프롬프트를 수정할 때는 해당 책임의 Markdown 모듈을 편집한다. 모듈별 책임·재사용 판단·최종 메시지 확인 절차는 [Prompt Composition](../../../../docs/development/review-ai-prompts.md)을 먼저 읽는다. 이 안내서는 모델에 전달되지 않는다.

기본 live의 단계별 텍스트 경로는 [staged/](staged/)의 질문과 [output/prose.md](output/prose.md)를 사용한다. 단계 조합은 [staged/prompt.py](../staged/prompt.py)가 소유한다. 아래 version 조합은 명시적인 structured 비교·재현 경로다.

## Parts

| Directory | Responsibility |
| --- | --- |
| [tasks/](tasks/) | 사고 유형에 결합된 검토 역할·범위와 입력 취급 |
| [policies/](policies/) | Review AI 조합 사이에 공유하는 한국어·원문 보존과 자문 정책 |
| [output/](output/) | v1의 [간략 출력 계약](output/compact.md), v2/v3의 [상세 출력 계약](output/structured.md) |
| [guidance/](guidance/) | 수치 보존, 근거·초안 충실성과 검토 가치의 판단 지침 |
| [examples/](examples/) | 출력 계약에 맞춘 형식 예시 |
| [titles/](titles/) | version별 조합 표시 제목 |

## Composition

Version은 사용할 모듈과 순서를 정하는 조합이다. 정확한 파일 목록은 [__init__.py](__init__.py)의 `_PROMPT_PARTS`가 소유한다. 제목 → 작업 → 언어 정책 → 출력 설명 → 선택한 지침·예시 → 자문 정책 순서로 조립한다.

각 모듈은 마지막 LF 하나를 포함한다. 로더는 원문 사이에 LF 하나를 넣어 섹션 사이의 빈 줄을 만든다. 공백을 제거하거나 Markdown을 변환하지 않는다. 공통 모듈 수정은 모든 참조 조합에 영향을 준다. import 시 로드하므로 편집 후 새 process에서 확인한다.

조립한 본문은 system 메시지 하나가 되고 canonical input JSON은 별도 user 메시지에 넣는다. 전체 메시지 배열의 canonical UTF-8 바이트에 크기 제한과 digest를 적용한 뒤 provider에 전달한다. 모델 응답은 기존 JSON 객체 하나다.

## Lifecycle

현재 다중 version은 개발 비교용이며 검증·채택 후 일반 실행의 기본 조합은 하나로 통일한다. 채택·과거 재현의 정본은 [Prompt lifecycle and active default](../../../../openspec/specs/review-ai-prompt-engineering/spec.md#requirement-prompt-lifecycle-and-active-default), 현재 기본값과 평가 절차는 [Review AI Evaluation](../../../../docs/development/review-ai-evaluation.md)을 따른다.
