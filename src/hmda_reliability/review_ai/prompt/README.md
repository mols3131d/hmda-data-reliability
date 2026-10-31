# Review AI Prompt Seeds

이 디렉터리는 Langfuse Prompt Management에 최초 등록하는 한국어 Markdown 자료다. **실행 정본은 Langfuse의 chat prompt와 참조된 text prompt version이다.** 일반 API와 실험은 native prompt를 읽으며 이 파일을 직접 조립하거나 fallback으로 사용하지 않는다. 모델은 텍스트로 답하고 코드가 JSON을 취합한다.

## Parts

| Directory | Responsibility |
| --- | --- |
| [tasks/](tasks/) | 사고 유형·역할·입력 취급 |
| [policies/](policies/) | 한국어·식별자 보존과 자문 경계 |
| [output/prose.md](output/prose.md) | 일반 텍스트 출력과 이전 답변 취급 |
| [guidance/](guidance/) | 수치·근거·초안 검토 지침 |
| [staged/](staged/) | 세 단계의 개별 질문 |

[최초 setup](../evaluation/setup.py)은 각 파일을 `hmda-review-ai/<상대 경로에서 .md 제거>` text prompt로 등록한다. 세 chat prompt는 `hmda-review-ai/evidence_review`, `hmda-review-ai/draft_critique`, `hmda-review-ai/synthesis`다. 공통 system reference·history placeholder·현재 질문 reference를 사용하며 reference는 실제 text version에 고정한다.

## Lifecycle

최초 등록 후 운영 편집·version·기본 `production` label은 Langfuse에서 관리한다. 실행은 시작에 읽은 prompt 객체를 고정하고 실제 name/version·compiled message digest를 기록한다. 원격 조회가 실패하면 `prompt_unavailable`로 끝나며 로컬 seed를 대신 실행하지 않는다. Setup 재실행은 새 version이나 Dataset item을 만들 수 있으므로 반복 실험 전마다 실행하지 않는다.

작성·재사용·config·대화 전달은 [Prompt Guide](../../../../docs/development/review-ai-prompts.md), 등록·실험·사람 평가는 [Evaluation Guide](../../../../docs/development/review-ai-evaluation.md)를 따른다. 이 README는 모델에 전달하지 않는다. 과거 v1/v2/v3나 별도 mode의 실행 지원은 제공하지 않는다.
