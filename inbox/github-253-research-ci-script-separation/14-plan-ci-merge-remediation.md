---
type: plan
title: "PR 253 Merge Remediation Plan"
description: "PR #253의 최신 병합 검토에서 확인한 Inbox 정책 불일치, archive 전송 중단과 revision 입력 오류를 개선하고 재검증할 때 사용하는 작업 계획입니다."
tags:
  - ci
  - pull-request
  - remediation
  - validation
---

# PR 253 Merge Remediation Plan

[PR #253](https://github.com/mols3131d/hmda-data-reliability/pull/253)은 **CI가 성공했지만 병합 권고는 보류**한 상태다. Inbox 제외 정책의 구현 적용 범위를 확정하고, 재현된 archive 전송 중단 처리와 잘못된 revision 입력을 수정한 뒤 재검증한다.

**첫 판단:** 이미 선택한 Inbox 제외 정책을 이번 PR의 구현과 테스트에 적용하는 것을 권고한다. 정책을 다시 선택하는 문제가 아니라 적용 시점과 구현 범위의 확정이다. 이 문서는 개선 계획이며 구현 착수, commit·push, Ready 전환, 승인이나 병합을 허가하지 않는다.

## State Basis

2026-10-07 검토 기준이다. Owning branch는 `agent/research-ci-script-separation`이며 이 문서는 해당 PR 작업의 non-canonical artifact다. 코드와 계약의 정본을 대체하지 않는다.

| Item | Reviewed State |
| --- | --- |
| Base | `5532dca2fd93696d40ba870471fa2359c5662335` |
| Head | `ee86aff4a7a91d21541cd8f9f8a01597907ff0c1` |
| Prospective merge | `c3a4960a27d26b91b93df4da2f953e854c152f88`; 부모가 위 base/head와 일치 |
| CI | [Run 37552804933](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37552804933): success |
| Lifecycle | Open·Draft, 충돌 없음. Protection API는 HTTP 403으로 요구사항을 확정하지 못함 |

전체 PR의 구현, 테스트와 현재 계약을 quality/adversarial 독립 리뷰로 대조했다. 추가된 과거 Inbox 보고서는 전수 검토하지 않았으며 현재 correctness의 근거로 채택하지 않았다. 아래 사실과 검증 결과는 이 revision에 한정한다. Base, head나 정책이 바뀌면 영향을 받는 근거를 다시 확인한다.

## Work Items

Finding ID는 독립 리뷰의 식별자를 유지한다. `F3`은 비차단 안내 보완이며, `F4`는 사용자에게 보고한 세 번째 문제다. 사용자 후속 요청으로 구현과 PR 전달을 승인받았다. F1·F2·F4·F3은 구현했고 현재 결과는 [완료 보고서](15-report-ci-merge-remediation-completion.md)와 [독립 리뷰 보고서](16-review-ci-merge-remediation.md)를 따른다. 아래 원래 재현과 계획은 기준 revision의 기록으로 유지한다.

| ID | Importance | Next Action |
| --- | --- | --- |
| F1 | Medium | Inbox 제외 정책의 구현 적용 범위 확정 후 정합화 |
| F2 | Medium | 불완전한 archive 응답을 실패로 처리 |
| F4 | Low | 옵션형 입력을 포함한 잘못된 revision 거부 |
| F3 | Low, non-blocking | 제한된 root-blob hash 예외를 안내에 반영 |
| Delivery | 병합 전 정합화 | 최신 revision·CI·변경 내용으로 PR 본문 갱신 |

### F1 Inbox Policy Alignment

**확인된 사실:** [Inbox 제외 정책](../../docs/development/ci/markdown-validation.md#inbox-exclusion)은 `inbox/**` 전체의 CI 검증 제외를 선언한다. 그러나 [classifier](../../scripts/ci/classify_changes.sh#L226)는 존재하는 Inbox Markdown에 `markdown=true`, `inbox=true`를 설정하고 [workflow](../../.github/workflows/ci-lite.yml#L42)는 artifact validator를 실행한다. [기존 선택 테스트](../../tests/scripts/ci/test_ci_classifier.py#L221)도 이를 기대하며, 위 CI run에서도 해당 단계가 실행됐다.

이는 이번 정책 변경과 보존된 실행 동작의 불일치다. 기존 CI가 새로 고장 난 것으로 해석하지 않는다.

**필요한 결정:** PR owner가 현재 정책을 이번 PR에서 구현할지 확정한다. 적용 대기라면 정책을 되돌리는 대신 시행 상태와 현재 미구현 동작을 명확히 구분한다. 이 계획 작성만으로 구현 범위를 확대하지 않는다.

현재 적용을 승인하면 다음 범위만 수정한다.

- Classifier와 Markdown 파일 수집에서 Inbox를 제외한다. 확장자별 다른 분류에도 Inbox-only 변경이 검증을 선택하지 않는지 확인한다.
- Inbox 전용 workflow 검증 단계를 제거하고 대응 테스트를 갱신한다. Validator 자체와 Inbox 작성 규칙을 삭제할 필요는 없다.
- [Testing Guide](../../docs/development/testing.md#pull-request-ci)와 PR 본문을 최종 동작에 맞춘다. 과거 Inbox 보고서는 역사적 기록으로 유지한다.

**완료 조건:** 존재하는 Inbox Markdown, 비-Markdown 파일, 삭제와 이름 변경에 대해 Inbox-only 변경은 검증 단계를 선택하지 않는다. Workflow는 계속 생성된다. 복합 변경은 다른 경로의 필수 검증을 보존하며, `docs/**`의 차단 lint와 다른 Markdown의 비차단 포맷 제안도 유지된다. Classifier뿐 아니라 파일 수집과 workflow 연결을 대응 계약 테스트로 확인한다.

### F2 Archive Response Completeness

**확인된 사실:** [archive 수집](../../scripts/agent_routes/sources.py#L182)은 제한된 크기로 읽지만 Content-Length 미충족을 확인하지 않는다. 실제 `HTTPResponse`를 사용한 재현에서 320바이트를 광고하고 310바이트만 전송했는데도 CLI가 `exit 0`으로 끝나고 mocked `write_routes`를 호출했다. ZIP의 마지막 comment만 잘라 member와 Skill 내용 hash는 정상으로 유지했다. 실제 route 파일을 쓰는 실험은 하지 않았다.

**최소 수정:** 기존 다운로드·압축 해제 크기 상한을 유지하면서 HTTP body의 완결성을 확인한다. 길이가 없는 정상 응답을 일괄 거부하거나 제한 없는 read, 새 retry 체계로 우회하지 않는다. 확인된 중단은 기존 오류 경로로 전파한다.

**회귀 검증:** 기존 [HTTP 중단 테스트](../../tests/scripts/test_generate_agent_routes.py#L572)에 파싱 가능한 ZIP의 Content-Length 중단을 추가한다. 현재 archive 분기는 chunked 중단과 `--check`를 사용하므로 새 사례는 쓰기 모드도 포함해야 한다.

**완료 조건:** 중단 응답은 CLI `exit 2`이며 기존 route 내용이 보존되고 새 route를 쓰지 않는다. 정상 archive는 기존 결과를 유지한다. 크기 초과, chunked 중단, metadata 오류와 기존 hash·경로 검증도 유지된다. 이 수정은 실패 계약 보완이며 Skill 내용 hash 우회가 확인됐다는 의미는 아니다.

### F4 Revision Input Validation

**확인된 사실:** [변경 파일 수집 helper](../../scripts/ci/changed_files.sh#L13)는 base/head를 Git 옵션 위치에 전달한다. `collect_changed_files files --quiet HEAD`는 깨끗한 작업 트리에서 성공하고 파일 0개를 반환했다. 잘못된 입력이 검증 없는 성공으로 바뀌는 로컬 인터페이스 문제이며, 고정된 CI 입력의 shell injection으로 해석하지 않는다.

**최소 수정:** Base와 head를 옵션으로 소비되지 않는 유효 revision으로 확인하고, 검증한 값을 사용해 비교한다. 오류는 빈 배열이나 성공으로 바꾸지 않는다. 기존 ref와 SHA를 사용하는 정상 호출은 유지한다.

**완료 조건:** 옵션형 입력과 존재하지 않는 revision은 nonzero로 끝난다. `HEAD^1`, `HEAD`, branch ref와 SHA는 유효할 때 정상 비교한다. 유효한 빈 diff는 성공으로, 삭제된 파일은 도구 입력에서 제외하는 기존 계약으로 유지한다. [CI step 테스트](../../tests/scripts/ci/test_ci_steps.py)에서 helper와 Markdown·Python 호출자의 실패 전파를 확인한다.

### F3 Hash Guarantee Wording

[Route 안내](../../.rulesync/README.md#L14)는 전체 폴더 hash만을 조건으로 설명하지만 [구현](../../scripts/agent_routes/sources.py#L285)은 ref 없는 허용 source의 root Skill에 단일 `SKILL.md` hash도 인정한다. 해당 제한된 예외와 설치 방식이 lock에 기록되지 않는 한계를 안내에 반영한다.

이는 비차단 문서 보완이다. 승인된 예외를 제거하거나 허용 source를 넓히는 작업이 아니며, nested Skill·명시적 ref·그 밖의 source에 대한 전체 폴더 검증은 유지한다.

## Execution Order

1. F1의 구현 적용 범위를 확정한다. 그 외 항목의 수정 범위도 승인된 작업에 한정한다.
1. F2와 F4의 재현을 기존 테스트에 고정하고, 최소 수정 후 각각의 focused 검증을 실행한다.
1. F1 적용이 승인됐다면 classifier, 파일 수집, workflow, 테스트와 현재 동작 안내를 정합화한다. Inbox 제외로 다른 경로의 검증이 빠지지 않는지 확인한다.
1. F3 안내를 보완하고 관련 계약 테스트를 함께 실행한다.
1. 전달 시점의 base/head와 prospective merge CI를 확인하고 PR 본문을 갱신한다. Head가 다시 바뀌면 해당 근거도 갱신한다.
1. 수정한 범위의 독립 재리뷰로 finding이 해소됐는지 확인한 뒤 병합 준비를 다시 판단한다.

## Validation

### Existing Evidence

아래는 수정 전 revision의 근거이며 개선 완료 증거가 아니다.

| Check | Result | Boundary |
| --- | --- | --- |
| 로컬 CI·route·agent-assets 관련 suite | `211 passed in 8.45s` | Head 환경의 계약·회귀 검증 |
| 최신 prospective merge CI | `416 passed in 10.08s`, 추가 `66 passed, 95 deselected in 2.39s` | 위 run과 merge revision의 실행 결과 |
| F1 재현 | Inbox-only 기존 Markdown 입력에서 `markdown=true`, `inbox=true` | 새 정책과 현재 선택의 충돌 |
| F2 재현 | HTTP 10바이트 미수신 상태에서 `exit 0`, mocked 쓰기 호출 | 실패 계약 공백; 내용 hash 우회 아님 |
| F4 재현 | 옵션형 base 입력에서 성공·파일 0개 | 로컬 revision 입력 계약 공백 |

CI의 Tach, 별도 runtime smoke, OpenSpec, JSON, TOML과 Lefthook 단계는 skipped였으며 pass로 세지 않는다. 실제 project Skills lock은 tracked되지 않아 route 검증 성공을 그 lock의 end-to-end 증명으로 확대하지 않는다.

### Required Rechecks

각 수정은 해당 재현과 기존 테스트부터 확인한다. 관련 slice를 수정한 뒤 함께 확인하는 범위는 다음과 같다.

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --no-sync pytest -p no:cacheprovider \
  tests/scripts/ci \
  tests/scripts/test_generate_agent_routes.py \
  tests/scripts/test_agent_assets.py
```

수정한 Bash의 syntax, Python의 lint·format·type과 변경 문서의 Markdown·링크도 해당 파일 범위로 확인한다. Local head 결과와 prospective merge CI는 구분한다. 테스트 존재, 과거 성공과 scoped review만으로 최신 전체 변경의 통과를 주장하지 않는다.

## Completion Gate

- [x] F1의 적용 결정과 문서·구현·테스트가 일치한다.
- [x] F2와 F4의 실패 사례가 검출되고 정상 동작의 회귀가 없다.
- [x] 비용 최적화의 기존 boundary·smoke target과 성공 조건이 유지된다.
- [ ] PR 본문이 최신 head, CI와 Inbox 정책을 반영한다.
- [ ] 현재 base/head의 필요한 prospective merge 검증과 수정 범위 재리뷰를 확인했다.
- [ ] Draft, required checks, applicable feedback과 approval 요구사항을 별도로 확인했다. Protection 조회 불가를 승인 불필요로 해석하지 않았다.

## Boundaries

애플리케이션 변경, 전체 CI 재설계, 환경 분리, 새 dependency·retry·write-back 자동화와 권한 변경은 포함하지 않는다. 실제 Skills lock의 end-to-end 실행이나 전체 domain suite를 이번 tooling 수정의 무조건적인 선행 조건으로 추가하지 않는다.

로컬의 다른 Git object·ref 손상은 별도 환경 이슈다. 이번 계획은 복구나 history rewrite를 포함하지 않으며, 후속 전달에서도 관련 없는 변경과 force-push를 피한다. 이전 [병합 검토 snapshot](12-review-pr-253-merge-readiness.md)과 [인간 리뷰 가이드](13-guide-pr-253-human-review.md)는 각각의 기준 revision으로 읽는다.
