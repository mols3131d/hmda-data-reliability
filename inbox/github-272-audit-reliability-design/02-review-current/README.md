---
type: review
title: Current Reliability Test Design Audit
description: PR 272의 현행 테스트 전수 검토, 과거 finding 재판정과 회귀 보강 근거를 연결합니다.
---

# Current Reliability Test Design Audit

**State:** 28/28 전수 조사와 test-only 회귀 보강 완료, 독립 리뷰 대기. 인간 승인을 뜻하지 않는다.

- **Baseline:** `b16ad5734b4a5a35c1db3d12fe03124438e71348` (원격 PR head `7a93a60c8b345dadc401968e2100ba19a395fd52` + main `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`).
- **Scope:** Reliability 소유의 tracked test/support/design 28개 전체. Production·Spec은 계약 대조를 위해 읽으며 수정하지 않는다.
- **Historical evidence:** [과거 보고서](../01-review-historical/README.md)의 조사 revision은 `3ab899100fc0b35e23d464bd761f3b144a978ae7`이고 반입 기준은 PR #258 `bdce0f4e`다. 현재 결함으로 자동 승격하지 않는다.
- **Next:** 현재 test diff와 이 검토 근거를 별도 `review-lead`에 전달하고, 결과를 수용 범위에 대조한 뒤 Draft PR로 전달한다.

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

각 process는 정상 기준 테스트를 먼저 통과시켰다. 잘못된 동작을 메모리에서만 치환하고 새 oracle의 observable assertion 실패를 확인했다. Production 파일이나 영구 mutant harness를 수정·추가하지 않았다.

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

의도한 pytest exit `1`은 각 driver가 assertion 실패로 확인했다. Import/collection/fixture 실패를 검출력으로 세지 않았다. Source semantics 전체에 대한 mutation coverage 수치로 일반화하지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 최신 main 통합 | `b16ad573`가 `ea39a4fd`를 포함하며 merge conflict 없음 |
| ✅ Pass | 독립 실행 환경 | PR worktree의 `uv sync --locked`, Python 3.13.13 |
| ✅ Pass | Baseline domain | `uv run --no-sync pytest tests/reliability -q`: 258 passed in 52.43s |
| ✅ Pass | Focused tests | Core 42, recovery 79, evaluation 77 passed. 상세 command는 각 보고서 |
| ✅ Pass | Final domain | 같은 command로 보강 후 268 passed in 22.97s, Tach skip 미사용 |
| ✅ Pass | Negative controls | 위 잘못된 동작 10종에서 기존 PASS / 보강 FAIL |
| ✅ Pass | Python static checks | `ruff check tests/reliability`, `ruff format --check tests/reliability` (28 files), `ty check tests/reliability` |
| ⚪ Not Verified | 독립 리뷰·원격 CI | 별도 확인 후 갱신. 인계 당시 Inbox-only CI 성공을 테스트 성공 근거로 사용하지 않음 |

## PR 277 Handoff

- **H1:** [Manifest node/edge shape](core.md#h1-deferred-manifest-node-and-edge-policy)의 거부/허용 정책을 결정하고 필요 시 Spec·source·회귀를 함께 수정한다. 확인된 parser 동작과 미정 계약을 구분한다.
- **H2:** [Evaluation Spec](../../../openspec/specs/reliability-evaluation-report/spec.md)의 `Existing or aliased evaluation database` scenario에 `THEN`이 없다. 기존 preflight 안전 계약과 source를 대조해 정본 문구를 보완한다. 여기서는 Spec을 수정하지 않았다.
- **H3:** 예약된 operations/lifecycle→recovery/evaluation 접점과 results-only projection, partition replay no-write, cleanup failure 전달을 최종 통합 상태에서 대조·실행한다. 외부 E2E는 targeted read-only 대조했으며 이 PR에서 실행하지 않았다.

## Completion Boundary

로컬 deterministic Reliability 검증이다. Cross-domain 최종 통합, 모든 filesystem 장애 조합, live provider·사람의 승인/효용은 증명하지 않는다. 이 lane에서 새 production defect를 확정하지 않았으며 보류 항목을 실패한 테스트의 우회로 사용하지 않았다. Draft 해제·approval·merge는 별도 인간 결정이다.
