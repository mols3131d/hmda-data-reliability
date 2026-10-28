---
type: plan
title: Review AI schema failure resolution
description: PR 278의 최소 진단·프롬프트 수정·재발 방지와 revision별 검증 계획 및 진행 근거
tags:
  - review-ai
  - runtime-ai
  - testing
---

# Review AI Schema Failure Resolution

## Scope and Acceptance

사용자의 2026-10-28 요청에 따라 [제안서](01-proposal-review-ai-diagnostic-observability.md)의 옵션을 검토하고, 실제 실패를 재현한 뒤 필요한 최소 기능과 회귀 검증을 구현한다. 시작 기준은 base `83538af4929c9d4cd533fa550e6b7e6aed22a5b8`, PR head `2d26ef7f4f172fc179160f9193b06ec0ec0b49f8`다. 기존 로컬 branch가 원격과 갈라져 있어 원격 head에서 별도 작업 트리를 만들었다. 기존 작업 트리와 main은 수정하지 않는다.

완료 조건은 현재 코드의 실패 분류, prompt 계약 일치, v1 재생 보존, invalid output·guard의 fail-closed/no-retry, 정제된 증적의 호환성, offline regression 및 모델별 opt-in live 결과다. Live success는 schema/guard/provenance 통과만 뜻하며 사람의 utility 평가를 대신하지 않는다. Raw 출력 저장·외부 전송, 출력의 자동 보정, schema 강제 transport, 모델별 router, CI network 호출 및 Ready/merge는 범위 밖이다.

## Option Decisions

| Option | Decision | Reason |
| --- | --- | --- |
| A. Validation diagnosis | Adopt | 현재 파서가 빈 응답·JSON·출력 계약 오류를 같은 코드로 숨긴다. 공개 failure code는 유지하고 bounded 분류와 allowlisted field/code만 저장한다. Pydantic input/message/context/URL은 저장하지 않는다. |
| B. Completion metadata | Adopt narrowly | SDK가 제공하는 완료 이유, 본문 상태와 byte 수만 보존한다. 알 수 없는 완료 이유는 고정 값으로 정규화한다. `length`만으로 새 거부 정책을 만들지 않는다. |
| C. Raw inspection | Defer | A/B와 synthetic fixture·live 호출로 우선 판별한다. Raw 출력용 CLI나 저장소는 만들지 않는다. |
| D. Wire inspection | Already covered | 실제 SDK와 fake HTTP의 기존 wire test를 확장한다. 새 network logger는 필요 없다. |
| E. Validation replay | Adopt as tests | 사람이 작성한 작은 응답 fixture로 GPU 없이 재현한다. 운영용 response capture/replay store는 만들지 않는다. |
| F. Cohort aggregation | Defer | 현재 문제 해결에 집계 API나 새 저장 모델이 필요하지 않다. |
| G. Langfuse raw trace | Reject for this scope | 로컬 판별에 충분하고 raw 전송은 canonical safety boundary와 충돌한다. 기존 projection allowlist를 유지한다. |

## Research and Plan

현재 source는 `uncertainties` 배열과 `priority` 조건을 명시하지 않은 v1 system instruction, `finish_reason`을 버리는 SDK transport, JSON/schema 오류를 함께 삼키는 파서를 확인했다. 동일 의미의 active OpenSpec Change는 없다. 계약 변경은 기존 [Spec](../../openspec/specs/reliability-agentic-review/spec.md)에 반영하며 별도 capability를 만들지 않는다.

1. 수정 전 offline suite와 opt-in synthetic v1 live 호출로 기준을 확보한다. 과거 9건의 raw 출력은 복원하지 않는다.
1. 정상/문자열 배열/priority 조건/잘린 JSON/빈 본문 fixture와 실제 SDK의 stop·length·null·빈 choices를 테스트한다. 실패는 계속 거부되고 재호출되지 않아야 한다.
1. Runtime은 domain-neutral 완료 metadata를 전달하고 Review AI는 정제된 parse 진단을 evidence에 추가한다. 기존 evidence는 optional field 없이도 읽힌다.
1. v1 instruction과 기본 identity는 보존한다. 타입·조건을 명시하는 고정 v2 instruction을 추가하고 live harness에서 명시적으로 선택한다. v1 digest golden 및 두 버전 replay를 검증한다.
1. 관련 suite·정적 검사·Spec·문서 검증 후 구현을 commit한다. 깨끗한 revision에서 같은 모델/설정의 live를 실행하고 독립 review를 받는다. 새 근거가 원인을 더 좁히면 계획을 갱신한 뒤 최소 수정한다.
1. 검증 revision, live invocation, 한계와 다음 판단을 같은 PR Inbox에 남기고 PR branch와 본문을 갱신한다. Draft는 유지한다.

## Run State

- Phase: RPI Main Loop / Work
- Readiness: READY
- Loops: 1/30
- Acceptance: open
- Next: enum instruction refinement, malformed metadata regression, final live and independent review

문서 작성·검증에는 `mols-documentation`, `mols-markdown-maintenance`를 적용한다. 실험과 수정 후 이 문서 또는 후속 결과 문서에서 실제 실행 근거와 계획 변경을 기록한다.

첫 구현의 실제 비교와 후속 범위 결정은 [결과 보고](03-report-review-ai-schema-resolution.md)에 기록한다. Qwen3.5 기본 context의 본문 미생성과 8k v1의 schema 위반을 구분했고, 8k v2는 schema·guard·provenance를 통과했다. Qwen2.5의 남은 kind 위반과 독립 review의 malformed completion metadata finding을 현재 범위에서 보완한다.
