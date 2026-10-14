---
type: campaign
title: "CI Documentation Improvement Campaign"
description: "PR 253의 CI 문서 개선 캠페인으로, README 중심 번들의 반영 결과와 전환 계획·이전 제안을 함께 관리합니다."
tags:
  - ci
  - documentation
  - contract
---

# CI Documentation Improvement Campaign

PR [#253](https://github.com/mols3131d/hmda-data-reliability/pull/253)의 branch `agent/research-ci-script-separation`이 소유하는 CI 문서 개선 캠페인이다. [현재 CI 번들](../../../docs/development/ci/README.md)의 반영 결과와 전환 계획·판단 근거를 함께 관리한다.

> [!NOTE]
> 사용자의 후속 실행 요청에 따라 README 중심 번들을 로컬 작업 트리에 반영했다. README는 진입점 기능과 Goal·Principles·Patterns를 함께 소유하며, 추가 요청에 따라 공통 권한·신뢰 경계도 흡수했다. 검증별 계약은 별도 파일로 둔다. 제안서와 계획서는 작성 당시의 판단 기록이며 현재 완료 상태를 대신하지 않는다.

## Start Here

| Need | Document | Role |
| --- | --- | --- |
| 현재 CI 정책과 책임별 계약 확인 | [CI 번들](../../../docs/development/ci/README.md) | Canonical 개발 가이드 |
| 전환 구조, 이동 순서와 완료 기준 확인 | [계획서](plan.md) | 이번에 지정한 README 중심 구조의 계획 기록 |
| 이전 선택지와 비용·위험 확인 | [제안서](proposal.md) | 구조 방향을 정하기 전의 검토 기록. 현재 계획을 대체하지 않는다 |

## Result

- 기존 단일 CI 문서를 README와 Admission·Change Impact·Markdown Validation·Inbox Validation 계약으로 전환했다. Safety and Authority는 [README의 해당 절](../../../docs/development/ci/README.md#safety-and-authority)에 통합하고 별도 파일을 제거했다.
- Development·Testing·Tooling의 현재 참조를 새 owner로 연결하고, 과거 근거 링크는 기록의 기준 revision에 고정했다.
- Native generator로 두 docs index의 CI 항목을 갱신했다. 무관한 기존 MVP description drift는 이번 변경에서 유지했다.
- 새 번들과 변경한 현재 가이드의 native Markdown·상대 링크·fragment 검사, required frontmatter 검사가 통과했다. Goal·Principles·유지한 Patterns와 Markdown·Inbox·권한 규칙은 링크 이동을 제외하고 기준 원문과 일치했다.

이 결과는 로컬 문서 검증이며 원격 CI 통과나 PR 승인 근거가 아니다. Workflow·script·test와 OpenSpec의 실행 동작은 변경하지 않았다.

## Scope

- README에 번들 안내와 Goal·Principles·Patterns·공통 권한·신뢰 경계·Ownership을 둔다.
- 검증별 계약은 책임별 파일로 분리하고 기존 의미와 병합 기준을 보존한다.
- 문서 전환 시 필요한 링크·metadata·generated index와 검증을 계획서에 따라 다룬다.

CI 동작, workflow·script 구조, 검사 범위, 권한과 OpenSpec capability 변경은 이 캠페인의 문서 전환 범위에 포함하지 않는다.

## Boundary

이 디렉터리는 non-canonical Inbox 작업물 묶음이다. 캠페인 README는 목적·범위와 읽기 안내를, 계획서는 세부 전환 계획을, 제안서는 이전 검토 근거를 맡는다. 실제 CI 정책과 구현을 override하지 않는다.

문서 전환 결과는 미커밋 로컬 작업 트리에 남겼다. Commit·push나 PR metadata 변경은 수행하지 않았다.
