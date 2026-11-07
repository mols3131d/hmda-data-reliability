---
type: report
title: "Reliability Agentic Refactoring Progress and Remaining Work"
description: "PR #284의 bounded 조사·위임 구현, 최종 회귀·독립 확인, 실제 모델 비교와 사람 평가·전달 인계를 정리한다."
tags:
  - reliability
  - ai-engineering
  - testing
  - refactoring
---

# Reliability Agentic Refactoring Progress and Remaining Work

## Summary

**제한된 실제 조회·조사·위임 보고, native Prompt·관측·Dataset 연결과 정본 이전을 구현했고, 최종 전체 회귀는 1,179 passed / 1 skipped다. 사람의 품질 평가와 전달 판단은 남아 있다.** 실제 비교는 baseline 2/3 완료, 후보 1/3 완료였으므로 후보를 채택하지 않았고 production은 v1을 유지한다.

이 문서는 2026-11-08 Asia/Seoul의 로컬 작업 트리를 기준으로 갱신한 **비정본 실행 근거와 인계 보고서**다. 사용자의 구현 계속 승인에 따라 기존 Change를 적용했으며, 아래 푸시 이력과 이후 미커밋 구현을 구별한다. 요구사항의 owner는 OpenSpec이며 이 보고서가 품질 채택이나 PR 승인을 대신하지 않는다.

