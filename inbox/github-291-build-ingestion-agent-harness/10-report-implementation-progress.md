---
type: report
title: PR 291 Implementation Progress
description: PR 작업 트리에서 실행한 변경과 검증, 남은 증명 및 다음 작업을 누적 기록합니다.
---

# PR 291 Implementation Progress

[작업 목록](09-plan-implementation-todo.md) · [교체 설계](07-design-reliability-ai-runtime-replacement/README.md)

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

## Resume

작업 브랜치는 `agent/feat/build-ingestion-agent-harness`다. 두 Change의 수용 조건은 로컬·합성·실제 제공자 근거로 확인했다. 현재 배포 환경에서 적재 전용 native Prompt의 `production` 라벨을 조회하면 등록 전 상태다. 규칙만으로 끝나는 조사는 바로 실행할 수 있다. 운영자가 모델 보조 경로를 채택하면 [적재 조사 가이드](../../docs/development/ingestion-investigation.md#model-and-observation)의 명시적 등록 명령을 실행한다. 실제 출력의 업무 효용 평점, Draft 해제와 병합은 사람에게 남는다.
