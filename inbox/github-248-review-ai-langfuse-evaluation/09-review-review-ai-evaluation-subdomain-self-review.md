---
type: review
title: Review AI Evaluation Subdomain Self-Review
description: PR 251 리팩터링의 동작 보존과 테스트 검출력을 확인한 셀프 리뷰이며, nested comparison JSON 검증 공백의 재현 근거를 기록합니다.
---

# Review AI Evaluation Subdomain Self-Review

2026-09-27 KST. **Assessment: changes_required — 테스트 검증 공백 1건.** 검토한 현재 구현에서 새 runtime defect는 확인하지 못했다. 다만 직렬화 호환성 테스트가 nested field 변경을 놓치는 것을 임시 mutation으로 재현했다. 구현의 현재 JSON 호환성과 테스트가 미래 회귀를 검출하는 능력은 별도 결과다.

이 결과는 구현자가 수행한 셀프 리뷰다. 독립 리뷰나 approval이 아니며, [이전 구현 보고서](08-report-review-ai-evaluation-subdomain-refactor.md)의 adversarial specialist 미확보 상태를 해소하지 않는다. Source, tests, 기존 Inbox 문서, Git과 GitHub는 수정하지 않았다.

## Reviewed Scope

- **Base:** `6e64cc70a5dca8ff8cd423a9f2240848f4b2e7dd`
- **Head:** `47713d1b1668317a7b3b117c87a379dac14aa976`
- **PR:** #251. GitHub read로 위 base/head와 open Draft 상태를 확인했다.
- **Implementation:** `review_ai.evaluation.value`, `review_ai.evaluation.langfuse`, 두 package facade, live harness import와 child entrypoint.
- **Contracts:** Canonical Review AI Spec, 새 OpenSpec Change의 design/tasks, domain/testing guide와 public API rename 결정.
- **Tests:** Evaluation, Langfuse, public-surface, live-harness 테스트 및 직접 영향을 받는 Review AI/Runtime AI suite.

모듈 이동과 symbol rename이 평가·비교, output identity, annotation 검증, optional export의 의미를 바꾸는지 추적했다. Intentional pre-1.0 API breaking change는 결함으로 분류하지 않았다. Recovery evaluation과 실제 원격 Langfuse 환경은 검토 대상에서 제외했다.

## Findings

### F1. Nested comparison serialization changes escape the compatibility test

