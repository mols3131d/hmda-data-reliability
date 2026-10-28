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

**Implemented and verified:** 코드 revision `babea53600c48d63049c2fa83c85ccfeb0a1c976`의 같은 synthetic case에서 `qwen2.5-coder:7b`와 8k context의 `qwen3.5:4b-8k-local`이 모두 schema·guard·durable provenance를 통과했다. 원인은 불충분한 출력 타입·조건 설명과 Qwen3.5의 부족한 active context로 분리했다. 원문 없는 실패 진단, 명시적 v2 instruction, 예시와 계약의 drift 검사 및 SDK 회귀를 구현했고 독립 review는 `clear`다.

이 PR 범위의 추가 구현 blocker는 없다. 사용자는 #278 merge와 후속 PR 준비를 요청했다. 실제 output에서 남은 수치 설명 오류·예시 복사·human utility 검증은 [후속 계획](04-plan-review-ai-output-quality-follow-up.md)에 인계한다. Qwen3.5에서 확인한 조건은 context 8192, output cap 4096, timeout 180초이며 모든 모델이나 기본 4096 context의 성공을 뜻하지 않는다. 범위와 옵션별 채택·기각 이유는 [계획](02-plan-review-ai-schema-resolution.md)을 따른다.

## Revision and Validation

| State | Evidence |
| --- | --- |
| Start base / PR head | `83538af4929c9d4cd533fa550e6b7e6aed22a5b8` / `2d26ef7f4f172fc179160f9193b06ec0ec0b49f8` |
| First implementation | `1c2622ce93ea18b1c98cb7558759f3c6cc8e030a` |
| Final code and live basis | `babea53600c48d63049c2fa83c85ccfeb0a1c976`; 후속 delivery commit은 Inbox 문서만 변경 |
| Baseline offline | `204 passed, 1 skipped`; Review AI + Runtime AI |
| Regression red | 구현 전 14 tests failed: diagnosis 7, v2 prompt 1, SDK metadata 6 |
| First implementation focused | `228 passed, 1 skipped`; `uv run --no-sync pytest -p no:tach tests/review_ai tests/runtime_ai -q --tb=short` |
| First implementation full suite | `1191 passed, 3 skipped in 124.11s`; `uv run --no-sync pytest -p no:tach -n 4 -q` |
| Final focused suite | `234 passed, 1 skipped in 2.56s`; 동일 focused command |
| Final full suite | `1197 passed, 3 skipped in 130.12s`; `uv run --no-sync pytest -p no:tach -n 4 -q -rs` |
| Static and contract checks | Ruff, project-wide `ty check`, `tach check`, modified Spec strict validation, rumdl, Inbox artifact validation, `git diff --check`: pass |
| Full Spec and packaging | OpenSpec `validate --all --strict`: `22 passed, 0 failed`; `uv build --wheel`: pass |

`-p no:tach`는 pytest의 affected-selection plugin만 끄고 선택된 범위를 실제로 전부 실행한다. 별도 `tach check`와 full suite의 boundary guard는 유지했다. 세 skip은 optional Langfuse SDK smoke, cached zizmor가 필요한 실제 audit, Windows npm/Node 전용 테스트다. 원격 projection 또는 human utility 평가는 실행하지 않았다.

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
| `babea536` | `qwen2.5-coder:7b` / v2 | `ar-20261028-a613ff9cd836` | `accepted`: schema·guard·provenance 통과 | `stop`, text `1751` bytes; `1390/503/1893` |
| `babea536` | `qwen3.5:4b-8k-local` / v2 | `ar-20261028-ce7a6c327159` | `accepted`: schema·guard·provenance 통과 | `stop`, text `2041` bytes; `5088/616/5704` |

각 record는 ignored local `.local/artifacts/pr278-baseline/`, `.local/artifacts/pr278-live-1c2622ce/`, `.local/artifacts/pr278-live-babea536/` 아래에 있다. PR 검토자는 원격에서 해당 파일을 열 수 없다. Raw response·prompt·secret은 저장하지 않았으며 이 표는 sanitized record에서 추출했다. 최종 두 호출은 `exit_code=0`, `attempt_count=1`, 동일 prompt digest `sha256:3636e263750d9e264df2142cea4b4bb6bc16af70d84f60402dcd0a6893b37322`를 기록했다. v1 digest는 수정 전후 모두 `sha256:14fccce9b74ee49fa70d41ea9a36dd184ff75bff65db416e1d871fd9b4f87899`다.

### Observed Context Configuration

실제 Ollama `/api/show`에서 `qwen3.5:4b-8k-local`의 `num_ctx=8192`를 확인했다. 기본 Qwen3.5가 실행 중일 때 `/api/ps`에서 active `context_length=4096`을 확인했다. 모델 아키텍처가 지원하는 최대 context 값은 이 active runtime 설정과 다르므로 context 여유의 증거로 사용하지 않는다. `qwen2.5-coder:7b`의 `/api/show`에는 explicit `num_ctx`가 없었다.

