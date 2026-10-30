"""Native SDK lifecycle의 비공개 격리 진입점. 부모가 외부 I/O deadline을 소유한다."""

import contextlib
import json
import logging
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any


def worker() -> int:
    protocol = sys.stdout

    def emit(kind: str, **data: Any) -> None:
        protocol.write(json.dumps(dict(kind=kind, **data), ensure_ascii=False) + "\n")
        protocol.flush()

    logging.disable(logging.CRITICAL)
    try:
        request = json.loads(sys.stdin.buffer.read(2_097_153))
        from hmda_reliability.review_ai import review_null_spike
        from hmda_reliability.review_ai.contracts import AgenticReviewInput
        from hmda_reliability.review_ai.evaluation.live import load_live_configuration
        from hmda_reliability.review_ai.evaluation.native_sdk import (
            make_client,
            read_annotations,
            run_native_experiment,
        )

        with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink):
            if request.get("action") == "check":
                result = read_annotations(
                    make_client(request["langfuse"]),
                    request["receipt"],
                    request["reviewer_id"],
                    artifact_root=Path(request["artifact_root"]),
                    baseline=request.get("baseline"),
                )
                emit("receipt", receipt=dict(status="checked", annotations=result))
            else:
                configuration = load_live_configuration(os.environ)

                def review(case: Any) -> Any:
                    material = AgenticReviewInput.model_validate(
                        dict(
                            case["review_input"],
                            project_revision=configuration.project_revision,
                        )
                    )
                    emit("phase", phase="core")
                    try:
                        result = review_null_spike(
                            incident=material.incident,
                            evidence=material.evidence,
                            draft=material.draft,
                            project_revision=configuration.project_revision,
                            settings=configuration.settings,
                            review_settings=configuration.review_settings,
                            execution_settings=configuration.execution_settings,
                            artifact_root=configuration.artifact_root,
                            on_progress=lambda event: emit(
                                "progress", event=asdict(event)
                            ),
                        )
                        emit(
                            "core_result",
                            result={
                                "case_id": case["case_id"],
                                "workflow_id": result.workflow_id,
                                "status": result.status,
                                "failure_code": result.failure_code,
                            },
                        )
                        return result
                    finally:
                        emit("phase", phase="remote")

                receipt = run_native_experiment(
                    settings=request["langfuse"],
                    cases=request["cases"],
                    run_name=request["run_name"],
                    project_revision=configuration.project_revision,
                    artifact_root=configuration.artifact_root,
                    review_case=review,
                    baseline=request.get("baseline"),
                )
                emit("receipt", receipt=receipt)
        return 0
    except ImportError:
        emit(
            "receipt",
            receipt=dict(status="unavailable", failure_code="optional_sdk_missing"),
        )
    except Exception:
        emit(
            "receipt",
            receipt=dict(status="unavailable", failure_code="native_experiment_failed"),
        )
    return 1


if __name__ == "__main__":
    # Native run_experiment가 flush한 뒤 자동 atexit flush를 다시 기다리지 않는다.
    os._exit(worker())