- **Severity:** P2 — test coverage gap.
- **Disposition:** current_required / acceptance_gap.
- **Evidence strength:** Observed.
- **Location:** [새 compatibility test](../../tests/review_ai/test_utility_evaluation.py#L131), 특히 top-level field set 검사와 일부 scalar/digest assertion. [CriterionDelta](../../src/hmda_reliability/review_ai/evaluation/value.py#L112)의 serialized score field names는 고정하지 않는다.

Canonical Spec은 API rename 후 serialized field names와 enum values가 기존 비교 계약과 같아야 한다고 요구한다. OpenSpec Task 1도 대표 serialized comparison을 이동 전에 고정하도록 명시한다. 현재 테스트는 최상위 key set, `status`, `decision`, `rubric_id`와 output digests를 확인하지만 `criterion_deltas` 내부 key/value 전체를 기존 JSON과 비교하지 않는다. Round-trip 테스트는 현재 모델로 쓰고 현재 모델로 읽어, 함께 바뀐 schema를 검출하지 못한다. Output digest도 comparison의 score/delta 구조를 포함하지 않는다.

`/tmp`의 package 복사본에서 `value.py`에만 다음 변경을 적용하고 평가 테스트는 그대로 실행했다. Repository source/test는 변경하지 않았으며 임시 복사본은 실행 후 제거했다.

```text
baseline_score -> before_score
candidate_score -> after_score
```

Constructor, validator와 내부 참조를 같은 문자열 치환으로 함께 바꿨다. 비교 기록의 실제 nested JSON key는 다음처럼 변했다.

```text
['after_score', 'before_score', 'criterion', 'delta']
```

그런데 기존 `test_utility_evaluation.py` 전체는 **15 passed, 1 warning**이었다. Warning은 임시 실행의 `/dev/null` config에 `unit` marker가 등록되지 않아 발생했으며 테스트가 skip된 것은 아니다. 실행은 기존 venv Python에서 `pytest -c /dev/null --rootdir <temporary-root> -p no:cacheprovider -p no:tach -q test_utility_evaluation.py`로 수행했다. Import origin도 임시 package 아래인지 먼저 확인했다.

이 변경이 실제 들어가면 기존 consumer가 기대하는 `baseline_score`/`candidate_score`가 사라지지만 이번에 추가한 compatibility test는 통과한다. 현재 branch가 그 변경을 포함한다는 뜻은 아니다. 이전 baseline의 테스트에도 완전한 golden guard는 없었으며, 이번 finding은 새 호환성 요구와 추가된 테스트의 검증 범위 차이에 관한 것이다.

**최소 개선:** Base revision에서 얻은 대표 comparison JSON 전체를 독립 golden으로 고정하고 nested score/delta field와 enum value까지 비교한다. Golden을 새 모델로 다시 생성해 expected로 쓰지 않는다. 위 mutation이 그 검사에서 실패하는지 확인하면 된다.

## Validation

| Check | Current result | Meaning |
| --- | --- | --- |
| Review AI and Runtime AI | 183 passed, skip 없음 | 현재 head에서 기존 도메인 suite를 실행했다. |
| Baseline differential | 21 comparisons identical | 정상, role/case/version/revision/fact mismatch의 7개 상황을 human decision 3종으로 비교했다. Assessment/rubric JSON과 comparison JSON bytes가 base와 같고, 양방향 comparison loading도 같았다. |
| Markdown rendering | Intended heading change only | 이전 `Review AI Utility Comparison` heading을 새 `Review AI Value Comparison`으로 치환하면 대표 rendering이 동일했다. |
| Actual child entrypoint | Pass | Repository 밖 `/tmp`에서 `python -I -m hmda_reliability.review_ai.evaluation.langfuse`를 실행했다. Malformed JSON stdin은 exit 1과 빈 stdout/stderr로 종료됐다. JSON parsing에서 실패하므로 SDK/network는 호출하지 않았다. |
| Fresh evaluation import | Pass | 새 isolated interpreter에서 evaluation package를 import해 optional Langfuse SDK가 `sys.modules`에 들어오지 않는 것을 확인했다. |
| Mutation probe | False green reproduced | Nested score field names를 바꾼 임시 package에서 unchanged evaluation tests 15개가 통과했다. 현재 코드의 pass 결과와 구분한다. |
| Static and architecture | Pass | Project-wide `ty check`, Ruff check, `tach check`. |
| OpenSpec | Pass | `openspec validate review-ai-evaluation-subdomain-refactor --strict`. |

Baseline differential은 현재 구현의 호환성을 확인하는 transient review evidence다. 이 검사를 repository regression test로 남긴 것은 아니므로 F1의 지속적인 검증 공백을 해소하지 않는다. 새 child command probe도 malformed-input 실행 경계만 확인하며 실제 SDK export 성공을 증명하지 않는다.

## Remaining Limits

전체 repository pytest는 이번에 다시 실행하지 않았다. 이전 보고서가 기록한 orchestration Airflow timeout은 당시 실행의 제한이며 현재 head의 전체 suite pass 근거로 사용하지 않았다. Domain suite가 통과해도 repository 전체 correctness를 보장하지 않는다.

External Python consumers, wheel 설치 후 실행, 실제 Langfuse ingestion/UI와 human evaluation은 Not Verified다. 기존 독립 review-lead의 adversarial coverage gap도 그대로 남는다. 완료된 이전 OpenSpec design의 옛 module/symbol 명칭은 revision 당시 설계 기록으로 취급했으며 current implementation consumer로 판단하지 않았다.

```yaml
revision:
  reviewed_base: 6e64cc70a5dca8ff8cd423a9f2240848f4b2e7dd
  reviewed_head: 47713d1b1668317a7b3b117c87a379dac14aa976
  review_kind: self_review
  assessment: changes_required
  required_findings: 1
  implementation_defects_found: 0
```
