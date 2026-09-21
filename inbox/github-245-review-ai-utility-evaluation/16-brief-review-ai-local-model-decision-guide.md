---
type: brief
title: "Review AI Local Model Decision Guide"
description: "7B급 로컬 모델 환경에서 Review AI를 개선할 때 반드시 기억해야 할 판단 원칙과 작업 순서를 짧게 정리합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
  - "brief"
  - "local-llm"
  - "decision-guide"
---

# Review AI Local Model Decision Guide

## What Matters Most

현재 문제를 곧바로 "7B 모델이 너무 작다"고 결론내리면 안 된다. 지금 모델은 한 번의 호출에서 deterministic facts 복사, evidence reference 준수, 조사 우선순위 판단, uncertainty 표현, remediation critique, recommendation 작성과 structured JSON 계약 준수까지 동시에 요구받는다.

따라서 먼저 물어야 할 질문은 모델 크기가 아니라 다음이다.

> 작은 모델에게 한 번에 너무 많은 책임을 맡기고 있는가?

더 큰 모델을 쓰기 어려운 제약은 multi-call을 검토할 이유는 되지만, multi-call을 자동으로 정답으로 만들지는 않는다.

## Five Points to Remember

### 1. Separate Formatting Failure from Reasoning Failure

`response_schema_invalid`가 발생했다고 해서 모델의 판단이 나빴다고 바로 결론내리지 않는다. 마크다운 펜스나 JSON 형식 문제라면 이는 reasoning 문제가 아니라 parser 또는 structured-output 경계 문제다.

따라서 순서는 다음이어야 한다.

```text
format / parser 문제 해결
        ↓
schema-valid live output 확보
        ↓
실제 내용 평가
        ↓
내용이 부족할 때 reasoning 구조 개선
```

[14 plan](14-plan-review-ai-json-markdown-fence-sanitization.md)은 이 첫 단계를 다룬다.

### 2. Reduce Work Before Adding Calls

현재 모델은 Python이 이미 알고 있는 값까지 다시 출력한다.

```text
incident_id
target_column
baseline_null_rate
current_null_rate
delta
threshold
```

이 값은 LLM의 추론 결과가 아니다. 가능하다면 Python이 계속 소유하고, LLM은 사람이 필요한 semantic judgment에 집중시키는 것이 더 단순하다.

핵심 원칙은 다음이다.

```text
Python
→ 사실, identity, evidence boundary

LLM
→ 조사 우선순위, 중요한 uncertainty, remediation critique
```

추가 호출 없이 output contract를 줄여 같은 개선을 얻을 수 있다면 multi-call보다 이 방법을 우선한다.

### 3. Treat Two-Stage Reasoning as an Experiment

Single-call을 단순화한 뒤에도 실제 utility가 부족할 때 two-stage를 실험한다.

권장되는 분리는 evidence source별 분할이 아니라 판단 책임별 분할이다.

```text
Stage 1
Investigation Prioritization

"무엇을 먼저 확인해야 하는가?"
        ↓
Stage 2
Remediation Critique

"그렇다면 현재 remediation draft의 무엇이 부족한가?"
```

이 방식은 작은 모델에게 더 많은 지식을 주는 것이 아니라 한 번에 풀어야 하는 문제를 작게 만든다.

### 4. Never Promote LLM Reasoning to Evidence

Stage 1의 결과는 Stage 2에서 참고할 수 있지만 Evidence가 아니다.

예를 들어 Stage 1이 "upstream source change를 먼저 확인할 가치가 있다"고 판단했더라도 이는 확인된 root cause가 아니다.

반드시 다음 경계를 유지한다.

```text
LLM intermediate output ≠ Evidence
LLM intermediate output ≠ deterministic fact
LLM intermediate output ≠ confirmed root cause
```

Stage 2에는 deterministic facts, supplied evidence와 LLM prior notes를 구분해서 전달해야 한다. Evidence ID 위조, numeric contradiction과 authority escalation은 기존 deterministic guard가 계속 차단한다.

### 5. Keep Complexity Only When Human Utility Pays for It

Two-stage는 호출 수, latency, token usage, failure surface와 provenance complexity를 늘린다. 따라서 답변이 더 길거나 그럴듯해졌다는 이유만으로 유지하면 안 된다.

다음 질문에 실제로 더 좋은 답을 줄 때만 채택한다.

- 사람이 다음에 무엇을 조사해야 할지 더 명확해졌는가?
- 이미 알려진 facts 또는 context gap을 반복하는 수준을 넘어섰는가?
- 중요한 uncertainty를 더 잘 좁혔는가?
- RemediationDraft의 실제 누락이나 위험을 더 잘 찾았는가?
- 추가 latency를 감수할 만큼 도움이 되는가?

같은 효과를 더 단순한 single-call contract로 얻을 수 있다면 single-call을 선택한다.

## Recommended Order

현재 권장 작업 순서는 다음과 같다.

```text
1. Parser / formatting 안정화
        ↓
2. Single-call accepted output 확보
        ↓
3. 사람이 실제 utility 평가
        ↓
4. 필요하면 LLM output responsibility 축소
        ↓
5. 다시 human utility 평가
        ↓
6. 여전히 부족할 때만 two-stage 실험
        ↓
7. 같은 model / case / rubric으로 비교
        ↓
8. utility gain이 complexity cost를 넘을 때만 채택
```

현재 PR #245 안에서 multi-call architecture까지 확장하지 않는다. 먼저 현재 live path와 기존 blocker를 닫고, single-call의 실제 한계를 관찰한 뒤 별도 change에서 실험하는 것이 적절하다.

## Decision Rule

가장 중요한 판단 규칙은 두 문장으로 정리할 수 있다.

> 작은 모델을 큰 모델처럼 만들려고 하지 않는다. 작은 모델이 잘할 수 있을 만큼 문제를 작게 만든다.

그리고 문제를 작게 만드는 방법도 가장 싼 것부터 시도한다.

> parser 안정화 → single-call 책임 축소 → human utility 확인 → 필요할 때만 two-stage

## Related Artifacts

- [14 plan](14-plan-review-ai-json-markdown-fence-sanitization.md) — 현재 live parser failure의 최소 수정 계획
- [15 report](15-report-review-ai-limitations-and-gaps.md) — PR #245의 blocker, runtime 및 evaluation limitation 종합 기록
- [12 proposal](12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md) — blocker remediation과 evaluation simplification의 순서
- [11 report](11-report-review-ai-overengineering-assessment.md) — MVP에 비해 무거운 evaluation infrastructure 진단
