---
type: report
title: Review AI schema diagnosis and resolution evidence
description: PR 278의 revision별 원인 분류, 최소 수정의 실험 결과와 재발 방지 검증
tags:
  - review-ai
  - runtime-ai
  - diagnostics
  - testing
---

# Review AI Schema Resolution Evidence

## Current State

**In progress:** 원문 없는 진단과 v1 replay를 보존하는 v2 instruction을 구현했다. 첫 v2 live는 완전한 해결이 아니었다. 남은 enum 위반과 Qwen3.5 context 차이를 조사하고 있으며, 아래 기록을 성공 증명으로 확대하지 않는다. 범위와 옵션별 채택·기각 이유는 [계획](02-plan-review-ai-schema-resolution.md)을 따른다.

## Revision and Validation

| State | Evidence |
| --- | --- |
| Start base / PR head | `83538af4929c9d4cd533fa550e6b7e6aed22a5b8` / `2d26ef7f4f172fc179160f9193b06ec0ec0b49f8` |
| First implementation | `1c2622ce93ea18b1c98cb7558759f3c6cc8e030a` |
| Baseline offline | `204 passed, 1 skipped`; Review AI + Runtime AI |
| Regression red | 구현 전 14 tests failed: diagnosis 7, v2 prompt 1, SDK metadata 6 |
| First implementation focused | `228 passed, 1 skipped`; `uv run --no-sync pytest -p no:tach tests/review_ai tests/runtime_ai -q --tb=short` |
| First implementation full suite | `1191 passed, 3 skipped in 124.11s`; `uv run --no-sync pytest -p no:tach -n 4 -q` |
| Static and contract checks | Ruff, project-wide `ty check`, `tach check`, modified Spec strict validation, rumdl, Inbox artifact validation, `git diff --check`: pass |

`-p no:tach`는 pytest의 affected-selection plugin만 끄고 선택된 범위를 실제로 전부 실행한다. 별도 `tach check`와 full suite의 boundary guard는 유지했다. Optional Langfuse SDK가 설치되지 않아 관련 smoke가 skip됐으며 원격 projection 또는 human utility 평가는 실행하지 않았다.

## Live Experiments

모든 호출은 기존 synthetic harness·실제 SDK·create-only evidence를 사용한다. Langfuse는 끄고 모델은 명시적으로 선택했다. `max_output_tokens=4096`, `max_retries=0`, `timeout_seconds=180`, `max_prompt_bytes=65536`, `max_output_bytes=32767`로 비교했다. 실패 후 자동 재생성은 없다. 아래 목록은 이 작업에서 실행한 논리적 invocation 전체를 기록하며 모델별 성공률로 해석하지 않는다.

| Revision | Model / prompt | Invocation | Status / cause | Completion / usage |
| --- | --- | --- | --- | --- |
| `2d26ef7f` | `qwen2.5-coder:7b` / v1 | `ar-20261028-4dc8618bbe00` | `validation_failed / response_schema_invalid`; 이전 parser는 세부 원인을 보존하지 않음 | token total `1565` |
| `1c2622ce` | `qwen2.5-coder:7b` / v1 | `ar-20261028-238a2f2e319e` | `schema_validation_failed`: `uncertainties.item / type_invalid`, utility의 `conditional_invalid` 3건 | `stop`, text `1868` bytes; prompt/completion/total `1046/519/1565` |
| `1c2622ce` | `qwen2.5-coder:7b` / v2 | `ar-20261028-6ce979367cf9` | `schema_validation_failed`: `utility_contributions.item.kind / value_invalid` 1건 | `stop`, text `1797` bytes; `1222/514/1736` |
| `1c2622ce` | `qwen3.5:4b` / v1 | `ar-20261028-db2acbb38847` | `response_content_empty` | `length`, text `0` bytes; `1048/3048/4096` |
| `1c2622ce` | `qwen3.5:4b` / v2 | `ar-20261028-86bf7cf6bff5` | `response_content_empty` | `length`, text `0` bytes; `1236/2860/4096` |
| `1c2622ce` | `qwen3.5:4b-8k-local` / v1 | `ar-20261028-83d1f58b4626` | `schema_validation_failed`: `uncertainties / type_invalid`와 utility `conditional_invalid` 2건 | `stop`, text `2106` bytes; `4809/625/5434` |
| `1c2622ce` | `qwen3.5:4b-8k-local` / v2 | `ar-20261028-98426c9f2270` | `accepted`: schema·guard·provenance 통과 | `stop`, text `1807` bytes; `4978/562/5540` |

