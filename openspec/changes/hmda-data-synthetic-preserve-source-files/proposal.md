---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Preserve Synthetic Source Files
description: 합성 결함 생성 시 입력 파일과 출력 삭제 범위가 겹쳐 발생하는 원본 데이터 손실을 방지합니다.
---

## Why

`row_count_drop`의 source가 기존 case output directory 내부에 있으면 생성 준비 과정에서 원본까지 삭제될 수 있다. PR #258의 [재현 근거](https://github.com/mols3131d/hmda-data-reliability/blob/b6b47606bdabf69221eff94c8f9c69dc03b6cc57/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/validation.md#a2-synthetic-source-preservation)는 원본 삭제 후 오류가 발생한 사례를 기록한다. 이는 현행 [Isolated synthetic output](../../specs/hmda-data-synthetic-defects/spec.md#requirement-isolated-synthetic-output)의 원본 불변 계약에 어긋난다.

## What Changes

- 출력 case directory를 정리하기 전에 실제 입력 경로와 삭제 범위의 중첩을 확인해 위험한 요청을 거부한다.
- 원본의 존재와 내용을 검증하는 회귀 테스트를 추가하고, 겹치지 않는 정상 생성·기존 case output 교체 동작은 유지한다.

## Boundaries

- **In Scope:** `row_count_drop`, `null_spike`, `schema_drift`가 공유하는 synthetic 출력 경계와 해당 원본 보존 회귀 테스트.
- **Out of Scope:** 다른 ingestion/recovery 결함, synthetic sampling 알고리즘, 기존 case output의 원자적 교체 정책 및 새로운 데이터 품질 계약.

## Impact

- 대상: `src/hmda_reliability/hmda_data/synthetic/`와 `tests/hmda_data/test_synthetic.py`.
- 기존 capability의 계약을 복구하는 수정이므로 별도 delta Spec은 작성하지 않는다.
