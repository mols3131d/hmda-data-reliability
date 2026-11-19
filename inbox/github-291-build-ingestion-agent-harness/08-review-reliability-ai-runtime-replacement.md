---
type: review
title: Reliability AI Runtime Replacement Design Review
description: PR 291의 07 설계 번들에 대한 독립 검토, 토론과 수정 근거를 기록합니다.
---

# Reliability AI Runtime Replacement Design Review

> [!NOTE]
> **Clear.** 두 독립 검토자가 최종 설계에서 구현을 막는 문서상의 충돌을 찾지 못했다. 실행에서 확인할 항목은 [구현 완료 기준](07-design-reliability-ai-runtime-replacement/migration-and-verification.md#acceptance-evidence)에 적었다.

- **Target** [07 설계 번들](07-design-reliability-ai-runtime-replacement/README.md)의 Markdown 파일 4개
- **Revision** 로컬 코드 `90bbbe668313baf35470416581d5c8642e9c6996`. 번들 SHA-256은 아래 검토 차수에 기록했다.
- **Scope** 사고 조사 실행부 교체, 제공자와 기존 호출의 호환, 복구 권한, 원문 보존·재현, 후속 적재 조사 연결

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 Major | 기존 제공자 주입과 호환 설정을 함께 넣을 때 선택이 모호했다. | API에서 주입을 우선한다. CLI의 명시적 호환 연결, 기본 로컬 Codex와 제공자별 재시도 규칙을 명시했다. [제공자 계약](07-design-reliability-ai-runtime-replacement/provider-and-evidence.md#provider-contract) |
| F2 | 🟠 Major | 적재의 규칙 완료 분기가 사고 조사에도 적용될 수 있었다. 첫 조회 뒤 새 모델 턴으로 넘어가면 배치의 나머지 요청을 잃는다. | 사고 조사는 모델 보고서 검증과 저장으로 완료한다. 같은 턴의 조회를 순서대로 처리하고, 한도 초과 전까지의 근거를 회수한다. [조사 흐름](07-design-reliability-ai-runtime-replacement/architecture.md#investigation-workflow) |
| F3 | 🟠 Major | Codex 스레드의 문맥과 그래프 입력이 겹칠 수 있었다. 실행 권한·요청 수락 여부·종료를 검증할 조건도 부족했다. | 턴마다 임시 스레드를 열고 실제 앱 입력의 크기와 digest를 기록한다. 격리 확인, 수락 여부에 따른 재시도, 기한 안의 저장을 명시했다. [Codex와 기한](07-design-reliability-ai-runtime-replacement/provider-and-evidence.md#codex-and-ollama) |
| F4 | 🟠 Major | 최종 파일 쓰기에 실패하면 도구 결과 참조가 사라질 수 있었다. 응답·시간만으로는 프롬프트와 저장 실패를 재현할 수 없다. | 원문과 도구 결과를 독립적으로 보존하고, 고정 입력과 기록한 저장 결과를 재현에 공급한다. [근거와 재현](07-design-reliability-ai-runtime-replacement/provider-and-evidence.md#evidence-and-replay) |
| F5 | 🟡 Minor | Codex 한 턴의 성공과 실험 완료만으로는 실제 조회 연결, 원격 관측과 저장량 절감을 확인하기 어려웠다. | 후속 턴에서 조회 결과를 사용하는 실실행, Dataset·턴 관측의 재조회, 동일한 합성 사례의 전체 로컬 저장량 비교를 정의했다. [완료 기준](07-design-reliability-ai-runtime-replacement/migration-and-verification.md#acceptance-evidence) |

## Discussion and Re-review

구현 일관성과 실패·권한 경계를 서로 다른 새 서브에이전트가 읽기 전용으로 검토했다. 전용 리뷰 역할의 호출이 지원되지 않아 별도 컨텍스트 두 개를 사용했다. 검토자들은 초기 결과를 독립적으로 제출한 뒤 서로의 근거와 반대 제안을 메시지로 검토했다.

한 조사에서 Codex 스레드를 이어 쓰면 재전송량을 줄일 수 있다. 전체 이력을 다시 보내면 문맥이 겹칠 수 있고, 변경분만 보내면 앱이 실제 입력의 전체 한도와 재현 기준을 증명하기 어렵다. 두 검토자가 재검토한 안은 App Server 연결과 인증을 재사용하고 매 시도에 새 임시 스레드를 사용하는 것이다. 재전송량과 지연은 구현 후 같은 조건에서 측정한다.

| 검토 차수 | 번들 SHA-256 | 결과 |
| --- | --- | --- |
| 최초 독립 검토 | `9eee17397ca11a0ade8e8069e248dacb34e7b3803e37e6a07d971d8e91087549` | 제공자 선택, 조사 완료, 격리·기한, 기록, 평가와 측정 조건 수정 |
| 첫 재검토 | `602ce9641a846e7e4497024645a979bee72cf62bfefdcd7d07d9f0ec12c046f2` | 배치 처리, 주입 우선순위, 프롬프트·저장 결과 재현을 보완했다. 호환 연결은 기존 재시도 분류를 적용한다. |
| 최종 독립 검토 | `7f3286d36340c75675c2068b7ee88db2a947d9aa08a9cbb5c0b01e08e860b9ac` | 두 검토자 모두 `clear` |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 원본과 계약 대조 | [현재 조사와 복구 명세](../../openspec/specs/reliability-agentic-review/spec.md), [호환 제공자 코드](../../src/hmda_reliability/runtime_ai/provider.py) |
| ✅ Pass | 번들 형식과 다이어그램 | `rumdl`, Inbox 검증과 로컬 Mermaid SVG 렌더링 |
| ⚪ Not Verified | 앱 구현과 실실행 | Codex OAuth와 Ollama의 실실행, 원격 관측, 저장량과 지연 비교는 [구현 검증](07-design-reliability-ai-runtime-replacement/migration-and-verification.md#acceptance-evidence) 항목으로 남겼다. |
