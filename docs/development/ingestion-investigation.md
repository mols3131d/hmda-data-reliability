---
title: Ingestion Investigation
description: 원천 준비, 지정 Airflow 실행 조회, 근거 복원과 적재 모델 설정 사용법입니다.
categories:
  - data-engineering
tags:
  - airflow
  - ingestion
  - llmops
---

# Ingestion Investigation

`prepare`는 요청에 지정된 원천을 읽고 운영자가 적재를 진행할 수 있는지 검사한다. `review_run`은 이미 존재하는 DAG 실행의 단계를 읽는다. 두 호출은 같은 디렉터리에 조사 ID별 기록을 남긴다.

## Prepare And Review

```python
import os
from pathlib import Path

import httpx

from hmda_reliability.data_operations.request import DataOperationRequest
from hmda_reliability.reliability_ai.ingestion import (
    AirflowRunReader, RunRef, investigate_ingestion, replay_ingestion,
)

root = Path(".local/artifacts")
request = DataOperationRequest(source_root=Path("data/raw/hmda"), source_year=2025)
before = investigate_ingestion("prepare", request=request, artifact_root=root)
print(before["status"], before["next_action"], before["initial"]["version"])

with httpx.Client(
    base_url=os.environ["AIRFLOW_API_V2_URL"],  # 예: http://localhost:8080/api/v2/
    headers={"Authorization": "Bearer " + os.environ["AIRFLOW_API_TOKEN"]},
) as client:
    after = investigate_ingestion(
        "review_run",
        run=RunRef(run_id=os.environ["AIRFLOW_RUN_ID"]),
        reader=AirflowRunReader(client),
        previous_id=before["investigation_id"],
        artifact_root=root,
    )

again = replay_ingestion(after["investigation_id"], artifact_root=root)
print(after["initial"]["stages"], again["termination"])
```

| 결과 | 운영자가 확인할 내용 |
| --- | --- |
| `ready` | 확인한 버전에서 필수 열·대상 행 검사를 통과했다. 실제 적재는 별도의 권한으로 요청한다. |
| `blocked` | 빈 원천, 누락 열, 파싱 위반 또는 대상 0행을 확인했다. `initial`의 이유와 범위를 본다. |
| `needs_human` | 판정에 필요한 근거가 부족하다. 경로·권한·기한을 확인한다. |
| `input_match=unknown` | 실제 적재의 원천 버전이나 같은 시도의 근거가 부족하다. 태스크 성공만으로 행 수 또는 입력 일치를 확정할 수 없다. |
| `termination` | 모델·도구·저장 경계의 종료 사유다. `advisory`에는 확인된 근거를 인용한 후속 권고가 담긴다. |

중단된 조사를 재요청하려면 `previous_id`에 원 조사 ID를 전달한다. 새 ID로 현재 입력을 다시 검사한다. 과거 사실을 검토할 때는 `replay_ingestion`을 사용한다. 원천·모델·Airflow 접근 없이 기록된 그래프를 실행하며 누락·손상된 근거는 종료 사유로 표시한다.

## Model And Observation

판정과 다음 조치가 정해지면 모델과 Prompt 조회는 0회다. 추가 해석이 필요한 경우 첫 모델 턴에서 native Prompt를 읽어 버전을 고정한다. 적재 Prompt를 새 Langfuse 환경에 발행할 때 운영자는 다음 명령을 한 번 실행한다. 이 명령은 `hmda-reliability-ai/ingestion`의 새 버전에 `production` 라벨을 부여한다.

```bash
uv run --env-file .env python -m hmda_reliability.reliability_ai.evaluation.setup --ingestion-prompt-only
```

제공자 주입과 Codex·Ollama 선택은 사고 조사와 같다. `synthetic=True`는 호출자가 승인한 합성 입력에만 지정한다. 모델과 조회의 관측 전송 상태는 조사 디렉터리의 `observations.json`에서 확인한다. [제공자 설정과 실실행 범위](review-ai-evaluation.md#configure-connections)

[적재 도메인](../domains/hmda-data.md) · [공개 조사 API](../../src/hmda_reliability/reliability_ai/ingestion/__init__.py)
