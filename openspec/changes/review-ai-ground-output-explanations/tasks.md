---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Ground Review AI Output Explanations
description: 독립 품질 사례와 선택 가능한 prompt 후보의 구현 결과를 추적합니다.
tasks_completed: 3
tasks_total: 3
---

## Tasks

- [x] 대표 입력과 독립 oracle 및 semantic negative control을 기존 offline suite에 연결한다.
  - **Done when:** 세 입력이 기존 계약과 context 경계를 통과하며 baseline-zero, 다른 threshold, context 유무, backfill 유무가 구별된다. 알려진 prose 결함은 structured acceptance와 별개임을 test하고 fixture 점수를 사람 평가로 기록하지 않는다.
- [x] 선택 가능한 v3 후보와 historical replay 호환성을 구현한다.
  - **Test first:** v3 identity/렌더링 실패를 먼저 확인하고 v1/v2의 변경 전 digest를 고정한다.
  - **Done when:** v3가 단위·zero baseline·제공된 근거·실제 draft·조건부 다음 판단을 안내한다. v1/v2 digest, closed output, byte bound와 기존 기본값이 보존되며 focused tests가 통과한다.
- [x] 정본 계약과 실행·평가 가이드를 후보 지원에 맞춘다.
  - **Done when:** v3 선택과 세 사례의 동일 revision 비교, 전 시도 기록 및 human rubric 절차가 명시되고 실제 live/human evidence 없이는 개선·채택을 주장하지 않는다. 관련 source/test static checks와 Markdown/OpenSpec 검증이 통과한다.