## Review and Next Transition

첫 구현의 outer Review에서 offline 통과만으로 목표가 닫히지 않음을 확인했다. v1은 JSON 생성 실패가 아니라 field type/conditional 실패였고, 첫 v2는 오류를 줄였지만 허용되지 않은 contribution kind가 남았다. Loop 1은 이 차이를 근거로 닫고 bounded prompt refinement로 진행했다.

후속 Research에서 기본 Qwen3.5의 v1/v2 모두 `length`, 0-byte content와 정확한 4096-token total을 관찰했다. 적어도 이 두 호출은 schema field 오류와 다른, context 한도에서 본문이 생성되지 않은 실패다. 8k 변형으로 같은 비교를 수행하고, Qwen2.5의 남은 enum 위반에는 finding kind와 utility kind를 명시적으로 구분하는 작은 JSON contribution 예시를 추가했다. 모델별 transport 변경이나 schema repair는 추가하지 않았다.

8k v1은 배열·priority 위반으로 실패했지만 8k v2는 통과했다. Context 확대만으로 해결되는 문제가 아니며 v2 instruction의 구체화가 함께 필요하다는 비교 근거다. Qwen2.5 잔여 enum 위반에는 두 enum의 구별과 네 contribution kind의 유효 JSON 예시를 추가했다. 예시는 현재 출력 계약으로 parse하고 kind 전체를 포함하는지 검사해 향후 계약과 예시의 drift를 탐지한다. 초기 v2 실험도 위의 revision/digest로 보존하며 공개 전 instruction 보완의 결과와 섞지 않는다.

### Independent Review

`review-lead`가 quality/adversarial 두 specialist와 전체 21개 변경 파일(`2d26ef7f` → `1c2622ce`)을 독립 검토했고 `changes_required` 1건을 반환했다. 실제 SDK가 `finish_reason=[]|{}`를 반환하면 새 set membership에서 `TypeError`가 발생해 typed result와 provenance를 우회한다는 `current_required / direct_regression` finding이다. 실제 live provider에서 이 타입을 관찰한 것은 아니다.

문자열 타입 확인 후 `unknown`으로 정규화하도록 수정하고 SDK adapter 및 실제 service/evidence 경로의 두 비정상 타입 회귀를 추가했다. 후속 독립 review는 `babea53600c48d63049c2fa83c85ccfeb0a1c976`의 8개 변경 파일과 직접 호출 경로를 검토해 **`clear`**를 반환했다. 이전 finding은 `resolved`이며 새로운 `current_required`, `scope_decision` 또는 blocker는 없다. Lead의 동일 SDK 재현도 stop·배열·object 모두 1회 호출로 통과했다.

최초 review의 독립 focused 검증은 quality 27 passed, adversarial 19 passed였고 최종 review에서는 각 specialist 28 passed였다. Full suite와 live 결과는 이 작업에서 실행한 caller evidence이며 독립 모델 재실행 또는 human utility 평가로 표시하지 않는다. Loop 2/30에서 현재 구현·검증·review의 acceptance를 확인하고 Finalize로 진행했다.

## Prevention Boundary

회귀 테스트는 잘못된 배열 타입·priority 조건·JSON 문법·빈 본문, 오류 path/개수 제한과 원문 비노출, 실제 SDK의 stop/length/null/빈 choices, valid length 응답의 기존 acceptance, v1 고정 digest와 version별 replay, invalid version의 호출 전 거부를 다룬다. 실패 원인 구분과 containment를 자동으로 검증하며 모델의 의미적 품질이나 모든 미래 출력의 성공을 보장하지 않는다.

## Handoff

원격 PR은 [#278](https://github.com/mols3131d/hmda-data-reliability/pull/278)이다. 현재 source와 full/live 검증 기준은 위의 `babea536`이며 delivery 문서 변경과 구분한다. 새 source 수정, 실제 provider/config 변경 또는 base 변경이 생기면 해당 검증과 review의 적용 가능성을 다시 판단한다. 재현·진단·prompt 선택 방법은 정본 [Evaluation Guide](../../docs/development/review-ai-evaluation.md#diagnose-a-failed-response)를 따른다.

PR #278의 구현 작업은 완료됐으며 사용자의 merge 요청에 따라 후속 계획 문서를 포함해 최종 검증 후 전달한다. 다음 PR의 재현 사례·수정안 비교·평가와 완료 기준은 [Output Quality Follow-up](04-plan-review-ai-output-quality-follow-up.md)을 따른다. Human utility나 Langfuse 원격 수집 완료를 이 보고서가 증명하지는 않는다.
