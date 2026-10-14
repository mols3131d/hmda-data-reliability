---
type: review
title: Langfuse Integration Code Review
description: Review AI의 Langfuse projection, provenance, annotation과 관련 테스트를 검토하고 합성 입력 타입 비교 결함의 로컬 재현 근거를 기록한다.
tags:
  - domain:review-ai
  - langfuse
---

# Langfuse Integration Code Review

> [!IMPORTANT]
> **Changes Required**: 합성 입력 비교가 JSON 타입 차이를 놓치는 Major 결함 1건을 확인했다. Canonical JSON 비교와 회귀 테스트 보강이 필요하다. 이번 작업에서는 구현과 테스트를 수정하지 않았다.

- **Target**: [PR #251](https://github.com/mols3131d/hmda-data-reliability/pull/251)의 현재 Langfuse 연동 구현. PR diff가 새로 도입한 문제만이 아니라 기존 구현 전체의 계약 적합성을 검토했다.
- **Revision**: `2c3b61cd021267649f1cbc76f1c149abf93598f9`, `agent/refactor/review-ai-evaluation-subdomain`. 2026-10-02 KST에 HEAD와 tracked-clean 상태를 확인했다. 기존 미추적 Inbox 자료와 dependency lock 자료는 검토 대상에서 제외했다.
- **Scope**: Langfuse adapter 전체, live harness의 projection/provenance 연결부, 전용 테스트, 직접 연결된 evidence/prompt/evaluation 계약, 고정 SDK `4.15.6` 및 projection 개발 가이드. 일반 Review AI 재설계와 실제 원격 평가 운영은 제외했다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Major | Python 객체 동등성이 boolean/정수 입력 차이를 허용해 prompt digest와 전송 입력의 연결이 깨진다. | 타입을 보존하는 canonical JSON 비교로 대조하고 타입 불일치 거부 테스트를 추가한다. |

## Details

### F1: Synthetic Input Equality Loses JSON Type Identity

#### Locations

- [Langfuse adapter](../../src/hmda_reliability/review_ai/evaluation/langfuse.py#L68): `project_invocation()`의 입력 비교. 같은 함수는 102행 이후에 record가 아니라 fresh `expected_input`을 payload에 복사한다.
- [Live harness](../../scripts/run_agentic_review_live.py#L362): `_verify_live_provenance()`는 기록 자체로 prompt를 재렌더링한다. Fresh 합성 입력의 prompt digest와 직접 비교하지 않는다.
- [Prompt renderer](../../src/hmda_reliability/review_ai/prompt.py#L147): `render_canonical_input()`은 JSON 직렬화 결과를 digest에 반영한다.
- [Projection tests](../../tests/review_ai/evaluation/test_langfuse_projection.py#L122): 입력 불일치 검사는 빈 입력을 사용하며 boolean/정수 경계를 다루지 않는다.
- [Canonical Spec](../../openspec/specs/reliability-agentic-review/spec.md#L220): 현재 합성 입력과의 일치 및 불일치 시 projection 생략 계약.

#### Evidence

`record.canonical_input != expected_input`은 Python dict 비교다. Python의 `True == 1`과 달리 JSON의 `true`와 `1`은 서로 다른 값과 타입이며, prompt renderer도 서로 다른 digest를 만든다. 따라서 입력에서 boolean을 동등한 정수로 바꾸고 prompt digest를 재계산한 record는 자기 자신에 대한 provenance 검사를 통과하면서 fresh 합성 입력과 같다고 판정된다. 이후 projection은 fresh boolean 입력과 정수 입력에 대응하는 prompt digest를 함께 내보낸다.

로컬에서 정상 fixture의 `draft.requires_approval`을 `bool`에서 `int`로 바꾸고 digest를 재계산했다. `project_invocation()`은 거부하지 않았다. 별도 확인에서는 변경된 record를 `model_dump_json()`과 `model_validate_json()`으로 왕복한 뒤 `_verify_live_provenance()`에 전달했으며 역시 `True`를 반환했다. 파일이나 원격 데이터를 변경하지 않은 인메모리 재현이다.

핵심 재현은 저장소 루트에서 다음과 같다.

```bash
.venv/bin/python - <<'PY'
from copy import deepcopy
from runpy import run_path
from hmda_reliability.review_ai.evaluation.langfuse import project_invocation
from hmda_reliability.review_ai.prompt import render_canonical_input

record = run_path('tests/review_ai/evaluation/test_langfuse_projection.py')['record'].__wrapped__()
expected = deepcopy(record.canonical_input)
modified = deepcopy(expected)
modified['draft']['requires_approval'] = int(modified['draft']['requires_approval'])
prompt = render_canonical_input(modified, record.prompt_identity, max_prompt_bytes=65536)
changed = record.model_copy(update={'canonical_input': modified, 'prompt_digest': prompt.prompt_digest})
payload = project_invocation(changed, expected_input=expected)
print('python_input_equality:', modified == expected)
print('prompt_digest_changed:', prompt.prompt_digest != record.prompt_digest)
print('projected_input_type:', type(payload['input']['draft']['requires_approval']).__name__)
PY
```

관측 결과는 `python_input_equality: True`, `prompt_digest_changed: True`, `projected_input_type: bool`이다. JSON 왕복 추가 확인에서는 `persisted_record_input_type: int`, `harness_provenance_accepted: True`였다.

#### Impact

현재 합성 사례와 정확히 일치하는 입력만 전송한다는 provenance 경계가 깨지고, Langfuse에 표시되는 입력과 기록된 prompt digest가 다른 입력을 가리킬 수 있다. 정상 생성 경로가 언제나 이 값을 바꾼다는 뜻은 아니며, 타입이 달라진 기록을 거부해야 하는 검증 경로의 결함이다. 임의 문자열 유출, core Review AI 결과 변경 또는 원격 ingestion 성공까지 입증한 것은 아니다.

#### Action

기존 canonical JSON 직렬화 방식으로 record 입력과 독립 생성한 fresh 입력을 비교한다. 최소 회귀 검증은 boolean/정수 불일치와 재계산된 digest를 가진 기록을 사용해 provenance 자기 검사가 통과하더라도 projection/export 전에 거부되는지 확인해야 한다. 정상 record의 입력, 출력과 digest 보존은 함께 유지한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| Pass | Independent review | `review-lead`가 quality/adversarial specialist 결과를 대조해 `changes_required`와 F1을 반환했다. 첫 호출은 연결 오류였고 재시도에서 완료했다. |
| Pass | Projection module tests | `.venv/bin/python -m pytest tests/review_ai/evaluation/test_langfuse_projection.py -q`: **33 passed**, skip 없음, 2.40초. 설치된 `langfuse==4.15.6` media processor 테스트도 포함한다. |
| Fail | Exact synthetic input boundary | 인메모리 재현에서 `bool`/`int` 차이와 서로 다른 prompt digest가 있는 기록을 `project_invocation()`이 허용했다. 이는 pytest 실패가 아니라 기대 계약의 재현 실패다. |
| Fail | Provenance plus type mismatch | JSON 왕복 후에도 정수 타입이 남았고 `_verify_live_provenance()`가 변경 기록을 허용했다. Fresh-input 경계에서 거부할 수 없음을 확인했다. |
| Not Verified | Remote ingestion and human evaluation | 실제 provider 호출, Langfuse 전송, UI 표시와 다섯 rubric 항목의 사람 평가는 실행하지 않았다. |
| Not Verified | Current official documentation | `https://langfuse.com/llms.txt` 접근이 네트워크 도메인 정책으로 차단됐다. 제한을 우회하지 않았으며 SDK 관련 결론은 고정 버전과 로컬 테스트 범위로 제한한다. |

VS Code 테스트 도구는 해당 모듈을 발견하지 못해 구성된 Python 3.13 환경에서 pytest를 직접 실행했다. 기존 테스트 통과는 F1이 없다는 증거가 아니며, 현재 suite의 oracle이 해당 경계를 검사하지 않는다는 별도 재현 근거와 함께 해석해야 한다.

## Risks and Limits

F1 외에는 accepted payload의 필드 제한, 실패 payload 최소화, SDK child 격리와 timeout, media 변환 차단, core 결과 보존, `submitted_unverified`의 제한 및 annotation completeness/authenticity 구분에서 추가 material finding을 확인하지 못했다. 전용 로컬 테스트와 정적 검토의 범위이며 실제 원격 동작을 보증하지 않는다.

전체 repository suite, wheel 설치 후 실행과 실제 Langfuse 운영 환경은 검증하지 않았다. 모든 runtime 설정을 provenance 비교에 추가하는 문제는 명시된 계약상 필수 결함으로 채택하지 않았다. 이 보고서는 현재 구현 리뷰이며 F1을 PR #251의 리팩터링에서 새로 도입한 회귀라고 단정하지 않는다. 수정 후에는 타입 경계 회귀 테스트와 같은 범위의 fresh review가 필요하다.