| Item | Verified State |
| --- | --- |
| PR | [#284: refactor: evolve reliability into agentic domains](https://github.com/mols3131d/hmda-data-reliability/pull/284), Open / Draft |
| Owning branch | `agent/refactor/evolve-reliability-agentic-architecture` |
| Head | `1b0bd473e1f0e6c8318974e4b150aeb50968c959` |
| Base | `57cd2bd49aa380273f677719c6b2aa68f49641ee` |
| Delivery | 위 head 이후 구현·테스트·문서 변경은 로컬 미커밋·미푸시다. 이번 continuation에서 commit·push·PR 상태 변경을 하지 않았다. |
| Remote CI basis | [CI Lite 실행 42351058184](https://github.com/mols3131d/hmda-data-reliability/actions/runs/42351058184)은 위 head의 과거 성공이다. 현재 dirty 변경의 원격 CI로 재사용하지 않는다. |
| Implementation tracking | 진행 집계는 [Migration Tasks](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/tasks.md)가 소유한다. 1~5의 구현·회귀를 닫았고 6~7의 실험·통합 근거도 아래에 확보했다. |
| Exact source state | `src`·`tests`의 `.py`·`.md`·`.json` 221개에서 상대 경로·NUL·파일 bytes·NUL을 정렬 결합한 SHA256은 `7821c600dd6bbbb1e9b2ebfafd3150b2d4343f66fe4e463322635f9cda80552a`다. `__pycache__`는 제외한다. |
| Assessment | 독립 리뷰의 확정된 현재 범위 결함을 보완하고 재확인했다. 구현 근거와 모델 품질·사람 승인·원격 전달 완료는 분리한다. |

## Goal and Preserved Boundaries

전체 목표는 결정론적 Reliability를 유지하면서, 고정된 LLM 텍스트 검토를 **제한된 실제 조회·동적 조사·위임 작업·근거 기반 보고**로 전환하는 것이다. 파일 재배치나 테스트 통과만으로 완료하지 않는다. 원래 목표와 완료 기준은 [01 Complete Implementation Plan](01-plan-reliability-agentic-complete-refactor.md)이 기록한다.

- `reliability.assessment`는 프로파일·탐지·quality gate·impact 등 결정론적 판단을 소유한다.
- `reliability.remediation`은 초안·외부 승인 기반 Recovery·재검증을 소유한다.
- `reliability_ai.investigation`은 읽기 전용 근거 조회와 가설·불확실성 보고를 소유한다.
- `reliability_ai.execution`은 위임 범위·예산 안의 실행 조합과 결과 보고를 소유한다. AI의 제안이나 상위 모델의 Task는 Recovery 승인을 대신하지 않는다.
- `runtime_ai`는 provider-neutral 전송·도구 호출 계약·오류·예산을 소유하며 업무 승인 정책을 소유하지 않는다.

현재 입력 계약은 `null_spike` 사례를 대상으로 한다. 임의 SQL·DB 쓰기·Airflow 제어의 모델 직접 노출, AI 쓰기 권한 확대, 과거 Prompt·실행 기록 재작성은 이번 작업의 완료 조건이 아니다. LangChain·LangGraph·Deep Agents 전체 도입이나 멀티에이전트 확대도 필수가 아니다.

## Work History

| Phase | Work and Outcome | Evidence |
| --- | --- | --- |
| 조사·계획, 2026-11-05 | 기존 소스·계약·책임 경계를 조사하고 전체 구현 목표와 후속 작업을 문서화했다. 이 시점은 구현 전 Draft였다. | [00 Research](00-research-reliability-agentic-boundary-audit.md), [01 Plan](01-plan-reliability-agentic-complete-refactor.md), [02 Brief](02-brief-reliability-agentic-work-handoff.md) |
| 기준 통합 | 개발환경·도구 변경이 반영된 main을 작업 브랜치에 통합했다. 다른 PR의 개발 도구 변경을 #284 제품 기능으로 집계하지 않는다. | `c3ac46ad`, base `57cd2bd4` |
| 핵심 구현, 2026-11-07 | Reliability 물리 구조, `reliability_ai`, provider 도구 호출과 조사·실행 서비스를 구현했다. 최초 인계는 W1~W4 완료를 주장했지만 후속 검토에서 이를 그대로 승인하지 않았다. | `0b2ac8c8`, [03 Handoff](03-report-reliability-agentic-refactor-handoff.md) |
| 검토·결함 보완 | 최초 결함 F1~F6과 재검토 중 확인한 관련 문제를 교정하고 회귀 테스트와 독립 재리뷰를 수행했다. | [04 Review and Remediation](04-review-reliability-agentic-remediation.md) |
| 조회 연동·전환 계획 | 사건 snapshot profile과 trusted dbt artifact 조회를 연결했다. 기존 정본과 구현의 차이를 해소할 OpenSpec proposal·design·delta spec 2개·tasks를 작성했다. | `1b0bd473`, [Migration Proposal](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/proposal.md) |
| 전달 | 서명된 최신 커밋을 포함한 로컬 변경을 일반 push로 전달했고 pre-push 검사 및 원격 CI 성공을 확인했다. | head `1b0bd473`, 위 CI 실행 |

## Implemented Work

### Deterministic Reliability and Runtime

프로파일·metadata·탐지·impact·quality gate를 assessment 아래로, Recovery 구현을 remediation 아래로 정리하고 import와 공개 export를 이전했다. 고정 `triage → rca → plan` LangGraph 조합은 결정론적 함수 파이프라인으로 단순화했다. 기존 authoritative Recovery·Approval의 의미를 유지하는 방향이며, 관련 회귀 검증은 아래처럼 실행 시점별로 구분한다.

`review_ai`의 소스·테스트·평가 자산은 `reliability_ai`로 이전했다. 호환 wrapper나 옛 설정 alias는 복원하지 않았다. 현재 Architecture·domain map·개발/Prompt/평가 guide와 consumer를 이전하고 두 canonical Spec의 Purpose·Requirement를 동기화했다. 과거 실행·Inbox 기록과 기존 Spec ID는 보존했다.

`runtime_ai`에는 도구 정의·호출 계약, `tool` 메시지와 응답 정규화, OpenAI-compatible SDK의 `tools`·`tool_choice` 전달을 추가했다. 업무별 도구 허용·승인 판단은 이 전송 계층으로 옮기지 않았다.

### Investigation and Delegated Execution

[Investigation service](../../src/hmda_reliability/reliability_ai/investigation/service.py)는 제한된 도구 선택·호출과 후속 모델 호출을 조합하고 findings·hypotheses·uncertainties·도구·turn 기록을 반환한다. Task/caller의 허용 도구와 더 좁은 예산을 적용하고, 중복 호출·호출 수·누적 prompt 크기·새 호출 시작 시 deadline을 검사한다. 진행 중인 동기 호출을 강제로 취소하는 기능까지 입증한 것은 아니다.

[Tool registry](../../src/hmda_reliability/reliability_ai/investigation/tools.py)의 현재 조회 연결은 다음과 같다.

| Tool | Current Behavior | Remaining Limit |
| --- | --- | --- |
| `get_incident_evidence` | 초기 입력과 같은 공유 projection에서 필드별 metadata shape·크기·민감 key·개인 경로를 제한한다. 전체 도구 결과에도 정제를 적용한다. | 임의 payload·raw row·범용 파일 읽기를 제공하지 않는다. |
| `compare_profiles` | 깊게 복제한 사건 profile의 실제 수치·Evidence·시각·가용 snapshot ID를 보존한다. 다른 column과 과대 snapshot reference를 거부한다. | live DB 재프로파일링이 아니다. |
| `inspect_dbt_impact` | trusted pair만 동일 shared lock 안의 hash·기존 impact API로 읽는다. Current projection과 실제 downstream을 반환한다. | 과거 snapshot이 아니며 빈 downstream은 `unresolved_or_leaf`다. 실제 운영 dbt 실행이나 모델 경로 선택을 하지 않는다. |

[Execution service](../../src/hmda_reliability/reliability_ai/execution/service.py)는 Task·ActionProposal·ExecutionReceipt·ReportEnvelope로 조사와 승인된 도메인 실행을 조합한다. 사건·대상·partition·snapshot reference 충돌, 복수 요청과 허용 action을 조사 전에 검증한다. Task/caller의 도구 교집합·최소 예산을 적용하고, 조사 실패 뒤 mutation을 시작하지 않는다. 별도 외부 승인 요청만 기존 authoritative executor로 전달하며 Task·승인·proposal·실제 mutation/reconciliation을 보고에 보존한다.

Prompt는 invocation 시작에 읽은 native 객체·실제 version을 고정하고 매 turn 같은 canonical input·history를 compile한다. Provider raw는 파싱·원격 output 전에 보존하며 core manifest가 성공해야 완료를 보고한다. 알려진 미완료 종료·필수 배열 누락·과대 context·저장 실패·최종 core 처리의 예산 만료는 실패로 남는다. 관측 장애는 별도 bounded record에 기록하고 모델을 다시 호출하지 않는다.

### Review Remediation

| ID | Original Problem | Completed Remediation |
| --- | --- | --- |
| F1 | 미설정 도구가 조회 없이 고정 성공 결과를 생성했다. | 미연결 도구의 비노출·실행 차단, 허용 목록과 엄격한 인자 검증을 적용했다. 실제 profile/dbt 연결은 이 보완 뒤 추가했다. |
| F2 | Task의 허용 도구·호출 수·시간 제한이 적용되지 않았다. | Task/caller의 교집합·최소 예산을 조사 실행에 전달했다. |
| F3 | batch 도구 호출·누적 prompt·deadline 경계에서 예산을 넘었다. | 개별 dispatch 및 provider 시작 직전의 잔여 예산을 재검사하고 한도 뒤 추가 호출을 차단했다. |
| F4 | 조사 실패가 완료로 보이거나 Recovery 변경·재개 정보가 소실됐다. | 조사 실패 시 실행 중단, 실제 도메인 결과·proposal 참조·mutation/reconciliation 보존과 상태 구분을 추가했다. |
| F5 | 원문 저장 실패·동일 ID 충돌·중첩 JSON 오류가 숨겨졌다. | UUID 실행 identity, raw-before-parse 저장, turn·manifest 연결, 명시적 오류와 JSON-safe fallback을 추가했다. |
| F6 | Dataset output에 조사 내용이 빠지고 SDK 예외 항목 누락을 성공으로 처리했다. | 전체 조사 결과를 보존하고 입력·결과의 항목 ID multiset을 대조해 누락·중복·실패를 성공으로 보고하지 않도록 했다. |

독립 재리뷰의 `clear`는 **04 문서가 식별한 F1~F6 보완 당시 상태**에 한정된다. 그 뒤 추가한 실제 조회 연동과 현재 head 전체가 독립 리뷰를 통과했다는 의미로 확대하지 않는다. 검토 반복과 재현 근거는 04에 보존하며 이 보고서에서 다시 정의하지 않는다.

### Migration Planning and Delivery

[Bounded Investigation Migration](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/proposal.md)의 두 delta를 canonical Spec에 의미 병합하고 Purpose를 갱신했다. Native 사람 평가·baseline 비교와 언어 준수 평가 요구는 유지했다. 구조 검증과 Markdown 검사를 통과했으며 Change는 archive하지 않았다. 선행 구현을 사후 test-first로 집계하지 않고 이번 결함은 실제 RED→focused GREEN과 연결 회귀로 구분했다.

커밋·푸시 중 발생한 로컬 SSH 문제는 기존 systemd agent 연결 및 키 등록으로 해결했다. 동일 키의 agent 기반 서명을 유지한 채 push했으며, 키 암호 제거·훅 우회·force-push·Git history 재작성은 하지 않았다. 이는 개발환경 전달 장애 해결이지 제품의 새 기능은 아니다.

## Verification Evidence

| State Basis | Check | Result and Limit |
| --- | --- | --- |
| 최초 구현 `0b2ac8c8` | AI/runtime 131개와 관련 deterministic·operations·orchestration·CI/Tach 597개 | 합계 728개 통과. 이후 보완을 포함한 최신 head 전체 결과로 사용하지 않는다. |
| 결함 보완 중간 상태 | 관련 회귀 집합 | 750개, 이후 754개 통과 기록이 있다. 그 뒤에도 코드가 바뀌었으므로 최종 full suite로 표현하지 않는다. |
| F1~F6 최종 보완 상태 | AI/runtime 및 정적 검사·독립 재리뷰 | 172개 통과, Ruff·type·Tach·source/test/script format 통과. 독립 리뷰 범위는 위에서 제한한 상태다. |
| 실제 조회 연동 후 | investigation tools/agent와 execution focused 검사 | 50개 통과. live provider나 실제 운영 DB의 검증은 아니다. |
| 푸시한 head `1b0bd473` | native pre-push `pytest --testmon --testmon-forceselect` | 485 passed, 105 deselected. 전체 non-resource suite 실행으로 해석하지 않는다. |
| 같은 push | OpenSpec 전체 strict 구조 검사, Ruff, JSON, TOML | OpenSpec 33항목 통과. Python 46파일 lint/format 및 JSON 2파일·TOML 1파일 검사 통과. Spec 통과는 구현 의미 일치를 증명하지 않는다. |
| 같은 PR head/base | 원격 CI Lite | 성공. 실행 head는 `1b0bd473`, 조회한 PR base는 `57cd2bd4`다. 이 보고서는 CI의 개별 테스트 수를 새로 집계하지 않는다. |
| 최종 dirty source state | 전체 non-resource suite | `env TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" uv run --no-sync pytest -n auto -q --tb=short --junitxml=.local/artifacts/pytest-pr284-final.xml`: 1,179 passed / 1 skipped, XML time 109.301s. Skip은 Windows npm/Node 경계 전용이다. |
| 같은 최종 source state | AI/runtime·정적·배포 | 213 passed / 3.73s. Project-wide `ty check`, Ruff check, source/test/script format 236파일, Tach 통과. Wheel 재빌드 및 실제 setup의 Prompt 5개·Dataset seed 1개 포함 확인. |
| 같은 최종 source state | 독립 확인 | 두 관점의 별도 reviewer가 반복 검토했고 확정된 현재 범위 결함은 수정·재확인했다. 마지막 exact fingerprint에서 접두 file URI 회귀 3 passed를 독립 확인했다. |
| 정본·guide | Spec·Markdown·index | 전체 canonical Spec 19개와 active Change 검증 통과. Mermaid 두 diagram validator·로컬 preview 완료. Native docs index 생성·check 완료. 최종 기록 변경은 별도 문서 검증한다. |
| 실제 원격 실행 | baseline/candidate 및 v1 후속 run | 아래 run·trace 조회로 SDK 반환과 원격 적재를 구분했다. 사람 평가는 미평가다. |

첫 전체 실행의 EDA Git fixture 4건은 상대 `TMPDIR/TMP/TEMP=./.tmp`가 임시 cwd에서 해석돼 실패했다. 검증 invocation에만 절대 경로를 전달해 isolated 4건과 전체 suite를 통과시켰다. 실제 Git 서명 설정·테스트 assertion은 바꾸지 않았다. Build의 uv cache 위치와 uv/uv-build version range 경고는 남지만 wheel 빌드는 성공했다.

## Live Comparison Evidence

세 실행은 Dataset `hmda-reliability-ai-v1`의 같은 version `2026-11-07T12:58:25+00:00`과 세 사례를 사용했다. Project는 `cmuqox6on01i6ad0dc8ocxzam`, Dataset ID는 `cmw6erzxb0100ad0gt04gd8v5`다. 실제 model은 `qwen3.5:4b-16k-local`, temperature 0·output 4096 tokens·tool 상한 5·workflow 300s·prompt cap 65,536bytes·retry 0이다.

| Run | Actual Result | Native Link |
| --- | --- | --- |
| `pr284-baseline-16k-20261107`, Prompt v1 | 2 completed / 1 `invalid_investigation_output`. 9 generations·6 도구 모두 성공. Prompt/completion tokens 합계 21,525 / 5,527. | [baseline](https://jp.cloud.langfuse.com/project/cmuqox6on01i6ad0dc8ocxzam/datasets/cmw6erzxb0100ad0gt04gd8v5/runs/9e4c068c-5250-4aca-910c-b649ed9d854c) |
| `pr284-candidate-16k-20261107`, Prompt v2 | 1 completed / 2 `duplicate_tool_call_cycle`. 13 generations·10 실행 도구 모두 성공. Tokens 34,084 / 6,107. | [candidate](https://jp.cloud.langfuse.com/project/cmuqox6on01i6ad0dc8ocxzam/datasets/cmw6erzxb0100ad0gt04gd8v5/runs/0714631d-06f5-4694-8a48-fda0b8723fd2) |
| `pr284-post-review-v1-16k-20261107`, Prompt v1 | 2 completed / 1 `invalid_investigation_output`. 9 generations·6 도구 모두 성공. 원격 항목과 세 trace의 상태를 재조회했다. | [v1 regression](https://jp.cloud.langfuse.com/project/cmuqox6on01i6ad0dc8ocxzam/datasets/cmw6erzxb0100ad0gt04gd8v5/runs/67e166bd-264d-49f1-97e0-0c92e987230e) |

Baseline의 zero-baseline 사례는 최종 본문이 0bytes이며 `finish_reason=stop`이었다. 후보는 최종 JSON 본문을 강조하는 지시를 시험했지만 반복 도구 순환이 늘어 악화됐으므로 채택하지 않았다. Repository seed의 강화 문구도 되돌렸으며 영어 heading 차이는 있다. Production은 v1, candidate는 v2로 분리했다. 자동 추가 튜닝·생성 재시도·Score Config·Queue·사람 점수 생성은 하지 않았다.

기존 12개 `hmda-review-ai` Prompt inventory를 읽고 새 이름으로 명시적 setup을 한 번 수행했다. 이후 후보는 investigation component/chat v2만 발행했다. 세 run의 실제 revision은 `1b0bd473e1f0e6c8318974e4b150aeb50968c959-dirty`다. 이 문자열은 exact content identity가 아니며 이후 privacy·context·최종 예산 보완 전 실행이다. 최종 fingerprint의 품질 검증으로 소급 주장하지 않는다.

Model ID `51cd52990b56`는 Qwen35 4.2B Q4_K_M 기반이며 실제 `num_ctx=16384`, Ollama resident 3.6GB·100% GPU offload를 확인했다. RTX 3070 8,192MiB에서 실행 전 3,326MiB, 후보 뒤 7,415MiB를 관찰했지만 peak 측정은 아니다. Model capability에 thinking이 있고 명시적 override는 없으나 실제 default thinking은 확인하지 못했다. 상속 sampling 설정과 별개로 Runtime은 temperature 0을 적용했다. 32K는 필요성과 여유 근거가 없어 시험하지 않았다.

Baseline generation 지연은 약 3.34~82.31s, 후보는 2.78~20.06s였다. Baseline 첫 호출의 cold 상태와 후보의 warm 상태가 달라 속도 개선으로 해석하지 않는다. 각 turn의 실제 usage·지연·digest·원문·도구 결과는 local manifest에 보존했다. 첫 두 run의 여섯 trace와 후속 run의 세 trace를 CLI로 재조회해 Prompt version·model·usage·IO·agent 아래 sibling generation/tool·실패 상태를 대조했다. 후속 trace ID는 `02cf7e7d3860250cee43f3da7aebca88`, `2f44b65a6d29fde737c01d5a39473822`, `2f78aafe474d32a6196ed7f03edf0787`다.

**사람의 다섯 기준 평가·한국어 준수·품질 채택은 미평가다.** SDK 반환·완료 수·원격 audit은 독립적인 사람 평가가 아니다. 실패한 후보와 baseline의 빈 최종 본문을 포함해 [기존 rubric](../../docs/development/review-ai-evaluation.md#human-evaluation)으로 사람이 판단해야 한다.

## Development Collaboration Evidence

이번 구현은 하나의 coding agent가 순차 수행했고, 독립 reviewer만 두 관점으로 병렬 실행했다. 병렬 구현 agent 간 branch 통합이나 생산성 비교 실험은 하지 않았다. 모델명·탐색/조정/재작업 wall-time의 비교 가능한 계측도 없어 비용 감소 수치를 주장하지 않는다. 제품 Task/supervisor 계약은 개발 협업의 실증으로 집계하지 않는다.

| Representative Change | Owner And Shared Contract | Actual Integration Evidence |
| --- | --- | --- |
| 초기 자료·Evidence·dbt 조회 | `context.py`의 자료 정책을 registry·prompt·service가 소비한다. `AgenticReviewInput`과 deterministic Evidence 의미는 유지했다. | 같은 raw-row/경로 회귀가 canonical·실제 tool·remote를 검사한다. 실제 dbt pair 결과가 후속 provider 메시지와 local-only 경로 manifest에 연결된다. |
| Task·Recovery 조합 | execution preflight와 report가 wrapper 의미를, 기존 `reliability`가 Approval·mutation·reconciliation을 소유한다. | 다른 사건·대상·partition·snapshot·복수 요청은 실행 전 차단. 실제 임시 DuckDB의 승인 대기·성공·닫힌 backend 오류가 Task·Evidence·승인·proposal 영수증과 일치한다. |
| Prompt·관측·저장 | 같은 investigation service를 바꾸므로 순차 통합했다. Native Prompt 객체·Runtime 응답·create-only store 계약을 공유했다. | 실제 SDK exporter로 version·history·parent·raw-before-output을 검증한다. Parse·직렬화·fsync 중 만료가 budget 실패와 manifest로 남는다. |
| 실행 생산자→Dataset 소비자 | `InvestigationResult`와 failure code가 인계 계약이다. Runner는 공통 조사만 호출한다. | 결과 전체·Counter 완전성·실패 exit·합성 표식 preflight를 검증한다. 반복 실행은 Prompt·Dataset·평가 자산을 생성하지 않는다. |

텍스트 merge 충돌은 이 순차 작업에서 관찰하지 않았다. 의미적 통합 오류·재작업은 관찰했다. 최초 공유 allowlist가 nested metadata shape를 제한하지 못해 raw row가 남았고, 도구의 provenance path가 초기 정제를 우회했다. `{}`를 완료 처리하던 가정은 Dataset 성공·위임 실행과 충돌했다. 합성 관측을 끄더라도 native SDK의 task output이 기록되는 별도 경로가 있었다. Context의 per-item/identity validation과 최종 처리 deadline도 wrapper 실패 계약과 어긋났다. 원인을 소유하는 projection·runner·service·store와 기존 테스트를 보완했으며 하위 Recovery 정책을 중복 구현하지 않았다.

독립 리뷰는 총 다섯 substantive 회차에서 확정 후보를 검증·수정·재확인했다. 마지막 정확한 source fingerprint에서 기존 POSIX·bare/prefixed file URI 세 회귀를 독립 확인했고 미해결 `current_required`는 없다. 삭제 자체가 실패하는 추가 저장 이중 장애에서는 완료 파일이 남을 가능성이 정적으로 제기됐지만 실행 재현·변경 귀속은 미확인이다. 이 경우 caller 결과는 저장 실패와 null manifest로 차단되므로 정상 완료로 판정하지 않았다. 이것과 모든 하위 Recovery 오류의 mutation state 보장을 현재 해결 완료로 확대하지 않는다.

## Human Handoff

자동화 가능한 구현과 통합 근거는 확보했다. 다음 사람이 필요한 행동은 두 가지다.

1. Native compare에서 세 run의 실패를 포함해 다섯 기준과 한국어 출력·검토 가치를 평가하고, 현 v1 유지 또는 별도 model/Prompt 실험 방향을 결정한다. 후보 v2 채택은 권장하지 않는다. 최종 privacy 보완 후 exact revision 평가가 필요하면 별도 run으로 기록하며 기존 비교를 다시 쓰지 않는다.
1. 로컬 diff를 검토해 commit·push와 PR 본문 갱신을 승인하고, 새 원격 head/base의 CI 뒤 Ready/merge를 판단한다. 기존 PR 본문은 문서 전용 초기 상태였으며 이번 작업에서 변경하지 않았다. 새 branch·commit·push·Ready·merge·archive는 하지 않았다.

독립 리뷰의 `clear`는 위 exact source 상태와 확정된 현재 범위 결함의 종결에 한정한다. 사람 품질 승인이나 최신 prospective merge의 원격 CI를 대신하지 않는다. RPI는 5/30 substantive review 회차를 사용했으며 사람 평가·전달 판단으로 인계한다. 다음 진행의 정본은 [Migration Tasks](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/tasks.md)다.

## Reading Guide

- 전체 배경과 원래 완료 목표: [00 Research](00-research-reliability-agentic-boundary-audit.md), [01 Plan](01-plan-reliability-agentic-complete-refactor.md).
- 최초 구현 인계와 주장 정정: [03 Handoff](03-report-reliability-agentic-refactor-handoff.md).
- F1~F6 재현·수정·독립 리뷰의 상세 근거: [04 Review](04-review-reliability-agentic-remediation.md).
- 앞으로의 구현 기준: [Proposal](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/proposal.md), [Design](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/design.md), [Tasks](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/tasks.md).

01·03·04의 과거 상태는 해당 기록 시점의 근거다. 06·07은 continuation 이전 검토·계획이며 현재 코드와 완료 집계를 대신하지 않는다. 이후 head·base·Prompt·Dataset이나 소스가 바뀌면 대응 검증과 독립 리뷰의 freshness를 다시 확인해야 한다.
