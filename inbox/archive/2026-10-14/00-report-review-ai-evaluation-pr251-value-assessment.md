---
type: report
title: Review AI Evaluation PR #251 Value Assessment
description: PR #251의 실효성에 의문을 제기한 사용자 의견과 기술적 효용·비용의 구분, 명시적인 머지 결정의 근거와 한계를 보존한다.
tags:
  - review-ai
  - evaluation
  - pull-request
  - decision
---

# Review AI Evaluation PR #251 Value Assessment

> [!IMPORTANT]
> **사용자 의견 (2026-10-14):** "이거 pr 닫아야하는거 아닐까? 실효성이 없어 보이는데 맞니?"
>
> 이 의견은 PR #251의 **투자 대비 실효성에 대한 명시적인 문제 제기**다. 기능 오류를 입증한 finding이나 최종 채택 판단과 혼동하지 않는다. 후속 사용자 요청은 이 의문과 평가를 아카이브에 기록한 다음 **PR #251을 머지하라는 명시적 지시**였다. 머지는 실효성 의문이 해소됐다는 증거가 아니다.

## Context

- 대상: [PR #251 — refactor(review-ai): isolate evaluation subdomain](https://github.com/mols3131d/hmda-data-reliability/pull/251).
- 비교 기준: `main@79e2e1eec6ad34c1457a815888c00556213ef195`, 검토 당시 PR head `1193397d01e7202893e084c642e4cb8dcc58f00d`. 머지 결과의 최종 revision은 GitHub를 확인한다.
- 범위: Review AI의 human utility evaluation과 optional Langfuse adapter를 `review_ai.evaluation`로 이동, Python API를 `ReviewValue*`로 rename, 기존 JSON 계약·fail-closed 비교와 관찰 경계를 유지하는 리팩터링.
- 변경량: 검토 당시 49개 파일, +2,168/−181줄이며, 이 중 23개 Inbox 파일(+1,281줄)은 보고서·작업 근거다. 라인 수 자체는 품질의 척도가 아니다.

## Assessment

### Why the practical value was questioned

1. **기존 기능의 대부분이 이미 존재했다.** 이전에도 `review_ai/evaluation.py`와 `review_ai/langfuse_projection.py`가 역할별로 분리돼 있었다. 새 하위 패키지는 소유권 표현을 개선하지만 사용자가 체감하는 Review AI 품질을 직접 높이지 않는다.
2. **의도적인 호환성 비용이 있다.** `HumanUtilityEvaluation` 등 구 Python import 이름을 alias 없이 없앤다. Repository 내부 소비자는 갱신됐지만 외부 소비자는 확인되지 않았다.
3. **MVP 핵심 증명과는 거리가 있다.** 지금 더 중요한 목표는 AI review가 deterministic facts의 재진술을 넘어 사람의 조사·판단을 실제로 개선하는지 representative case와 human rubric으로 검증하는 것이다. 패키지 재구성만으로는 그 증명이 되지 않는다.
4. **변경과 검토 표면이 넓다.** 폴더·public import·CLI module path·문서·테스트가 함께 바뀌어 작은 구조 개선에 비해 검토 비용이 크다. Inbox 보고서가 diff에서 큰 비중을 차지한다.

### What still has concrete value

- **정확성 수정:** Langfuse `project_invocation()`의 input equality를 deterministic JSON 직렬화 비교로 강화했다. Python의 `True == 1` 때문에 이전에는 놓칠 수 있던 JSON boolean/number 타입 차이를 감지하고 회귀 테스트로 보호한다.
- **회귀 근거:** 과거 `compared`/`blocked` JSON 전체를 golden fixture로 비교하고, output digest와 fail-closed 동작을 보존하는 검증을 추가했다.
- **소유권 가독성:** evaluation value와 optional Langfuse adapter의 위치와 entrypoint를 일관되게 명명한 점은 제한적인 유지보수 이점이 있다.

이 이점들이 **반드시 지금 이 규모의 리팩터링을 해야만 얻을 수 있었는지**는 별개 질문이다. 특히 입력 타입 수정은 작은 독립 PR로도 전달 가능했을 것으로 판단한다.

## Decision and Limits

- **기술 검토:** 기존 검토에서는 새로운 merge-blocking correctness defect를 확인하지 못했다. 이는 제품적 효용이나 투자 대비 가치를 승인한다는 뜻이 아니다.
- **가치 판단:** 실효성이 낮다는 사용자 의문은 타당하다. 초기에는 PR을 닫고 입력 타입 수정만 분리하는 선택을 권고했다.
- **후속 결정:** 사용자는 이 의문을 기록한 상태에서 PR 머지를 **명시적으로 요청**했다. 이 문서는 그 결정 과정을 보존하지만 의문이 해소됐다고 주장하지 않는다.
- **검증 경계:** 문서 작성 전 [CI Lite #38531266945](https://github.com/mols3131d/hmda-data-reliability/actions/runs/38531266945)는 기존 head 기반 통합 검증에서 **916 passed, 3 skipped** 및 별도 **11 passed**를 기록했다. 이후 문서 커밋이나 머지 결과의 검증을 자동으로 대표하지 않는다. 실제 Langfuse 원격 ingestion/UI, 외부 Python consumer, 사람의 utility 평가도 검증하지 않았다.
- **OpenSpec과의 구분:** 이 문서는 비정본 판단 기록이다. 현재 기능 계약은 `openspec/specs/**`, 구현은 `src/**`가 소유한다.

## Follow-up Principle

다음 구조 변경은 실제 소비자·반복된 유지보수 문제·측정 가능한 이익이 확인될 때 우선한다. MVP의 다음 판단은 **실제 human utility proof**를 먼저 수집해 결정하며, 테스트 통과와 패키지 정리만으로 AI review의 추가 가치를 주장하지 않는다.
