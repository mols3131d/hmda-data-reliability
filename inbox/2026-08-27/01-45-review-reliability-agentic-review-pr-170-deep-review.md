---
type: review
title: "PR #170 bounded agentic review deep review"
description: "PR #170의 agentic review 변경을 Spec, Design, 구현, 테스트와 운영 경계로 교차검증하고 현재 main에 남은 contract gap을 기록한다."
status: "completed"
tags:
  - reliability
  - agentic-review
  - llmops
  - pull-request
---

> [!NOTE]
> **Verdict: Revise.** PR #170의 큰 방향과 read-only delegation boundary는 유지할 가치가 있고 rollback은 필요하지 않다. 다만 현재 `main`에는 provenance failure의 typed boundary 누출, sanitized configuration의 credential 노출 가능성, 자연어 action policy와 Spec 사이의 계약 불일치가 남아 있다. 세 항목은 같은 capability의 후속 hardening change에서 해결하는 것이 적절하다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| PR #170 `Implement bounded agentic review` | base `a30a4079fd7a7f8018f78a3930afeebbb03a7c70` → head `651d241b170db0d74283b81547046175c283d303`; merge `203ecff066147f71a0eba4396f24804221140ddf` | `reliability/agentic_review`, OpenSpec contract, offline/live tests, provenance store와 provider boundary | **Revise** |

PR은 deterministic Reliability truth를 유지하면서 LLM을 advisory-only review에 한정하고, provider output을 structured parsing → deterministic validation → create-only provenance 순서로 통과시키는 구조를 도입했다. 이 구조 자체는 프로젝트의 evidence-first 및 recoverability-bounded delegation 방향과 잘 맞는다.

이번 review는 PR head를 immutable baseline으로 사용하고, merge 이후 현재 `main`에서 핵심 파일의 blob이 그대로 유지되는지도 확인했다. 따라서 아래 finding은 과거 PR diff에만 존재하는 문제가 아니라 review 시점의 `main`에도 남아 있다.

## Findings

### F1. Provenance filesystem failure가 typed result boundary를 우회할 수 있다

