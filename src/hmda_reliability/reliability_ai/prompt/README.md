# Reliability AI Prompt Seeds

이 디렉터리는 Langfuse Prompt Management에 명시적으로 등록하는 한국어 Markdown 자료다. **실행 정본은 native chat prompt와 참조된 text prompt version이다.** 일반 API·위임·실험은 seed를 직접 조립하거나 fallback으로 사용하지 않는다. 모델은 도구 조회 또는 최종 JSON 보고를 선택하고 코드는 canonical facts와 narrative를 구분한다.

## Parts

| Directory | Responsibility |
| --- | --- |
| [investigation.md](investigation.md) | 조사·도구·종료·최종 보고 구조 |
| [policies/](policies/) | 한국어·식별자 보존과 자문 경계 |
| [guidance/](guidance/) | 수치·근거·초안 검토 지침 |

[명시적 setup](../evaluation/setup.py)은 다섯 파일을 `hmda-reliability-ai/components/<상대 경로에서 .md 제거>` text prompt로, `hmda-reliability-ai/investigation`을 chat prompt로 등록한다. System의 version-pinned reference, canonical input user 메시지, `history` placeholder를 사용한다.

## Lifecycle

최초 등록 후 운영 편집·version·기본 `production` label은 Langfuse에서 관리한다. 실행은 시작에 읽은 prompt 객체를 고정하고 실제 name/version·compiled message digest를 기록한다. 원격 조회가 실패하면 `prompt_unavailable`로 끝나며 로컬 seed를 대신 실행하지 않는다. Setup 재실행은 새 version이나 Dataset item을 만들 수 있으므로 반복 실험 전마다 실행하지 않는다.

작성·재사용·대화 전달은 [Prompt Guide](../../../../docs/development/review-ai-prompts.md), 등록·실험·사람 평가는 [Evaluation Guide](../../../../docs/development/review-ai-evaluation.md)를 따른다. 이 README는 모델에 전달하지 않는다. 과거 package·고정 stage 실행은 지원하지 않는다.
