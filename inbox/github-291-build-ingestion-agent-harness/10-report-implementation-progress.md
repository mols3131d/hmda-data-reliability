---
type: report
title: PR 291 Implementation Progress
description: PR 작업 트리에서 실행한 변경과 검증, 남은 증명 및 다음 작업을 누적 기록합니다.
---

# PR 291 Implementation Progress

[작업 목록](09-plan-implementation-todo.md) · [교체 설계](07-design-reliability-ai-runtime-replacement/README.md)

## Current Status

- **구현** · 사고 조사 교체와 HMDA 적재 조사, 두 OpenSpec 작업을 각각 7/7 완료했다. Codex 구독 OAuth·Ollama의 실제 사고 조사와 오프라인 재현을 확인했다.
- **검증** · `main`과 통합한 구현이 GitHub CI를 통과했다. 로컬 전체 재실행에서 1,319건 통과·2건 생략. 앞선 추적 테스트 실패와 대조 결과는 아래에 기록했다. [최종 PR 검사](https://github.com/mols3131d/hmda-data-reliability/pull/291/checks)
- **운영 결정** · 규칙으로 끝나는 적재 조사는 즉시 실행할 수 있다. 모델 보조를 운영에서 쓰려면 담당자가 적재 Prompt의 `production` 라벨 발행을 선택한다. [운영 가이드](../../docs/development/ingestion-investigation.md#model-and-observation)

## Work Log

| 시점 (KST) | 작업 | 확인한 결과 |
| --- | --- | --- |
| 11월 19일 22:39 | PR 작업 트리를 원격 Draft head로 fast-forward | `617aba04 → 49b65523`. 기존 PR 자료를 보존하고 별도 브랜치의 `9b71834c`에서 PR 소유 조사·설계 문서 06–08과 두 OpenSpec만 가져왔다. |
| 22:39 | 실행 환경·교체 기준 고정 | 두 Change 모두 `spec-driven-tdd`, 시작 시 각 0/7. PR 트리에서 `uv sync --frozen --offline` 성공. 기존 head를 별도 디렉터리로 풀어 같은 lock으로 합성 다중 턴 테스트 1건 통과. |
| 22:39 | 기존 런타임 저장량 측정 | `tests/reliability_ai/test_investigation_agent.py::test_investigate_incident_dynamic_tool_calling_loop` 기준 모델 2턴, 도구 2건. 조사 파일 5개 24,514바이트(최종 JSON 23,595, 관측 69, 본문 0·524, 도구 요청 326). 테스트 입력으로 제공한 dbt 파일은 제외했다. |
| 22:39 | 구현 시작 | 사고 조사 그래프, 기록·재현, 제공자 구현을 나눴다. 위임 전제와 적재기의 읽기 경로를 같은 PR에서 확인한다. |
| 22:44 | 위임과 읽기 전용 준비 검사 | DB 연결 누락 1건과 복구 직전 기한 만료 2건을 실패로 재현한 후 수정했다. 위임 테스트 25건 통과. 원천 검사 5건에서 CSV·Parquet 대상 행, 다른 파일의 열 누락, 미확인·빈 원천, 심볼릭 링크 차단을 확인했다. |
| 22:46 | 첫 체크포인트 게시 | 설계·투두·보고서를 `1f1c18bf`로 Draft PR에 푸시했다. 두 Change의 strict 검증 통과. |
| 22:48 | 공용 그래프·사고 조사 근거 | 그래프·도구·조사 테스트 82건 통과. 같은 합성 조사의 상태·사실·권고·도구 순서·원문이 일치했다. 조사 파일은 5개에서 7개로 늘고 총량은 24,514에서 14,206바이트로 줄었다. |
| 22:49 | 구독 계정과 Ollama의 공개 진입점 실실행 | 합성 Dataset의 같은 항목과 native Prompt v1 사용. Codex `inv-c060f719edb64b2baf7426f928f4cdba`는 새 스레드 2개와 `compare_profiles` 1회로 완료했다. Ollama `inv-5a30b674f2b64468bff601972df62aae`는 모델 1턴, 조회 0회로 완료했다. |
| 22:49 | 적재 준비·사후·재현 경로 | 로컬 15건 통과. 모델 생략, 올바른 제안 ID의 후속 메시지, 복수·범위 밖 요청 차단, 근거 파일 손상, Airflow 실행·시도 불일치를 포함한다. |
| 22:53 | 실제 Airflow 기록 확인 | 격리된 로컬 CSV 1,000행 준비 검사 → 실제 DAG 실행 → Airflow 3.3 공개 API의 세 단계에서 success/success/skipped를 읽었다. 실행 `manual__2026-11-19T13:52:55.459989+00:00`의 동일 입력 여부는 `unknown`이었다. 조사 `ing-304a38f72fe244269127ef986025250d`를 오프라인으로 재현했다. |
| 22:55 | 독립 검토 후 보완 | 늦은 원천 검사 채택, Airflow 두 번째 요청의 기한, 잘린 모델 응답 채택을 각각 실패로 재현하고 수정했다. 적재 소스·Airflow 테스트 15건과 적재 워크플로 테스트 10건 통과. |
| 22:57 | 사고 조사 독립 재현 | 실제 Codex `inv-d686dbc2f2e248979e4e0b73f548c67f`(2턴)와 Ollama `inv-d21c326db35a4d768fbb3e75d6d5af47`(3턴)의 결과를 외부 모델·도구 호출 0회로 복원했다. Codex 입력의 직렬화 순서도 근거에 보존한다. |
| 22:57 | Langfuse 원격 조회 | 합성 항목 3개를 native Dataset CLI로 실행했다. 고정 응답 모델 6회, 호스트 조회 3회. 실험 `50177ab8-795b-4fb7-92d7-61fc51f8283e`의 항목 3개와 실제 span 12개의 ID·부모·Prompt v1을 원격에서 대조했다. 사람의 품질 평가는 별도로 남는다. |
| 23:02 | 로컬 전체 회귀 1차 | `pytest -q tests`에서 1,306건 통과·2건 skip. 실행 도중 보강한 마지막 회귀는 별도로 다시 확인한다. |
| 23:10 | 독립 검토 최종 보완 | 담당자 간 메시지로 재현 조건을 교차 검토했다. Codex 구독 유형·프레임 크기·재시도 분류를 수정하고 23건 통과. 도구 응답 ID 불일치·직렬화된 JSON의 민감 필드를 검증했다. 별도 검토자가 미완성 Markdown 코드 블록에서 누출을 재현했고 공통 파서를 적용한 뒤 독립 재검토 7건 통과. |
| 23:11 | 배포 가능한 산출물·구조 확인 | `uv build --offline --wheel` 산출물에 적재 Prompt와 두 실행 모듈 포함. 새 상태 표현으로 그래프·적재 20건 재검증. Ruff, Tach, 런타임·조사 코드 35개 파일의 mypy와 ty 통과. |
| 23:15 | 구현 커밋 재검증 | `255bf98d0b43c5cb2cd20e40e8bf62613157b806`에서 같은 합성 사고 조사의 모델 2턴·도구 2건·사실·결과·응답 바이트가 일치했다. 두 작업 경로 길이를 맞춰 측정한 전체 파일은 24,514 → 14,347바이트(41.5% 감소)였다. |
| 23:15 | 실제 제공자와 독립 재현 | 위 커밋에서 Codex `inv-29e7baa8470e484ba4c4d5cbfab0a5db`는 모델 2턴·호스트 조회 1건, Ollama `inv-84a70a6af0f14f4698d58e1be52a8510`는 모델 1턴·조회 0건으로 완료했다. 두 기록 모두 `replayed / completed`로 재현됐다. |
| 23:15 | 원격·Airflow 재확인 | Langfuse 실험 `2e2925a0-c433-43a6-aa02-9590bf2912b5`에서 위 구현 SHA, 항목 3개, 실제 span 12개를 조회했다. 격리 DAG 조사 `ing-628a077c45084679a77c6909525cec19`에서 성공·성공·생략을 확인하고 `ing-c699f27ae63f41c79d2320f3a227220a`로 재현했다. |
| 23:18 | 구현 커밋 전체 테스트 | `pytest -q -rs -p no:testmon tests`에서 1,319건 통과·2건 skip. skip은 Windows npm/Node 전용 검사와 로컬에 캐시되지 않은 zizmor 감사다. 제공자 테스트의 선택적 시도 기록에 명시적 단언을 추가하고 전 저장소 ty와 관련 테스트 28건을 별도 확인했다. |
| 23:20 | 로컬 푸시 훅 복구 | 훅이 상속한 Git 환경 때문에 테스트가 PR 로컬 ref와 인덱스·공용 Git 설정을 바꿨다. 푸시를 중단하고 구현 SHA·인덱스 트리 `de232a5a`·원래 작성자 설정을 복구했다. 주 작업 트리는 원래 `9b71834c`에서 clean, 원격은 `1f1c18bf`임을 확인했다. Git 환경을 비운 테스트 자식 프로세스에서 임시 저장소 생성·커밋 격리 검사를 통과했다. |
| 23:24 | `main` 테스트 분류 통합 | 기한 만료 회귀에 `component`를 적용하고 기존 테스트의 분류를 보존했다. 충돌이 있던 두 모듈에서 86건 통과. 격리한 훅으로 `742dc0ff`를 푸시한 뒤 두 작업 트리와 PR 인덱스를 확인했다. 원격에서 `main`의 `fe67f9eb`와 병합 가능 상태를 확인했다. |
| 23:25 | 변경 테스트 분류 독립 검증 | `bb67a5f0`에서 PR이 수정한 11개 테스트 모듈의 186건을 수집했다. unit 64건, component 56건, integration 66건이고 분류 누락·중복은 0건이었다. 병합 훅이 재정렬했던 타 PR의 문서는 `main` 원본과 동일하다. |
| 23:27 | 원격 통합 CI 통과 | head `742dc0ff`, base `fe67f9eb`, 시험 병합 `33af652a`. CI가 선택한 테스트 1,317건 통과·2건 생략. Python·wheel·OpenSpec 검사도 통과했다. [CI 실행 기록](https://github.com/mols3131d/hmda-data-reliability/actions/runs/44543419980) |
| 23:28 | 로컬 전체 실행에서 추적 테스트 차이 발견 | 1,318건 통과·2건 생략·1건 실패. 사전 설치한 OpenTelemetry 제공자의 네트워크 접근은 차단됐지만 테스트가 예상한 두 실패 중 하나를 pytest가 setup 오류로 분류했다. 해당 모듈만 재실행해도 한 번 재현됐다. |
| 23:30 | 추적 테스트 대조 | 테스트와 네트워크 차단 코드가 `main`과 동일함을 확인했다. 독립 검토자는 `main`에서 해당 사례를 3회 실행해 모두 통과했다. 같은 Python 환경에서 모듈 전체를 양쪽에 한 번씩 실행한 결과도 각각 5/5 통과였다. 최초 실패의 원인은 확정하지 못했다. |
| 23:32 | 통합 후 전체 회귀 재검증과 인계 | `bb67a5f0`에서 전체 테스트를 다시 실행해 1,319건 통과·2건 생략(235.94초). 생략한 검사는 위와 같다. Draft PR 본문을 구현·검증 결과로 갱신했다. 최종 보고서 커밋의 검사 결과는 [PR 검사](https://github.com/mols3131d/hmda-data-reliability/pull/291/checks)에서 확인한다. |
| 11월 20일 | Codex 기본 모델 변경 | 현재 모델 목록의 Luna 모델 중 최신인 `gpt-6-luna`를 기본으로 지정했다. 실제 구독 연결에서 조사 `inv-6a85377047f941dca356aa6a262d0f11`가 모델 2턴·조회 1건으로 완료하고 오프라인 재현됐다. 선택·어댑터 테스트 28건 통과. 모델은 버전 고정이므로 후속 모델이 나오면 설정 갱신이 필요하다. |
| 11월 20일 | 사고 조사 결과 JSON 자동 저장 | 새 사고 조사의 읽기용 결과를 `reliability-ai/results/<invocation_id>.json`에 자동 저장한다. 정상·모델 오류·기한 종료·쓰기 실패와 오프라인 재현을 검증했다. 적재 조사의 결과 파일은 `ingestion/<investigation_id>/result.json`에서 읽는다. |

## Resume

작업 브랜치는 `agent/feat/build-ingestion-agent-harness`다. 두 Change의 수용 조건은 로컬·합성·실제 제공자 근거로 확인했다. 현재 배포 환경에서 적재 전용 native Prompt의 `production` 라벨을 조회하면 등록 전 상태다. 규칙만으로 끝나는 조사는 바로 실행할 수 있다. 운영자가 모델 보조 경로를 채택하면 [적재 조사 가이드](../../docs/development/ingestion-investigation.md#model-and-observation)의 명시적 등록 명령을 실행한다. 실제 출력의 업무 효용 평점, Draft 해제와 병합은 사람에게 남는다.
