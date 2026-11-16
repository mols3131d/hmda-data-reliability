---
type: report
title: "PR #284 Response Retention And Failure Boundary Remediation Report"
description: "전체 PR 독립 리뷰에서 발견한 호출 자료 선저장·실패 보고 결함 두 건의 RED/GREEN, 전체 회귀와 수정 후 독립 검토 근거를 기록한다."
tags:
  - reliability-ai
  - provenance
  - testing
  - code-review
---

# PR #284 Response Retention And Failure Boundary Remediation Report

## Outcome

**전체 PR 독립 리뷰에서 확인한 필수 수정 두 건을 해결했다.** 도구 호출 자료를 원격 output·dispatch 전에 로컬에 보존하고, manifest 저장 실패 시 완성 보고 필드를 제거한다. 최종 회귀 6개, 관련 AI·Runtime 테스트 253개와 전체 non-resource 테스트 1,219개가 통과했다. 수정 delta의 독립 재검토 뒤 프로젝트 판정은 `clear`다.

이는 이번 저장·실패 보완의 완료 판정이다. 앞선 전체 PR 리뷰의 `changes_required`를 코드 변경 없이 철회한 것이 아니며, 전체 PR을 다시 전수 검토했다거나 실모델 품질·사람의 채택을 확인했다는 뜻도 아니다.