- **Severity** - Major
- **Location** - [`InvocationEvidenceStore.write()`](https://github.com/mols3131d/hmda-data-reliability/blob/651d241b170db0d74283b81547046175c283d303/src/hmda_reliability/reliability/agentic_review/store.py), [`_persist_result()`](https://github.com/mols3131d/hmda-data-reliability/blob/651d241b170db0d74283b81547046175c283d303/src/hmda_reliability/reliability/agentic_review/service.py)
- **Evidence** - `write()`는 `path.parent.mkdir(...)`를 `OSError` → `InvocationEvidenceWriteError` 변환용 `try` 바깥에서 수행한다. 또한 `finally`의 temporary-file cleanup도 동일한 정규화 경계 밖에서 실패할 수 있다. 반면 service는 `InvocationEvidenceStoreError`만 잡아 `provenance_failed`로 변환한다. 따라서 read-only filesystem, permission error 또는 일부 cleanup I/O failure에서는 raw `OSError`/`PermissionError`가 public review call 밖으로 탈출할 수 있다.
- **Contract** - OpenSpec의 `Typed review result boundary`와 `Durable invocation evidence`는 provider-started result의 evidence persistence가 실패하면 `provenance_failed`를 반환하고 accepted output을 차단하도록 요구한다. [`spec.md`](https://github.com/mols3131d/hmda-data-reliability/blob/651d241b170db0d74283b81547046175c283d303/openspec/changes/reliability-agentic-review/specs/reliability-agentic-review/spec.md)
- **Impact** - 설정된 artifact root가 생성 불가능한 환경에서 typed failure contract 대신 예외로 종료할 수 있다. `run_agentic_review_live.py` 같은 caller도 `AgenticReviewResult`를 받지 못하고 중단될 수 있어, 이 capability가 의도한 fail-closed/observable failure semantics가 깨진다.
- **Required Change** - directory creation, temporary-file creation/write/link/fsync, cleanup까지 persistence boundary의 filesystem failure를 일관되게 `InvocationEvidenceStoreError` 계열로 정규화한다. Duplicate identity는 기존 `InvocationEvidenceExistsError` 의미를 유지하고, cleanup failure가 이미 결정된 typed result를 raw exception으로 덮어쓰지 않게 한다. 실제 directory-creation failure를 통과시키는 deterministic test를 추가한다.

### F2. `base_url` 안의 credential이 sanitized provenance에 그대로 저장될 수 있다

- **Severity** - Major
- **Location** - [`AgenticReviewSettings`](https://github.com/mols3131d/hmda-data-reliability/blob/651d241b170db0d74283b81547046175c283d303/src/hmda_reliability/reliability/agentic_review/settings.py), [`SanitizedAgenticReviewConfiguration`](https://github.com/mols3131d/hmda-data-reliability/blob/651d241b170db0d74283b81547046175c283d303/src/hmda_reliability/reliability/agentic_review/evidence.py)
- **Evidence** - `base_url`은 `AnyHttpUrl`이고 `sanitized_configuration()`은 `str(self.base_url)` 전체를 그대로 기록한다. 프로젝트가 허용하는 최소 Pydantic version `2.13.4`의 URL type은 username, password, query와 fragment를 URL 구성요소로 표현할 수 있다. 따라서 `https://user:secret@example.test/v1` 또는 credential-bearing query를 사용하면 credential이 `configuration.base_url`로 persisted evidence에 남을 수 있다. Pydantic source: [`v2.13.4 pydantic/networks.py`](https://github.com/pydantic/pydantic/blob/v2.13.4/pydantic/networks.py)
- **Counterevidence check** - [`test_settings.py`](https://github.com/mols3131d/hmda-data-reliability/blob/651d241b170db0d74283b81547046175c283d303/tests/reliability/agentic_review/test_settings.py)의 sanitized configuration test는 별도 `api_key`가 제거되는지만 검증하며 credential-bearing URL은 다루지 않는다. Evidence-store test도 같은 safe URL fixture를 사용한다.
- **Contract** - Spec과 domain documentation은 invocation evidence에 API key와 credential을 저장하지 않는다고 명시한다. 현재 구현은 `api_key` 필드는 제거하지만 URL 자체를 credential-free로 보장하지 않는다.
- **Impact** - OpenAI-compatible endpoint를 userinfo 또는 secret query와 함께 구성한 경우, create-only invocation evidence가 장기적으로 credential을 보존하는 보안 사고가 될 수 있다. 이는 단순 logging hygiene가 아니라 명시적인 provenance sanitization contract 위반이다.
- **Required Change** - `base_url`의 credential-bearing component를 입력에서 금지하거나 persisted representation에서 안전하게 redact한다. 어떤 방식을 택하든 provider가 실제 사용하는 endpoint semantics와 provenance에 필요한 진단 정보를 유지해야 한다. 최소한 userinfo와 credential-like query를 대상으로 regression test를 추가한다.

### F3. `forbidden-action-policy-v1`의 자연어 coverage가 Spec의 보장보다 좁다

- **Severity** - Major, 단 자동 mutation blast radius는 read-only boundary로 제한됨
- **Location** - [`validator.py`](https://github.com/mols3131d/hmda-data-reliability/blob/651d241b170db0d74283b81547046175c283d303/src/hmda_reliability/reliability/agentic_review/validator.py), [`design.md` D4](https://github.com/mols3131d/hmda-data-reliability/blob/651d241b170db0d74283b81547046175c283d303/openspec/changes/reliability-agentic-review/design.md), [`spec.md` Deterministic review validation](https://github.com/mols3131d/hmda-data-reliability/blob/651d241b170db0d74283b81547046175c283d303/openspec/changes/reliability-agentic-review/specs/reliability-agentic-review/spec.md)
- **Evidence** - validator는 `execute`, `run`, `apply`, `trigger`, `perform`, `start` 및 몇 가지 특수 패턴을 정규식으로 찾는다. `Proceed with the backfill immediately.`, `You should backfill the 2025 partition now.`, `Initiate recovery now.` 같은 직접적인 실행 권고는 해당 verb/pattern set에 포함되지 않는다. Identity, deterministic facts와 evidence reference가 정상이라면 이런 free-text output은 `forbidden_action` 없이 accepted될 수 있다.
- **Contract mismatch** - Spec은 output이 recovery/backfill/data mutation 실행을 **명령**할 때 `forbidden_action`을 반환해야 한다고 요구한다. 반면 Design D4는 versioned action policy가 자연어 의미 전체를 판정하는 semantic judge가 아니며 안전성은 read-only execution boundary에도 의존한다고 명시한다. 즉 Design의 한계는 현실적이지만 Spec의 표현은 그 한계보다 강하다.
- **Counterevidence check** - [`test_validator.py`](https://github.com/mols3131d/hmda-data-reliability/blob/651d241b170db0d74283b81547046175c283d303/tests/reliability/agentic_review/test_validator.py)는 대표적인 `Execute`, `Backfill ... now`, `Delete`, `rm -rf`를 잘 검증하지만 동의어나 권고형 imperative가 동일한 contract를 우회하는 경우는 다루지 않는다.
- **Impact** - service에는 execution interface가 없어 model text가 곧바로 recovery를 수행하지는 않는다. 따라서 데이터 mutation safety boundary는 유지된다. 그러나 `accepted`가 action-policy 검증까지 통과한 결과라는 의미는 실제보다 강해지고, downstream human review나 향후 delegation 확장에서 잘못된 신뢰 신호가 될 수 있다.
- **Required Change** - 먼저 canonical contract를 하나로 맞춘다. deterministic action policy가 보장하는 **bounded grammar/pattern coverage**를 Spec에 명시하고 그 grammar를 테스트로 고정하거나, 현재 Spec 수준의 자연어 명령 탐지를 유지하려면 validator 구현을 그 계약에 맞게 강화한다. regex heuristic을 semantic guarantee처럼 취급해서는 안 된다. Read-only execution boundary는 그대로 최종 safety control로 유지한다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| Target resolution | PR #170 metadata: base `a30a4079…`, head `651d241b…`, merged as `203ecff0…` | Pass |
| Spec ↔ Design ↔ implementation trace | input/output contract, action policy, provenance requirement와 `settings.py`, `validator.py`, `service.py`, `store.py`를 cross-check | Pass |
| Test counterevidence | `test_settings.py`, `test_validator.py`, `test_service.py`, `test_evidence_store.py`, live harness tests 검토 | Pass |
| Current `main` relevance | review 대상 핵심 `store.py`, `settings.py`, `validator.py` blob이 PR head와 동일한 상태임을 확인 | Pass |
| PR validation claim | PR description에 agentic-review 80 tests, reliability 255 tests, 전체 404 tests 통과가 기록됨 | Pass as reported evidence only |
| GitHub Actions for reviewed head | reviewed head SHA에 연결된 workflow run을 확인하지 못함 | Not Verified |
| Independent pytest execution | 이 review runtime에서는 repository test suite를 직접 실행하지 않음 | Not Verified |
| Live Ollama invocation | PR description이 실제 Ollama call은 CI/default test에서 의도적으로 실행하지 않았다고 명시 | Not Verified |
| Pydantic URL semantics | project minimum `pydantic>=2.13.4`와 Pydantic `v2.13.4` URL implementation을 확인 | Pass |

## Remaining Risks

- Live provider compatibility는 이번 review에서 직접 실행하지 않았다. 다만 adapter의 timeout, bounded retry, max-output, schema failure는 offline test로 분리되어 있어 이 미검증 영역 자체를 추가 defect로 분류하지 않는다.
- Free-text action classification은 본질적으로 의미론적 한계가 있다. 향후 model output에 더 큰 authority를 부여하려면 regex coverage 확대만으로 delegation boundary를 넓히지 말고, 구조적 권한 경계와 recovery guard를 계속 최종 통제로 유지해야 한다.
- PR description의 test pass 수는 유용한 evidence지만 이번 review가 독립적으로 재실행한 결과는 아니다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| **Revise** | Architecture 방향은 유지 가능하지만 provenance failure typing, credential sanitization, action-policy contract의 세 gap이 current `main`에 남아 있다. rollback보다 bounded follow-up hardening이 적절하다. | `reliability-agentic-review` owning OpenSpec + implementation/tests를 같은 목적의 후속 change/PR에서 수정 |

후속 변경은 세 finding을 한꺼번에 일반 LLM framework redesign으로 확장할 필요가 없다. 현재 `agentic_review` capability 안에서 contract를 정렬하고, 가장 작은 regression test와 boundary fix만 추가하는 것이 KISS/YAGNI에 맞다.