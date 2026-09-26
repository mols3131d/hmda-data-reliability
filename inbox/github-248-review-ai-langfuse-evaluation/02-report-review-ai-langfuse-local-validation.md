---
type: report
title: Langfuse Local Implementation Evidence
description: PR 248의 로컬 구현, 검증 범위와 실제 프로젝트 없이 남은 proof를 기록한다.
---

# Langfuse Local Implementation Evidence

2026-09-27 KST. Base `1d7e5c70baa03540644e0dac71b740330f3e58cb`, starting head `e8441fb896eb94d07aed492b1dce0c641df2b0eb` 위 working tree에서 검증했다. 구현 계약과 완료 task는 [Change](../../openspec/changes/review-ai-langfuse-projection/tasks.md)가 소유한다.

## Implementation

- 기존 synthetic live harness의 검증 뒤에만 실행하는 optional projection을 추가했다. SDK는 extra `langfuse`로 선택 설치하며 4.15.6을 lock했다.
- 현재 합성 입력과 일치하는 record만 field allowlist로 투영한다. Output digest는 기존 utility 계약을 사용하며 failed record의 partial output이나 raw failure text를 보내지 않는다.
- SDK를 child process로 격리하고 parent timeout으로 init/export/flush/shutdown을 제한한다. Export 실패는 sanitized 상태이며 기존 result, record와 exit 의미를 유지한다.
- 수동 annotation의 exact target 및 다섯 criterion/score/rationale shape만 검사한다. 사람의 점수나 utility 판단을 만들지 않았으며 importer는 없다.

## Validation

| Check | Result | Evidence |
| --- | --- | --- |
| Test-first projection | Pass | 신규 모듈이 없는 상태에서 collection failure를 확인한 뒤 최초 15개 통과. |
| Test-first harness integration | Pass | 연결 전 missing integration status로 실패한 테스트가 구현 뒤 통과. |
| Domain regression | Pass | SDK가 없는 기본 locked 환경에서 `uv run --no-sync pytest tests/review_ai tests/runtime_ai -q`: 173 passed. |
| Unit regression | Pass | `uv run --no-sync pytest -m unit -q`: 352 passed, 342 deselected. |
| SDK runtime smoke | Pass | 실제 4.15.6 + InMemorySpanExporter에서 observation 한 개 생성, global provider 불변. Importlib lazy loading 변경 후 재실행했다. 실제 HTTP 전송은 하지 않았다. |
| Optional installation | Pass | `uv sync --locked` 뒤 `find_spec("langfuse") is None`, default harness disabled 확인. |
| Static contracts | Pass | Project-wide `ty check`, changed Python Ruff/format, `tach check`, Tombi pyproject lint, `git diff --check`. |
| Planning/docs | Pass | OpenSpec Change strict validation, changed Markdown rumdl format, testing guide rumdl check. |
| Independent review | Pass | quality/adversarial 두 specialist와 `review-lead`의 조정 결과 `clear`. [Review evidence](03-review-review-ai-langfuse-local.md)를 참조한다. |

SDK smoke는 실제 SDK의 manual observation, flush/shutdown 호출과 기존 OTEL provider 보존만 증명한다. Timeout 테스트는 실제로 30초 대기하는 child를 0.1초 제한으로 종료하고 부모가 3초 이내 반환하는 것을 확인했다. Init/export/flush/shutdown 오류 injection은 test double이며 원격 failure를 재현한 것은 아니다.

## Remaining Proof

사용자는 아직 endpoint/project가 없으며 로컬 구현·검증을 먼저 진행하도록 지정했다. 따라서 실제 ingestion, 배포별 score config/comment UI, 사람이 수행하는 다섯 항목 채점과 workflow 가치 비교는 **Not Verified**다. SDK 반환은 `submitted_unverified`로 표시하며 전체 PR의 live proof나 MVP utility acceptance를 완료했다고 주장하지 않는다.

후속 실행은 사용자가 대상과 credential을 로컬 환경에 설정한 뒤 [사용 안내](../../docs/development/testing.md#optional-langfuse-projection)에 따라 동일 implementation revision에서 수행한다. Credential, payload 전체 또는 synthetic test 점수를 human evidence로 남기지 않는다.