| Basis | Verified Value |
| --- | --- |
| Verified date | `2026-11-16` |
| Owning PR / branch | [#284](https://github.com/mols3131d/hmda-data-reliability/pull/284), `agent/refactor/evolve-reliability-agentic-architecture` |
| Baseline / reviewed PR head | `b0d9692de124265f8e631f1bc909d3ceb52f3635` |
| PR base at verification | `f1de6256cdd1e034f655b2f2ee3997481d0b195c` |
| Implementation commit | `5301ea505990fd8a1a9ba18260f3fbb1f0577f12`, ED25519 서명 검증 성공 |
| Reviewed source/test diff SHA256 | `3dc7f67c85c5c48df8dbc5d9ce099742dc55d760c3d6d6beb1b08ddba44463d9` |
| OpenSpec | [기존 Task 4](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/tasks.md) 재개 후 완료, `7/7 all_done` |

## Findings And Resolution

| Item | Admission | Observed Defect And Resolution |
| --- | --- | --- |
| 호출 자료 선저장 누락 | `High`, `explicit_target / current_required` | Tool-only 응답의 원격 output 시점에 로컬에는 0바이트 본문 파일만 있었고, 후속 manifest 실패 시 호출 ID·이름·인자의 영속 근거가 없었다. 정상 호출 목록·비정상 호출 원문을 본문과 별도 private create-only JSON으로 먼저 저장하고 turn의 `tool_calls_path`로 연결했다. |
| Manifest 실패 뒤 완성 보고 잔존 | `Medium`, `direct_regression / current_required` | 유효한 최종 보고 뒤 manifest 쓰기를 실패시키면 오류 상태에도 facts·findings·hypotheses·uncertainties가 반환·관측됐다. 해당 필드만 비우고 정확한 본문·turn·도구 기록·이미 보존한 경로는 유지한다. |

[조사 service](../../src/hmda_reliability/reliability_ai/investigation/service.py)는 호출 자료의 저장 성공 뒤에만 generation output과 도구 dispatch로 진행한다. 저장 실패는 `response_persistence_failed`로 끝내며 추가 provider·도구 실행을 하지 않는다. Root의 원격 partial output에서도 미보존 호출 자료가 있는 turn을 제외한다. 로컬 반환값과 가능한 manifest에는 진단용 partial turn을 유지한다.

기존 text-only `response_paths`와 본문 UTF-8 bytes는 유지한다. 새 선택적 경로는 [turn 계약](../../src/hmda_reliability/reliability_ai/investigation/contracts.py)에만 추가하고, [공통 원격 projection](../../src/hmda_reliability/reliability_ai/context.py)에서 제거한다. 별도 저장 계층·의존성·도구 권한·재시도·Recovery 정책을 도입하지 않았다. 도메인 안내는 [Reliability AI Guide](../../docs/domains/review-ai.md)에 반영했다.

## Verification

| Check | Observed Result |
| --- | --- |
| Clean RED | 기존 저장 실패 테스트 보강과 새 호출 자료 반례의 6개 사례 중 `1 passed, 5 failed`. 완성 facts 잔존, 선저장 JSON 부재, 호출 자료 저장 실패에도 completed되는 조건에서 assertion이 실패했다. 최초 실행의 테스트 변수 참조 오류 1건은 수정한 뒤 같은 6개를 재실행해 실제 계약 위반만 RED로 집계했다. |
| Focused GREEN | `.venv/bin/python -m pytest -q -p no:sugar --tb=short`로 아래 3개 함수의 6개 사례 실행: `6 passed` |
| Related consumers | `tests/reliability_ai tests/runtime_ai`: `253 passed` |
| Full non-resource suite | 절대 `TMPDIR/TMP/TEMP`를 지정하고 `.venv/bin/python -m pytest -n auto -q -p no:sugar --tb=short`: `1,219 passed, 1 skipped`, 실패·오류 0건 |
| Static checks | 변경 Python 4개 파일의 Ruff lint·format, project-wide `ty check`, `tach check`, 에디터 진단 모두 통과 |
| Plan / guide | 기존 Change strict validation, guide·task의 rumdl 검사 통과; Task 4 완료 후 `7/7 all_done` 확인 |
| Independent re-review | 서로의 초기 결과를 공유하지 않은 별도 Verifier·Challenger 검토. Confirmed material·unresolved 후보 0건. Caller의 이번 범위 판정 `clear` |
| Commit integrity | Pre-commit에서 Python 4개 파일 수정 없음. 구현 commit의 서명 검증 성공, committed source/test diff 해시가 reviewed state와 일치 |

[조사 테스트](../../tests/reliability_ai/test_investigation_agent.py)의 focused 함수는 `test_evidence_write_failure_cannot_be_completed`, `test_tool_call_data_precedes_remote_output_and_survives_manifest_failure`, `test_tool_call_data_write_failure_stops_before_dispatch_and_remote_output`다. 비어 있지 않은 보고, tool-only·본문 동반·다중 바이트 비정상 원문, 저장 실패의 dispatch 차단을 검사한다. 관측 콜백은 실제 파일 snapshot을 수집하고 assertion은 콜백 밖에서 수행하므로 관측 예외를 삼키는 wrapper가 false green을 만들지 않는다.

테스트 전담 agent는 테스트만 수정했고 구현 담당자가 실제 RED/GREEN·전체 회귀를 실행했다. 독립 재검토는 별도 context에서 수행했다. Verifier는 시작·종료 HEAD·diff 해시와 baseline을 확인했고 Challenger는 현재 소스를 정적으로 확인했다. 두 specialist 모두 Python 실행 사전확인 도구가 없어 pytest를 재실행하지 않았다. Challenger의 baseline·diff 해시 독립 검증도 수행하지 못했다. 전체 suite·재현·정적 검사 결과를 독립 runtime 검증으로 표현하지 않는다.

## Limits And Delivery

- 전체 PR 리뷰에서 제기된 JSON 문자열 내부 UNC 해석은 [이전 보고서](15-report-reliability-ai-unc-path-projection-remediation.md)의 별도 후속 요구로 유지한다. 주입 adapter와 별도 설정의 provenance 불일치는 이전 baseline에도 존재함을 확인했으며 이번 delta가 만든 회귀나 두 수정의 의존 결함으로 취급하지 않는다.
- 실제 provider·Langfuse 전송, 최종 제품 모델 재실험과 5개 기준 인간 효용 평가는 수행하지 않았다. 구조적 완료·코드 리뷰와 품질 채택을 구분한다.
- 본 보고서까지 별도 서명 커밋 후 일반 push하고 PR의 동작·최종 검증·References·revision을 갱신한다. 새 head의 원격 CI 결과는 확인 전 성공으로 기록하지 않는다.
- Ready 전환·approval·review thread 해결·merge·archive는 수행하지 않는다. 사람의 최종 채택 권한과 Draft 상태를 유지한다.
