---
type: review
title: Current Reliability Test Design Audit
description: PR 272의 현행 테스트 전수 검토, 과거 finding 재판정과 회귀 보강 근거를 연결합니다.
---

# Current Reliability Test Design Audit

**State:** 2026-10-27 원격 동기화와 리뷰 대조 결과, 기록된 새 `current_required`는 없다. `e772c53f`의 독립 재검토 `clear` 이후 테스트·source·Spec 변경이 없으며 원격 CI도 268개 통과했다. Draft를 유지하고, 후속 의견의 담당 범위는 아래에서 구분한다.

- **Baseline:** `b16ad5734b4a5a35c1db3d12fe03124438e71348` (원격 PR head `7a93a60c8b345dadc401968e2100ba19a395fd52` + main `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`).
- **Scope:** Reliability 소유의 tracked test/support/design 28개 전체. Production·Spec은 계약 대조를 위해 읽으며 수정하지 않는다.
- **Historical evidence:** [과거 보고서](../01-review-historical/README.md)의 조사 revision은 `3ab899100fc0b35e23d464bd761f3b144a978ae7`이고 반입 기준은 PR #258 `bdce0f4e`다. 현재 결함으로 자동 승격하지 않는다.
- **Code revision:** `e772c53fb975232e776d240cb61ff9a13cb896d1`. 이 보고서의 후속 delivery는 검증 결과·인계 metadata만 바꾼다. 재개할 때 원격 head/base/check를 새로 확인한다.
- **Synchronized snapshot:** head `3faa7ffba787a14e899a3ab9918c275a0695193e`, base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`. 이전 전달 `22660aba` 이후 17개 commit은 [심층 리뷰](../03-review-chatbot-deep.md) 한 파일만 변경했다. 이 정리의 후속 delivery도 Inbox-only다.
- **Next:** 인간의 PR 검토. H3의 통합 검증은 #277, Spec·reporter·공용 hook 수정은 각 owner 또는 별도 범위 결정이 필요하다. 기존 인계의 “H1–H4 모두 #277” 표현을 아래 소유권으로 정정한다.

## Review Reconciliation

| Review source | Revision and result | Current use |
| --- | --- | --- |
| [Historical review](../01-review-historical/README.md) | code `3ab8991`, delivery `bdce0f4e` | 당시 finding을 아래 개별 disposition으로만 사용 |
| [Implementation audit](core.md), [recovery](recovery.md), [evaluation](evaluation.md) | baseline `b16ad573`, code `e772c53f`; 28-file 전수 조사·보강 | 현재 코드와 동일한 테스트·source·Spec의 기존 근거 |
| [Independent review](independent.md) | `a85cac28`의 F1 `changes_required` → 보정한 `e772c53f`의 `clear` | 최초 finding과 수정·재검토 이력 보존. 이번 정리에서 새 reviewer를 실행한 것은 아님 |
| [Chatbot deep review](../03-review-chatbot-deep.md) | R1–R13 이력과 R15 최종 판정; reviewed pre-write `61187fce` | 최신 후보 판정은 아래 표에 통합. 동일 세션의 정적 대조·문자열 probe를 새 독립 검토나 원본 renderer 재현으로 승격하지 않음 |
| GitHub review / conversation / inline thread | 동기화 head에서 각각 **0 / 0 / 0** | Inbox의 agent 리뷰와 GitHub에 제출된 리뷰·인간 승인을 구분 |

기존 독립 리뷰가 확인한 code revision 이후 코드는 바뀌지 않았다. 심층 리뷰 이력의 `blocked`는 해당 회차에 새 specialist를 실행하지 못한 기록이며, 그 자체로 기존 code assessment를 취소하거나 새 PR 결함을 의미하지 않는다. R10의 C14 수용 및 R11/R12의 `unknown`은 R15의 `drop`으로 대체됐다.

| Item | Reconciled disposition | Owner and next action |
| --- | --- | --- |
| Independent F1 | `resolved` | 선택 partition만 NULL 처리하도록 수정됐고 재검토 `clear`; 재수정 불필요 |
| Deep C1–C4, C6–C8, C10, C12–C13 | `drop` | 기존 oracle·scope가 해당 후보를 반박; 구체적인 새 반례 없이 재개하지 않음 |
| Deep C14–C15 | `drop` | 정본의 subset/정상 case 문구로 역명제·extra detection 전면 금지 요구를 추가하지 않음 |
| Deep C9 | `follow_up` | Spec owner가 `rejected_by/at` 필수 조건을 공개 계약으로 명시할지 결정. 현재 구현 결함 주장이 아님 |
| Deep C11 | `follow_up` | Reliability test owner가 row-only UPDATE/INSERT에도 schema hash가 불변인 반례의 가치를 판단. Mutant 실행은 미확인 |
| Deep C16 | `follow_up`, conditional | Reliability reporter owner가 허용 입력·escaping 정책을 정하고 원본 model/reporter→renderer로 재현. 기존 문자열 조립 probe는 source 실행 증거가 아님 |
| H1 | `scope_decision` | Manifest node/edge 거부 정책은 Reliability source·Spec owner 결정. #277에 production/Spec 쓰기 권한을 부여하지 않음 |
| H2 / Deep C5·C18 | `scope_decision` | Spec owner가 existing/aliased DB scenario의 누락 THEN을 보완. 기존 무변경 거부 테스트가 있어 test 무보호 주장으로 확대하지 않음 |
| H3 | `deferred` | #277이 선행 PR 통합 revision에서 approval→recovery→revalidation 등 실제 도메인 접점 검증 |
| H4 / Deep C17 | `deduplicate`, `scope_decision` | 기존 [#270 F3](https://github.com/mols3131d/hmda-data-reliability/blob/agent/test/audit-data-operations-design/inbox/github-270-audit-data-operations-design/02-review-data-operations-tests.md#f3--major-hook-git-environment-escapes-temporary-repositories)와 같은 공용 hook 환경 문제. 실제 수정 owner/범위를 명시적으로 배정해야 하며 이번 test-only 변경의 신규 결함으로 중복 계산하지 않음 |
| Deep C19 | `drop` | Domain CI 성공·#277의 초기 문서 CI 성공을 로컬 Git hook 안전성 증거로 사용하지 않음 |

위 표는 기존 리뷰의 판정을 대조한 정리다. 이번 작업은 source/test/Spec 수정, 새 runtime probe 또는 독립 재검토를 포함하지 않는다.

## Audit Coverage

| Report | Subdomains | Full-body files |
| --- | --- | ---: |
| [Core](core.md) | contracts, metadata, profiling, detection, impact, remediation 및 support | 19 |
| [Recovery](recovery.md) | approval/backfill, schema candidate/executor, runtime evidence | 4 |
| [Evaluation](evaluation.md) | volume/null/schema/freshness 및 design | 5 |

Baseline의 `git ls-files tests/reliability` 28개와 각 보고서의 file row가 일대일 대응한다. 24개 test module·fixture 1개·design 1개·읽기 전용 package marker 2개다. 수정은 5개 test module에 한정하며 사례 수는 258 → 268이다.

## Historical Finding Disposition

| Historical ID | Current disposition | Evidence |
| --- | --- | --- |
| R1 / L1 | `obsolete` | #266의 cleanup 이후 mutation evidence 회귀를 현재 실행으로 확인 |
| R2 / L2 | `obsolete` | #267의 profile population 정렬·거부·replay 회귀를 현재 실행으로 확인 |
| I1 / L3 | `obsolete` | #268의 invalid container와 valid-empty 구분 회귀를 현재 실행으로 확인 |
| R3 / L4 | `accepted`, fixed | Replacement 진입 차단과 실제 after-state/profile을 기존 schema replay 테스트에 추가 |
| E1 / L5 | `obsolete` | #265의 schema failure Action FAIL·count/rate·Markdown 회귀를 현재 실행으로 확인 |
| E2 / L6 | `accepted`, fixed | 다중 incident/action의 부분 충족·완전 충족을 property/count/rate/literal Markdown으로 구분 |

그 밖의 historical 본문 관찰과 cross-reference는 각 보고서에서 개별 판정했다. 신규 보강 T1–T4와 빈 목록 집계 E3도 현재 정상 구현의 test gap이며 source 결함으로 세지 않는다.

## Negative Controls

처음 10개 control은 정상 기준 테스트를 먼저 통과시킨 뒤 잘못된 동작을 메모리에서만 치환하고 새 oracle의 assertion 실패를 확인했다. 독립 리뷰 뒤 table-MAX 반례를 추가로 확인했다. Production 파일이나 영구 mutant harness를 수정·추가하지 않았다.

| Wrong behavior | Existing oracle | Strengthened oracle |
| --- | --- | --- |
| Asset 동등성 검사 생략 | 기존 partition 거부 PASS | asset 반례 FAIL, partition 반례 PASS |
| Nonempty unavailable freshness에 observed_at fallback | 기존 empty 반례 PASS | all-NULL·미지정 column FAIL, empty PASS |
| Schema hash가 이름만 사용 | 기존 column 추가 PASS | type 변경 FAIL, 다른 2개 PASS |
| Schema hash가 타입만 사용 | 기존 column 추가 PASS | rename FAIL, 다른 2개 PASS |
| Rejected metadata 검사 생략 | 기존 approved/pending 2개 PASS | 거부자/시각 누락 3개 FAIL |
| Rejected 상태의 실행 허용 | 기존 approved/pending 2개 PASS | rejected gate FAIL |
| Schema replacement 후 replay label 반환 | 기존 state/label PASS, 실제 replacement 1회 | replacement 진입 guard FAIL |
| Detection all을 any로 변경 | 기존 singleton PASS | 부분 detection property FAIL |
| Action all을 any로 변경 | 기존 singleton PASS | 부분 action property FAIL |
| Empty rate를 1.0으로 변경 | 기존 singleton PASS | empty rate FAIL |
| Partition MAX가 없으면 table MAX로 대체 | 첫 수정 `a85cac28`의 9개 profile 사례 모두 PASS; 원래 baseline empty는 FAIL | fixture 보정 후 empty/all-NULL FAIL, 나머지 7개 PASS |

의도한 pytest exit `1`은 각 driver가 assertion 실패로 확인했다. Import/collection/fixture 실패를 검출력으로 세지 않았다. Source semantics 전체에 대한 mutation coverage 수치로 일반화하지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 최신 main 통합 | `b16ad573`가 `ea39a4fd`를 포함하며 merge conflict 없음 |
| ✅ Pass | 독립 실행 환경 | PR worktree의 `uv sync --locked`, Python 3.13.13 |
| ✅ Pass | Baseline domain | `uv run --no-sync pytest tests/reliability -q`: 258 passed in 52.43s |
| ✅ Pass | Focused tests | Core 42, recovery 79, evaluation 77 passed. 상세 command는 각 보고서 |
| ✅ Pass | Final domain | 첫 수정 268 passed in 22.97s; 독립 리뷰 후 fixture 보정에서도 268 passed in 25.69s. Tach skip 미사용 |
| ✅ Pass | Negative controls | 처음 10종의 기존 PASS/보강 FAIL 및 추가 table-MAX 반례 검출 확인 |
| ✅ Pass | Python static checks | `ruff check tests/reliability`, `ruff format --check tests/reliability` (28 files), `ty check tests/reliability` |
| ✅ Pass | 최초 delivery Inbox validation | `22660aba` 전달 당시 rumdl·Inbox structure·YAML frontmatter 16개, local link 70개, diff check. 이번 정리의 검사는 별도로 수행 |
| ✅ Pass | Git 환경 격리 후 push hook | `a85cac28`에서 testmon 선택 166 passed, 1 skipped in 95.30s; Ruff 통과. 전체 suite 성공으로 일반화하지 않음 |
| ✅ Pass | 최종 독립 리뷰 | `e772c53f`의 quality/adversarial 재검토를 lead가 `clear`로 조정. [첫 판정과 보정 이력](independent.md) 보존 |
| ✅ Pass | Code revision CI | [CI Lite 40208484838](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40208484838), merge `4f0042d707fc0afcb9f92653933e0e691e5ea5dd` (parents `ea39a4fd`/`e772c53f`), `TARGETS=tests/reliability`, 268 passed in 21.10s 및 Ruff/ty 실행 log 확인 |
| ✅ Pass | 수정 후 push hook | `e772c53f`의 testmon 선택 3 passed in 4.59s, Ruff 통과. Local domain 268개 실행과 별개의 선택 cache 결과 |
| ✅ Pass | 동기화 head의 원격 CI | [CI Lite 40388153792](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40388153792), merge `bdac1b5945c35ae5182a45108378a802757e974e` (base `ea39a4fd` + head `3faa7ffb`), `TARGETS/TYPE_TARGETS=tests/reliability`, **268 passed in 25.36s**, Ruff/format/ty 실제 log 확인 |
| ✅ Pass | 코드 불변·GitHub feedback | `22660aba..3faa7ffb` 변경은 심층 리뷰 한 파일뿐. Formal review·conversation·inline thread 각각 0개 확인 |
| ✅ Pass | 이번 정리의 문서 검증 | PR 소유 Markdown/Inbox/YAML 17개, 변경 문서 local link 69개 목적지 존재, diff check. Test/source/Spec 및 실행 설정의 두 기준 revision 대비 불변 확인 |
| ⚪ Not Verified | 이번 정리의 새 runtime·독립 검토 | 로컬 pytest·추가 mutant·원본 renderer·새 독립 specialist는 실행하지 않음. 이전 실행 근거와 구분 |

## PR 277 Handoff

**Ownership correction:** [#277 plan at `74ac659d`](https://github.com/mols3131d/hmda-data-reliability/blob/74ac659d084fadd5e93900b132ef5b995ef8d919/inbox/github-277-audit-cross-domain-design/00-plan-cross-domain-tests.md)은 `openspec/**`, `lefthook.yml`, Git helper/fixture를 exclusive writable 목록에 포함하지 않는다. 따라서 H1/H2/H4 수정이 이미 #277의 권한이라는 기존 표현을 정정한다. 일반 handoff 문구와 exclusive write 범위의 모순은 owner 배정 또는 명시적인 계획 개정으로 해소해야 한다.

- **H1 — Reliability source/Spec owner:** [Manifest node/edge shape](core.md#h1-deferred-manifest-node-and-edge-policy)의 거부/허용 정책을 결정한 뒤 필요한 수정 범위를 정한다. #277은 합의된 계약의 실제 접점 검증만 취합한다.
- **H2 — Spec owner:** [Evaluation Spec](../../../openspec/specs/reliability-evaluation-report/spec.md)의 `Existing or aliased evaluation database` scenario에 `THEN`이 없다. 기존 무변경 거부 테스트는 보존하며, 정본 보완은 승인된 Spec 작업에서 수행한다. #277이 현재 범위에서 Spec을 수정할 수 있다고 가정하지 않는다.
- **H3 — #277:** 예약된 operations/lifecycle→recovery/evaluation 접점과 results-only projection, partition replay no-write, cleanup failure 전달을 최종 통합 상태에서 대조·실행한다. Domain-selected CI나 이전 push hook 결과를 전체 통합 계약의 입증으로 승격하지 않는다.
- **H4 — Shared tooling owner pending:** 실제 Git hook 환경 오염은 #270 F3와 같은 원인이다. 최초 push 중단, private ref/index 복원과 98개 파일 동일성 확인, 임시 `uv` wrapper의 Git-local 환경 제거 후 전달 성공은 기존 incident 근거로 보존한다. 영구 수정은 별도 공용 도구 작업이나 명시적으로 변경한 #277 범위에서만 수행한다. Parent ref/index/config 불변과 child Git fixture 격리를 독립 oracle로 검증해야 하며, 임시 wrapper 성공을 영구 수리로 해석하지 않는다.

## Completion Boundary

로컬 deterministic Reliability 검증이다. Cross-domain 최종 통합, 모든 filesystem 장애 조합, live provider·사람의 승인/효용은 증명하지 않는다. 이 lane에서 새 production defect를 확정하지 않았으며 보류 항목을 실패한 테스트의 우회로 사용하지 않았다. Draft 해제·approval·merge는 별도 인간 결정이다.
