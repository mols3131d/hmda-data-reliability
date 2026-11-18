---
type: report
title: "PR #284 UNC Path Projection Remediation Report"
description: "14번 리뷰 F1의 UNC 경로 정제 누락을 공통 projection에서 보완하고 RED/GREEN, 전체 회귀와 독립 리뷰 결과 및 한계를 기록한다."
tags:
  - reliability-ai
  - privacy
  - testing
  - code-review
---

# PR #284 UNC Path Projection Remediation Report

## Summary

**[14번 리뷰](14-review-reliability-ai-unc-path-projection.md)의 F1을 수용하고, 공통 경로 정제 경계에서 Windows UNC를 처리하도록 보완했다.** 최종 context 테스트 20개와 전체 non-resource 테스트 1,209개가 통과했으며, 독립 DualVantage 재검토에서 현재 범위의 필수 미해결 항목은 없었다. 프로젝트 판정은 `clear`다.

이는 UNC 누출을 새로 도입한 회귀의 수정이 아니라 [Canonical provider input projection](../../openspec/specs/reliability-agentic-review/spec.md#requirement-canonical-provider-input-projection)의 기존 비노출 계약 이행 공백을 닫는 변경이다. 분류는 `acceptance_gap / current_required`이며, 보고서의 `Minor` 대신 프로젝트 기준 `Medium`으로 판단했다.

| Basis | Value |
| --- | --- |
| Verified date | `2026-11-16` |
| Owning PR | [#284](https://github.com/mols3131d/hmda-data-reliability/pull/284), Open / Draft |
| Owning branch | `agent/refactor/evolve-reliability-agentic-architecture` |
| Baseline HEAD | `6a8ddbf2939b143a623cf6f007ed7251ff7bfb52` |
| Implementation commit | `481c93470750314bcfc6399b85f5f5599618f81d`, ED25519 서명 검증 성공 |
| PR base at verification | `f1de6256cdd1e034f655b2f2ee3997481d0b195c` |
| OpenSpec | [Migration Tasks](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/tasks.md) Task 1 재개 후 완료, `7/7 all_done` |

## Changes

- [공통 context projection](../../src/hmda_reliability/reliability_ai/context.py)의 `_ABSOLUTE_PATH`에 UNC 분기를 추가했다. 기존 `file://`, POSIX, Windows drive 처리는 유지하고 초기 canonical 입력, 기본 Evidence 도구 응답과 중첩 원격 출력이 같은 정제 정책을 소비한다.
- UNC의 콜론 접두사, 공유명·파일명 공백과 공유 루트 경로를 처리한다. 경로 뒤 설명은 따옴표·개행 경계로 구분하며, 비인용 UNC의 끝이 모호하면 해당 경계까지 보수적으로 가린다.
- [기존 context 테스트](../../tests/reliability_ai/test_context.py)를 확장해 summary·허용된 nested facts·provenance의 실제 반환값과 JSON 파싱 후 도구 결과를 정확히 비교한다. 원격 projection은 이미 정제된 canonical 입력을 재사용하지 않고 독립적인 원본 payload로 검사한다.
- 일반 식별자·컬럼·URL·수치와 원본 summary를 보존한다. 연속 역슬래시 control·정규식 escape 및 JSON 메시지로 직렬화한 뒤 재투영한 문자열도 원문 그대로 유지되는지 확인한다. 새 의존성·공개 API·도구 권한·로컬 원문 재작성은 추가하지 않았다.

## Test-First Evidence

| Step | Observed Result |
| --- | --- |
| 최초 UNC 반례 | 기존 테스트 확장 후 `13 passed, 1 failed`. `Inspect \\fileserver\private\hmda.csv`가 제거되지 않는 summary assertion에서 실패했다. |
| 독립 리뷰의 추가 반례 | 초기 수정 후 공백 공유명·콜론 접두사·연속 escape 4건을 보강해 `14 passed, 4 failed`를 확인했다. 단순 배치 추가가 공백 뒤 경로를 남기고 일반 escape를 오인함을 재현했다. |
| 마지막 공백 경계 | 공백 파일명·공유 루트 사례에서 `18 passed, 2 failed`. `[private-path] data.csv` 또는 `[private-path] Share`처럼 잔존하는 조각을 확인했다. |
| 최종 GREEN | 동일 context 파일 `20 passed`. 모든 경로 사례의 정확한 정제와 공개 자료·직렬화 escape 보존을 확인했다. |

독립 oracle은 production 정규식의 복제가 아니라 명세가 금지한 실제 경로의 부재와 공개 반환 필드의 정확한 기대값이다. 문자열의 JSON escape 때문에 단순 substring 검사만으로 통과하지 않도록 파싱된 필드 assertion을 사용했다.

## Verification

| Check | Command / Scope | Result |
| --- | --- | --- |
| Focused pytest | `uv run --no-sync pytest tests/reliability_ai/test_context.py -q --tb=short` | `20 passed` |
| Full non-resource pytest | `env TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" uv run --no-sync pytest -n auto -q -p no:sugar --tb=short` | `1,209 passed, 1 skipped`, 실패·오류 0건 |
| Changed Python lint / format | `ruff check`, `ruff format --check`의 두 변경 파일 검사 | 모두 통과 |
| Project type / boundaries | `uv run --no-sync ty check`, `uv run --no-sync tach check` | 모두 통과 |
| OpenSpec tracking / structure | `openspec instructions apply --change reliability-agentic-review-enable-bounded-tools --json`, `openspec validate reliability-agentic-review-enable-bounded-tools --strict` | `7/7 all_done`, strict validation 통과 |
| Independent review | 최종 source·test delta에 대한 `mols-review-dualvantage` Verifier·Challenger 검토 | 현재 범위의 확정 결함·판단을 막는 미해결 항목 0건. Verifier가 격리된 focused pytest `20 passed`를 별도 확인했다. |
| Commit integrity | `git verify-commit`의 SSH allowed signer 대조 | 구현 commit의 ED25519 서명 검증 성공 |

전체 테스트와 독립 리뷰는 최종 source·test 상태를 기준으로 수행했다. 이후 Task 1 완료 표기와 본 보고서만 추가하며, 서명 커밋의 pre-commit 검사에서도 Python 수정은 발생하지 않았다. 이전 리뷰의 `clear`를 새 코드에 재사용하지 않고 수정 후 다시 검토했다.

## Limits And Delivery

- 검증한 것은 provider-visible projection의 정제다. 실제 provider·Langfuse 전송, 최종 제품 모델 재실험과 사람의 효용 평가는 수행하지 않았다. 오프라인 GREEN이나 이번 독립 리뷰를 모델 품질·외부 유출 부재의 증명으로 해석하지 않는다.
- 비인용 UNC 뒤의 자유 텍스트는 파일명과 구별할 수 없어 같은 인용부호·개행 경계 안에서는 함께 가려질 수 있다. 비공개 경로의 일부를 남기지 않는 쪽을 선택했으며, 따옴표 바깥의 설명 보존은 테스트했다.
- JSON 문자열 내부를 재귀 디코딩해 인코딩된 경로를 찾는 기능은 추가하지 않았다. 독립 리뷰에서도 기존 동작이며 별도 표현 해석이 필요한 `independent_requirement / follow_up`으로 분리했다. 일반 문자열의 UNC 정제와 직렬화된 escape 보존을 혼동하지 않는다.
- 이 보고서를 포함한 후속 문서 커밋까지 일반 push한 뒤 PR 본문의 동작·최종 검증·References·`revision.base/head`를 갱신한다. 보고서 작성 시점에는 새 원격 CI 결과를 통과로 기록하지 않는다. Ready 전환·approval·merge·archive는 수행하지 않는다.
