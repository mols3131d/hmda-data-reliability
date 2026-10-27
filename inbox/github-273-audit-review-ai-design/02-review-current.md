---
type: review
title: Review AI Current Test Audit
description: Review AI의 현행 테스트 전수 검토, 과거 finding 재판정, 최소 회귀 보강과 검증 근거를 기록합니다.
---

# Review AI Current Test Audit

> [!NOTE]
> 도메인 테스트 검토와 허용된 보강을 수행했다. 독립 리뷰는 clear이며 최종 전달 상태는 아래 Current Review에서 확인한다. Draft/Ready/approval/merge는 별도 인간 결정이다.

- **Target:** [PR #273](https://github.com/mols3131d/hmda-data-reliability/pull/273)의 exclusive test lane과 read-only support/reserved integration.
- **Revision:** base `be1dca8d044494e92a0d25c791471a41b5d11bcf`; implementation/test head `4969ab646b3d162fe891511d3775713585269e1c`. 최초 준비 branch에 최신 main을 merge하여 검증했다.
- **Scope:** current tracked 15파일 전체 본문을 두 specialist가 각자 검토했다. Source/Spec은 관련 계약 대조용이며 수정하지 않았다.

## Findings And Adoption

| ID | Decision | Current evidence and action |
| --- | --- | --- |
| AI1 / G7 | deferred / scope_decision | 유효한 referenced metadata의 허용 facts 5개에 각각 `가 * 333`을 넣은 새 probe에서 raw `ValidationError`, provider/store 0회를 재현했다. Typed preflight rejection의 production 문제는 Review AI source owner가 담당한다. |
| AI2 | accepted / implemented | 기존 provenance test를 보강했다. 실제 provider messages를 capture하고 저장 canonical input의 replay tuple·digest와 비교한다. |
| AI3 | accepted / implemented | 작은 referenced evidence 9개 중 bound에서 제외된 `ev-meta-7`을 인용하면 `validation_failed`/`deterministic_guard_failed`이며, persisted `fabricated_evidence`와 선택된 8개 refs를 검사한다. |
| AI4 / Evaluation F1 | accepted / implemented | baseline `(0,1,2,0,1)`, candidate `(2,0,1,1,2)`의 criterion별 literal score/delta와 totals 4/6/2를 검사한다. |

AI2는 저비용 service/provider 경계를 보호한다. #277의 default harness→actual SDK→HTTP→store 시나리오는 실제 다른 경계의 연결을 검사한다. 기존 uniform fixture와 static golden은 보존했다. AI1을 예상 예외로 고정하거나 xfail로 숨기는 test는 추가하지 않았다.

## Contract Coverage

입력 linkage/snapshot과 bounded context는 실제 Pydantic validation·고정 IDs/facts로, prompt/service는 actual outbound messages와 결과·저장 레코드로, validator는 structured violation으로 판정한다. Store는 실제 create-only 파일·동시 충돌·rollback, evaluation은 static compatibility golden과 criterion 귀속을 사용한다. Provider는 이 lane에서 통제되며 실제 모델 품질과 인간 rubric 점수의 타당성은 제외한다.

## Source Follow-up

[context.py](../../src/hmda_reliability/review_ai/context.py)의 per-evidence facts 한도가 [service.py](../../src/hmda_reliability/review_ai/service.py)의 typed preflight handler 밖으로 탈출한다. 재현은 `AgenticReviewInput` 검증을 통과한 뒤 발생하며 총 context overflow와 다른 경로다. 예상 typed rejection과 provider/store 미호출을 유지하는 source 수정은 별도 범위 결정이 필요하다. #277은 이를 수집하며 현재 계획만으로 source 수정 권한을 갖지 않는다.

## File Coverage

이 표는 위 revision의 검토 ledger다. 테스트 수와 파일 수는 별개이며 reserved 파일의 검토는 수정 권한을 뜻하지 않는다.

| File | Coverage | Contract / oracle |
| --- | --- | --- |
| [tests/review_ai/__init__.py](../../tests/review_ai/__init__.py) | reviewed | package 설명 support |
| [tests/review_ai/conftest.py](../../tests/review_ai/conftest.py) | reviewed | 실제 detector/draft의 고정 material |
| [tests/review_ai/evaluation/fixtures/utility_comparison_6e64cc7.json](../../tests/review_ai/evaluation/fixtures/utility_comparison_6e64cc7.json) | reviewed | 전체 static JSON과 serialized enum/digest/delta |
| [tests/review_ai/evaluation/test_langfuse_projection.py](../../tests/review_ai/evaluation/test_langfuse_projection.py) | reviewed | exact projection, annotation binding, secret 제외, subprocess timeout |
| [tests/review_ai/evaluation/test_utility_evaluation.py](../../tests/review_ai/evaluation/test_utility_evaluation.py) | reviewed | 독립 static golden, case/revision binding, 서로 다른 criterion 점수 |
| [tests/review_ai/test_context.py](../../tests/review_ai/test_context.py) | reviewed | count/bytes, provenance, missing/unconfirmed, canonical target 우선 |
| [tests/review_ai/test_contracts.py](../../tests/review_ai/test_contracts.py) | reviewed | snapshot/linkage, closed output, typed result, compatibility |
| [tests/review_ai/test_dependency_boundaries.py](../../tests/review_ai/test_dependency_boundaries.py) | reviewed | AST import 방향; dynamic import 전체는 제외 |
| [tests/review_ai/test_evidence_store.py](../../tests/review_ai/test_evidence_store.py) | reviewed | 실제 I/O, create-only, 동시 충돌, legacy, fsync rollback |
| [tests/review_ai/test_live_harness.py](../../tests/review_ai/test_live_harness.py) | reviewed | #277 reserved; opt-in/config/revision/provenance 경계 |
| [tests/review_ai/test_prompt_provider.py](../../tests/review_ai/test_prompt_provider.py) | reviewed | allowlist/raw 제외, prompt replay, system/user 분리 |
| [tests/review_ai/test_public_surface.py](../../tests/review_ai/test_public_surface.py) | reviewed | 고정 public exports |
| [tests/review_ai/test_service.py](../../tests/review_ai/test_service.py) | reviewed | typed 상태, 실제 store, provider capture/replay, omitted citation 거부 |
| [tests/review_ai/test_settings.py](../../tests/review_ai/test_settings.py) | reviewed | prompt bytes 기본값과 상한 |
| [tests/review_ai/test_validator.py](../../tests/review_ai/test_validator.py) | reviewed | structured violation, stable order, free-text/non-mutation |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Current domain suite | `uv run --no-sync pytest -q -ra tests/review_ai`: **160 passed, 1 skipped (2.78s)**. Testmon selection 없이 domain 전체를 실행했다. |
| ✅ Pass | Changed Python | Ruff check/format check와 ty check 통과. 위 implementation head의 변경 파일 대상이다. |
| ✅ Pass | Transient negative controls | 저장소 source를 수정하지 않는 monkeypatch 주입으로 user message 누락, selected allowlist 제거, candidate score 순환 이동을 각각 만들었다. 신규 AI2/AI3/AI4 witness가 세 fault를 모두 거부했다. 전체 mutant suite 실행은 아니다. |
| ✅ Pass | Artifact mechanics | Native rumdl, Inbox validator, 실제 YAML parser의 필수값 검사, local links와 git diff check 통과. |
| ⚪ Not Verified | Runtime limits | optional Langfuse SDK media test는 dependency 부재로 skip했다. |

## Current Review

**Assessment: clear.** Review-lead가 quality/adversarial 두 specialist의 독립 결과를 조정했다. 정확한 reviewed implementation head는 `4969ab646b3d162fe891511d3775713585269e1c`이며 base는 `be1dca8d044494e92a0d25c791471a41b5d11bcf`다. 기존 46파일 baseline 중 이 lane의 변경된 테스트와 현재 문서 3개를 두 관점에서 다시 대조했다.

수용한 공백은 닫혔고 남은 `current_required` finding은 없다. Source/공유 tooling 후속은 `follow_up / scope_change`로 분리했다. Reviewer는 suite를 재실행하지 않았으며 위 실행 결과는 coordinator evidence다. 이 판정은 test/document review gate이며 제품 source 후속의 해결이나 correctness approval을 의미하지 않는다.

최종 Inbox-only delivery는 이 head의 test/source/Spec blob을 보존한다. 전달 후 exact remote head, prospective merge CI와 review readiness는 [현재 PR 본문](https://github.com/mols3131d/hmda-data-reliability/pull/273)에서 확인한다. Draft/Ready/approval/merge를 자동 전환하지 않는다.

## Handoff

[Plan](00-plan-review-ai-tests.md)과 위 검토 ledger에서 이어간다. 과거 [historical bundle](01-review-historical/README.md)은 그대로 보존하며 현재 검증 수로 재사용하지 않는다. Final Inbox-only delivery는 위 head의 test/source/Spec blob을 보존하고 exact remote head/CI는 PR 본문에서 확인한다.
