---
type: plan
title: "Code Review Review Plan"
description: "구현·테스트 검토의 고유 컨텍스트와 범용 중복을 구분한다."
---

# Code Review Review Plan

> [!NOTE]
> **검토 가설 및 작업 인계.** 실제 수정은 아직 수행하지 않았다. 공통 목적·검증 방식은 [bundle](../README.md)을 따른다.

## Baseline

[Source](../../../../.rulesync/skills/prj-review-code/SKILL.md)는 target, baseline, contract, scope, validation을 정해 구현·테스트 변경을 검토한다. workflow, implementation, tests, findings 네 reference를 선택적으로 연결한다. 공통 asset의 `review-changes`와 `mols-test-design`에도 관련 책임이 있다.

## Preserve

- 변경된 관찰 가능 행동과 reachable regression, safeguards 및 실제 근거에 기반한 finding.
- 테스트 oracle·false-green·isolation을 다루는 **조건부 전문 컨텍스트**.
- Git diff뿐 아니라 요청된 개별 파일·테스트·작업트리 범위에도 적용 가능한 review surface.
- 검토 결과와 remediation·persistence 권한을 구분하는 역할 경계.

## Review Candidates

- 공통 review/test 스킬과 현재 네 reference 사이에서 중복된 설명.
- 모든 리뷰에 arguments와 다단계 workflow가 필요하다는 암묵적 전제.
- `inbox/_guidelines/review.md`가 이 스킬을 특정 implementation review owner로 참조하는 dependency.

## Tasks

1. PR diff 리뷰와 단일 파일 구현·테스트 리뷰의 서로 다른 요구를 재현한다. 문서-only review에서는 부적절하게 선택되지 않아야 한다.
2. 공통 스킬의 실제 repository route 등록·runtime discoverability를 확인한다. 이름이 존재한다는 사실만으로 대체 가능하다고 판단하지 않는다.
3. 리뷰 전문성을 남기면서 중복되는 guidance를 축소하거나 링크하는 후보를 만들고, 참조하는 guideline의 변경 영향도 확인한다.

## Acceptance

리뷰의 근거 기준·test-specific 판단을 상실하지 않는다. 통합이나 삭제는 모든 target surface를 대체하고 근거 있는 finding 품질을 유지할 때만 제안한다.
