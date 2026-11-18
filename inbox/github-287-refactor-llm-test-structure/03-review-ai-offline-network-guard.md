---
type: review
title: PR 287 Independent Review of the Offline AI Test Guard
description: "PR #287의 AI pytest 네트워크 차단, 실패 보고 및 회귀 검증을 독립적으로 검토한다."
tags:
  - testing
  - ci
---

# PR 287 Independent Review of the Offline AI Test Guard

> [!IMPORTANT]
> **Revise (`changes_required`)** — 네트워크 차단 예외를 제거해도 이번 PR의 회귀 테스트 7개가 모두 통과했다. 명시적으로 켠 pytest OTLP/HTTP 내보내기도 AI 테스트의 네트워크 호출로 기록돼 정상 테스트가 실패했다.

- **Target** — 2026-11-18 KST 기준 열린 Draft PR. GitHub 검토 제출은 0건이다. [PR #287](https://github.com/mols3131d/hmda-data-reliability/pull/287)
- **Revision** — `main` base `a326d8d9cfb8c7cc477e46b3df67c05e62d093dc`, head `7aec7be0fe8481eaec0f63bb5336b5485c1773d8`. [Prospective merge `0ab02324`](https://github.com/mols3131d/hmda-data-reliability/commit/0ab023240404fa7c0cf322462b76abec38d82c41)
- **Scope** — PR 변경 파일 6개. 독립 검토자 두 명이 AI 테스트의 setup·call·teardown, 오류를 처리한 뒤 `skip`·`xfail`하는 경우, 직접 선택, 다른 디렉터리, 모의 SDK 전송과 pytest trace 내보내기를 검토했다. [Testing Guide](../../docs/development/testing.md#reliability-ai-evaluation), [Work Status](02-brief-llm-test-structure-work-status.md)

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 Major | 차단 동작 없이 실패 보고만 남겨도 새 회귀 테스트가 통과한다. | 차단 예외 제거 시 실패하는 검증을 추가한다. |
| F2 | 🟠 Major | `--export-traces`에서 pytest의 OTLP/HTTP 전송이 정상 AI 테스트를 실패시킨다. | 명시적으로 요청한 pytest 내보내기와 AI 클라이언트 호출을 구분한다. |

## Details

### F1 · Missing Assertion for Rejected Socket Operations

`acceptance_gap` · `current_required`

#### F1 Locations

- [tests/conftest.py](https://github.com/mols3131d/hmda-data-reliability/blob/7aec7be0fe8481eaec0f63bb5336b5485c1773d8/tests/conftest.py#L27-L38)
  - `_reject_ai_network`의 시도 기록과 `OSError`
  - [`pytest_runtest_makereport`의 실패 보고](https://github.com/mols3131d/hmda-data-reliability/blob/7aec7be0fe8481eaec0f63bb5336b5485c1773d8/tests/conftest.py#L60-L75)
- [tests/test_ai_network_guard.py](https://github.com/mols3131d/hmda-data-reliability/blob/7aec7be0fe8481eaec0f63bb5336b5485c1773d8/tests/test_ai_network_guard.py#L47-L62)
  - `try_network`가 `OSError`를 처리하고 호출 반환 여부를 기록하지 않는다.
  - [바깥 테스트는 pytest 결과, 종료 코드와 메시지를 확인한다.](https://github.com/mols3131d/hmda-data-reliability/blob/7aec7be0fe8481eaec0f63bb5336b5485c1773d8/tests/test_ai_network_guard.py#L85-L94)

#### F1 Evidence

pytest 9.1.1에서 head의 두 파일을 임시 디렉터리에 복사했다. 비교용 사본에서 `raise OSError("AI tests must use offline transports")` 한 줄만 제거하고 `_NETWORK_ATTEMPTED` 기록을 유지했다. `test_ai_network_guard.py`는 원본과 비교용 사본에서 각각 `7 passed`였다. 두 독립 검토자도 같은 결과를 재현했다.

별도 pytest 항목에서 `getaddrinfo('127.0.0.1', 9, flags=AI_NUMERICHOST)`를 호출했다. 원본은 차단기의 `OSError`를 냈고 비교용 사본은 주소를 반환했다. 두 실행 모두 같은 네트워크 시도 메시지와 exit code `1`을 냈다. 숫자 주소만 사용했으며 외부 DNS나 모델에 연결하지 않았다.

#### F1 Impact

차단 코드가 빠지는 회귀가 생기면 pytest가 실패를 보고하기 전에 소켓 작업이 진행될 수 있다. 현재 회귀 테스트와 CI 결과만으로는 그 회귀를 잡을 수 없다. 저장소 테스트 기준은 각 계약을 관찰 가능한 결과에 연결하도록 요구한다. [Test Design](../../docs/development/test-design.md#choose-an-independent-oracle)

#### F1 Action

주소 조회가 차단기의 `OSError`로 중단됐을 때만 하위 실행이 남기는 결과를 바깥 테스트에서 확인한다. 하위 실행의 실패 여부만 보면 내부 `pytest.raises` assertion의 실패도 기존 검사에 통과할 수 있다. 오류를 처리하거나 `skip`·`xfail`한 뒤에도 pytest가 실패하는 기존 검증을 유지한다. 차단 예외 한 줄을 제거한 사본에서는 새 검증이 실패해야 한다.

### F2 · Pytest Trace Export Fails Offline Tests

`direct_regression` · `current_required`

#### F2 Locations

- [tests/conftest.py](https://github.com/mols3131d/hmda-data-reliability/blob/7aec7be0fe8481eaec0f63bb5336b5485c1773d8/tests/conftest.py#L27-L53)
  - `_reject_ai_network`, `pytest_runtest_protocol`
- [Testing Guide](../../docs/development/testing.md#additional-evidence)
  - `--export-traces`로 OTLP collector에 trace를 보내는 실행법

#### F2 Evidence

차단기는 프로세스의 모든 audit event를 받고, 그때 실행 중인 pytest 항목의 경로로 시도를 귀속한다. pytest-opentelemetry가 자체 배치 스레드에서 OTLP/HTTP 요청을 준비하는 동안 AI 항목이 활성화돼 있으면 주소 조회 예외와 네트워크 시도 기록이 그 항목에 남는다.

pytest-opentelemetry 1.1.0과 설치된 OTLP/HTTP exporter를 로드해 `--export-traces`로 `runtime_ai`의 샘플 테스트를 실행했다. 테스트 본문은 스레드 신호만 주고받았다. `requests.Session.post` 전송 대역이 `127.0.0.1` 주소 조회를 수행하는 시점을 테스트 실행 중으로 맞췄다. `OTEL_TRACES_EXPORTER=otlp_proto_http`와 로컬 endpoint를 지정했다. 차단기가 없는 base 조건에서는 조회 성공과 `1 passed`를 확인했다. head에서는 같은 조회에서 차단기의 `OSError`가 나고 pytest가 exit code `1`과 네트워크 시도 진단을 남겼다. 실제 collector에는 연결하지 않았다.

실패 경로 검토자는 기본 OTel 배치 설정과 같은 전송 대역으로 현재 AI suite 두 개도 실행했다. head의 root `conftest.py`를 로드하면 `1 failed, 249 passed, 4 errors`였다. `--confcutdir tests/reliability_ai`로 새 root `conftest.py`를 제외하고 AI 자체 fixture를 유지한 대조군에서는 `253 passed`였다.

#### F2 Impact

trace 수집을 요청하면 배치 스레드의 실행 시점에 따라 모의 전송만 쓰는 AI 테스트도 실패하고 trace 전송이 중단될 수 있다. 기본 CI에서는 `--export-traces`를 사용하지 않아 이 조합을 검증하지 않는다.

#### F2 Action

명시적으로 켠 pytest 자체의 OTLP/HTTP 전송을 허용하면서 AI 클라이언트의 주소 조회와 연결 차단을 유지한다. 하나의 pytest 실행에서 정상 AI 항목의 trace 내보내기와 AI 클라이언트 차단을 각각 확인하는 회귀 검증을 추가한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 로컬 xdist 2개 worker | `pytest -q -p no:sugar -p no:cacheprovider -n 2 --tb=short tests/test_ai_network_guard.py tests/reliability_ai tests/runtime_ai`에서 `260 passed`. |
| ✅ Pass | 원격 CI Lite | Prospective merge `0ab02324`의 `check` job이 Markdown·Python 검사를 통과했다. `python3 scripts/ci/run_checks.py pytest` 로그에서 `FULL_TESTS: true`, `1225 passed, 2 skipped`를 확인했다. [CI Job](https://github.com/mols3131d/hmda-data-reliability/actions/runs/44272773892/job/134693256335) |
| ✅ Pass | 실제 CPython 숫자 주소 조회 | 원본에서 차단기 `OSError`와 pytest 실패 진단을 확인했다. |
| ❌ Fail | 차단 제거 대조 실행 | 차단을 제거한 사본에서도 기존 회귀 테스트 `7 passed`. 주소 조회 함수의 반환 여부로만 원본과 차이를 확인했다. |
| ❌ Fail | `--export-traces`와 오프라인 AI 항목 동시 실행 | 같은 OTLP/HTTP 전송 대역에서 base는 exit `0`, head는 네트워크 시도 진단과 exit `1`을 반환했다. |
| ⚪ Not Verified | 실제 IPv4·IPv6 `connect`·`connect_ex` 실행 | 로컬 샌드박스가 소켓 생성을 거부했다. CPython 3.13.13 소스에서 두 함수가 `socket.connect` 이벤트의 예외를 받으면 `internal_connect` 전에 중단되는 경로를 확인했다. [CPython socket implementation](https://github.com/python/cpython/blob/v3.13.13/Modules/socketmodule.c#L3292-L3342) |

## Risks and Limits

- 샘플 AI session fixture의 정리 중 주소 조회는 AI 항목만 실행했을 때 차단됐다. 같은 fixture를 쓰는 AI 항목 뒤에 다른 디렉터리 항목을 실행하면 pytest가 마지막 항목의 teardown에서 정리해 주소 조회가 반환됐다. 현재 두 AI suite의 fixture와 AI pytest 항목 기준의 적용 범위를 확인해 후속 고려 사항으로 남긴다. [항목별 적용 경로](https://github.com/mols3131d/hmda-data-reliability/blob/7aec7be0fe8481eaec0f63bb5336b5485c1773d8/tests/conftest.py#L45-L57), [Work Status](02-brief-llm-test-structure-work-status.md#current-test-boundaries)
- 실제 collector 전송과 OTLP/gRPC, 실제 LLM·Langfuse 호출 및 평가는 실행하지 않았다. 수집 단계, 하위 프로세스와 native DNS는 차단기의 적용 범위 밖이다.
