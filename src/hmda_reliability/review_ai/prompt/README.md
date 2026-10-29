# Review AI Prompt Parts

일반 API와 live CLI는 현재 한국어 단계별 프롬프트를 사용한다. 프롬프트 version을 고르지 않으며 모델이 텍스트로 답하면 코드가 결과 JSON을 취합한다. 편집·재사용 절차는 [Prompt Composition](../../../../docs/development/review-ai-prompts.md)을 따른다. 이 README는 모델에 전달하지 않는다.

## Current Parts

| Directory | Responsibility |
| --- | --- |
| [tasks/](tasks/) | 사고 유형에 결합된 검토 역할·입력 취급 |
| [policies/](policies/) | 한국어·식별자 보존과 자문 정책 |
| [output/prose.md](output/prose.md) | 일반 텍스트 응답과 이전 답변의 취급 |
| [guidance/](guidance/) | 수치·근거·초안 검토 지침 |
| [staged/](staged/) | 근거 검토·초안 비판·종합의 고정 질문 |

현재 조합은 [staged/prompt.py](../staged/prompt.py)가 소유한다. 고정된 모듈의 system 지시문과 별도 user 사례 입력, 이전 assistant 답변을 함께 전달한다. 전체 메시지 배열에 byte cap과 digest를 적용하며 사례 데이터가 모듈을 선택하지 않는다. 모듈은 import 시 로드하므로 편집 뒤에는 새 process에서 확인한다.

## Lifecycle

현재 실행 경로의 workflow identity `staged-v1`은 출처 기록용이며 현재 프롬프트를 선택하는 환경 설정은 없다. 일반 진입점의 선택 원칙은 [Prompt lifecycle and active default](../../../../openspec/specs/review-ai-prompt-engineering/spec.md#requirement-prompt-lifecycle-and-active-default)가 소유한다. 실행 경로의 통일은 실제 모델 품질이 검증됐다는 의미가 아니다.