각 record는 ignored local `.local/artifacts/pr278-baseline/` 또는 `.local/artifacts/pr278-live-1c2622ce/` 아래에 있다. PR 검토자는 원격에서 해당 파일을 열 수 없다. Raw response·prompt·secret은 저장하지 않았으며 이 표는 sanitized record에서 추출했다.

### Observed Context Configuration

실제 Ollama `/api/show`에서 `qwen3.5:4b-8k-local`의 `num_ctx=8192`를 확인했다. 기본 Qwen3.5가 실행 중일 때 `/api/ps`에서 active `context_length=4096`을 확인했다. 모델 아키텍처가 지원하는 최대 context 값은 이 active runtime 설정과 다르므로 context 여유의 증거로 사용하지 않는다. `qwen2.5-coder:7b`의 `/api/show`에는 explicit `num_ctx`가 없었다.

## Review and Next Transition

첫 구현의 outer Review에서 offline 통과만으로 목표가 닫히지 않음을 확인했다. v1은 JSON 생성 실패가 아니라 field type/conditional 실패였고, 첫 v2는 오류를 줄였지만 허용되지 않은 contribution kind가 남았다. **Loop 1/30 closed; acceptance open; next Research → Plan → bounded prompt refinement.** Qwen3.5 live 비교와 `review-lead`의 독립 code review가 진행 중이다.

후속 Research에서 기본 Qwen3.5의 v1/v2 모두 `length`, 0-byte content와 정확한 4096-token total을 관찰했다. 적어도 이 두 호출은 schema field 오류와 다른, context 한도에서 본문이 생성되지 않은 실패다. 8k 변형으로 같은 비교를 진행한다. Qwen2.5의 남은 enum 위반에는 finding kind와 utility kind를 명시적으로 구분하고 작은 JSON contribution 예시를 추가하는 최소 v2 보완을 계획한다. 모델별 transport 변경이나 schema repair는 추가하지 않는다.

8k v1은 배열·priority 위반으로 실패했지만 8k v2는 통과했다. Context 확대만으로 해결되는 문제가 아니며 v2 instruction의 구체화가 함께 필요하다는 비교 근거다. Qwen2.5 잔여 enum 위반에는 두 enum의 구별과 네 contribution kind의 유효 JSON 예시를 추가했다. 예시는 현재 출력 계약으로 parse하고 kind 전체를 포함하는지 검사해 향후 계약과 예시의 drift를 탐지한다. 초기 v2 실험도 위의 revision/digest로 보존하며 공개 전 instruction 보완의 결과와 섞지 않는다.

### Independent Review

`review-lead`가 quality/adversarial 두 specialist와 전체 21개 변경 파일(`2d26ef7f` → `1c2622ce`)을 독립 검토했고 `changes_required` 1건을 반환했다. 실제 SDK가 `finish_reason=[]|{}`를 반환하면 새 set membership에서 `TypeError`가 발생해 typed result와 provenance를 우회한다는 `current_required / direct_regression` finding이다. 실제 live provider에서 이 타입을 관찰한 것은 아니다.

문자열 타입 확인 후 `unknown`으로 정규화하도록 수정하고 SDK adapter 및 실제 service/evidence 경로의 두 비정상 타입 회귀를 추가했다. 새 source 상태에 대한 후속 독립 assessment는 아직 대기 중이다. 최초 review의 독립 focused 검증은 quality 27 passed, adversarial 19 passed였으며 full/live는 caller의 실행 근거와 구분했다.

## Prevention Boundary

회귀 테스트는 잘못된 배열 타입·priority 조건·JSON 문법·빈 본문, 오류 path/개수 제한과 원문 비노출, 실제 SDK의 stop/length/null/빈 choices, valid length 응답의 기존 acceptance, v1 고정 digest와 version별 replay, invalid version의 호출 전 거부를 다룬다. 실패 원인 구분과 containment를 자동으로 검증하며 모델의 의미적 품질이나 모든 미래 출력의 성공을 보장하지 않는다.
