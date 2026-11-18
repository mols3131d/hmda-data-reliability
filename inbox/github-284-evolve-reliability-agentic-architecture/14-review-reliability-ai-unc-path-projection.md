---
type: review
title: "PR #284 Follow-up Review — UNC Path Projection"
description: "PR #284의 로컬 절대 경로 투영 경계를 최신 코드·계약·테스트와 대조한 후속 리뷰."
tags:
  - reliability-ai
  - pull-request
  - code-review
---

# PR #284 Follow-up Review — UNC Path Projection

> [!WARNING]
> **Revise** — `context.py`의 로컬 경로 정제 로직이 Windows UNC 경로를 놓친다. 일반 텍스트 `Evidence.summary`가 외부 provider의 canonical 입력으로 전달되는 경로가 있으므로, PR의 명시적인 경로 비노출 계약을 수용하려면 좁은 범위의 수정과 회귀 검증이 필요하다. 기존 리뷰 11~13에서 다룬 중복 도구 ID·복구 상태 전파 문제는 최신 코드에서 수정된 상태로 확인했다.

- **Target** — [PR #284: refactor: evolve reliability into agentic domains](https://github.com/mols3131d/hmda-data-reliability/pull/284)
- **Revision** — base `f1de6256cdd1e034f655b2f2ee3997481d0b195c` → reviewed head `990a60d18844e796e94616a4c64db86b193c40e1` (본 리뷰 파일 추가 전)
- **Scope** — `reliability_ai`의 provider 입력·도구 응답 경로 투영, 해당 정본 계약과 테스트, 11~13번에서 해결한 직접 관련 후보의 상태를 원격 소스로 확인했다. PR 174개 변경 파일 전체 전수 검토나 독립 dual-perspective 리뷰는 아니다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟡 Minor | Windows UNC 절대 경로가 canonical provider 입력과 일부 정제 출력에 그대로 남는다. | UNC 경로 정제 및 입력·도구·원격 관측 회귀 테스트 |

## Details

### F1 · Redact UNC Paths in Provider Projections

#### Locations

- [`src/hmda_reliability/reliability_ai/context.py`](../../src/hmda_reliability/reliability_ai/context.py)
  - `_ABSOLUTE_PATH` (90–93행): `file://`, POSIX `/...`, Windows drive 경로는 처리하지만 UNC `\\server\share\...`는 처리하지 않음
  - `project_review_evidence` (211–241행): `Evidence.summary`에 위 정규식을 적용
  - `project_remote_output` / `_project_public_value` (267–283행): 중첩 공개 출력의 문자열에 같은 정규식을 적용
- [`src/hmda_reliability/reliability_ai/prompt/__init__.py`](../../src/hmda_reliability/reliability_ai/prompt/__init__.py)
  - `build_canonical_input`: 선택한 Evidence의 정제된 summary를 provider 입력의 `evidence`로 포함
- [`tests/reliability_ai/test_context.py`](../../tests/reliability_ai/test_context.py)
  - `test_provider_and_remote_projection_remove_nested_private_material` (227–292행): POSIX, `file://`, Windows drive 사례는 있으나 UNC 반례 없음
- [`openspec/specs/reliability-agentic-review/spec.md`](../../openspec/specs/reliability-agentic-review/spec.md)
  - `Canonical provider input projection`: 범용 파일 경로를 자동으로 provider에 포함해서는 안 된다는 계약

#### Evidence

Python 표준 라이브러리 `re`로 HEAD의 정규식을 동일하게 구성해 `sub('[private-path]', value)`를 적용했다. 다음 UNC 예시는 일치 항목이 없어 변경되지 않았다. 반대로 대조한 `C:\private\hmda.csv`, `/opt/private/hmda.csv`, `file:///home/private/a.csv`는 `[private-path]`로 치환됐다.

```text
input:    \\fileserver\private\hmda.csv
actual:   \\fileserver\private\hmda.csv
expected: [private-path]
```

이는 정규식 동작의 직접 확인이다. `Evidence.summary → project_review_evidence → build_canonical_input → provider` 전송 경로는 소스 기반으로 확인했으며, UNC 경로가 포함된 실제 provider 호출을 실행한 것은 아니다.

#### Impact

UNC 형태의 서버·공유 이름과 로컬 파일 경로가 provider 요청 및 허가된 원격 관측 입력에 남을 수 있다. 노출은 해당 문자열이 실제 Evidence에 존재하는 경우에 한하며, 원시 행·자격 증명 노출이나 승인 없는 복구 실행을 입증하는 결과는 아니다. 영향도는 제한적이지만 이번 PR의 명시적 비노출 계약과 직접 충돌한다.

#### Action

1. 최신 HEAD에서 실제 `build_canonical_input`과 `project_remote_output`을 사용해 UNC 경로 반례를 먼저 재확인한다. 반례가 잘못됐다면 finding을 수정 또는 기각한다.
1. 유효하다면 공통 정제 경계에서 UNC 형식을 최소 수정으로 처리하고, 기존 POSIX·drive·`file://` 처리와 정상적인 텍스트·식별자를 보존한다.
1. `test_context.py`의 기존 parametrized 사례에 UNC summary·중첩 도구 출력·원격 관측 출력의 긍정/부정 oracle을 추가한다. 독립 oracle은 실제 로컬 경로 문자열이 provider-visible 자료에서 사라져야 한다는 명세에 둔다.
1. 관련 focused pytest 및 영향받는 정적 검사를 실행한 뒤 현재 PR HEAD 기준 CI·readiness를 재확인한다. 해결 범위를 임의의 범용 경로 탐지기 재설계로 확대하지 않는다.

## Prior Review Recheck

| Earlier item | Current state | Evidence |
| --- | --- | --- |
| 11 · 중복 tool-call ID | **Resolved in source** | `runtime_ai/provider.py`의 정규화 후 `seen_ids` 검증 및 `test_duplicate_sdk_tool_call_ids_fail_before_dispatch`의 SDK 반례 |
| 11/12 · `diverged_after_profile_failure` | **Resolved in source** | `execution/service.py`의 `partial` 분류 및 `test_post_mutation_failure_preserves_reconciliation_evidence` 사례 |
| 12 · 금지 도구 반환 oracle | **Resolved in tests** | `test_delegated_task_enforces_empty_tool_allowlist_and_timeout`가 `tool_not_allowed`·영수증 부재를 검증 |
| 11 · custom handler JSON serialization | **Follow-up, non-blocking** | 기본 handler 경로의 현재 결함으로 입증되지 않았으며 기존 [13번 수정 보고](13-report-reliability-ai-final-review-remediation.md)와 같은 보류 판단 유지 |

기존 항목은 [13번 수정 보고](13-report-reliability-ai-final-review-remediation.md)에 상세 근거가 있다. 위 상태는 **코드·테스트 구조 대조**이며 이번 세션의 pytest 재실행 결과가 아니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Reviewed target·source·contract 확인 | GitHub PR #284 base/head 및 관련 코드·정본 OpenSpec·테스트를 직접 읽음 |
| ✅ Pass | UNC 정규식 반례 | Python `re`로 현재 정규식과 UNC 입력의 불일치 및 POSIX/drive/`file://` 정상 치환을 직접 확인 |
| ✅ Pass | 최신 HEAD CI Lite | [GitHub Actions run 42510947442](https://github.com/mols3131d/hmda-data-reliability/actions/runs/42510947442) `completed / success`; 선택된 `check` job 성공 |
| ✅ Pass | 11~13 수정 항목 소스 대조 | provider 정규화, 복구 결과 상태 분류 및 직접 연관된 회귀 assertion 정적 확인 |
| ⚪ Not Verified | UNC end-to-end 재현·focused/full pytest | 이 세션에서는 실행하지 않음. 정규식 반례를 전체 서비스·모델 요청 재현으로 과장하지 않음 |
| ⚪ Not Verified | 실모델 재실험·인간 평가·독립 reviewer | 본 리뷰 범위에서 수행하지 않음. 과거 CI 성공은 모델 효용을 증명하지 않음 |

## Local Agent Handoff

로컬 에이전트는 이 리뷰를 자동 수용하지 않는다. **현재 HEAD에서 명세·기존 safeguard·반례를 독립적으로 검토해 `Accept / Reject / Revise / Defer`를 결정**한다. 채택한다면 F1 한 경계의 최소 수정과 실패→성공 회귀 테스트로 마무리하고 실제 실행 결과를 기록한다. 불일치하면 근거를 남겨 수정·기각한다. 기존 복구·provider 계약, history, 정본 범위와 다른 문제까지 묶어 변경하지 않는다.

## Risks and Limits

- 검토 기준 HEAD 이후 변경이 있다면 결과를 새 코드에 다시 적용해야 한다.
- 정적 결함 및 제한된 정규식 재현 외에 실제 provider 전송 경로는 테스트되지 않았다.
- 보고서 작성 자체는 코드 수정, GitHub approval, Draft 해제 또는 merge 권한을 부여하지 않는다.
