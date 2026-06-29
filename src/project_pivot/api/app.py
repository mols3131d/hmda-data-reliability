"""FastAPI app for MVP pipeline runtime."""

from fastapi import FastAPI, HTTPException

from project_pivot.hmda_data.errors import HMDADataLoadError
from project_pivot.pipeline import (
    MvpPipelineRunRequest,
    MvpPipelineRunResult,
    PipelineRuntimeError,
    run_mvp_pipeline,
)
from project_pivot.reliability.errors import ReliabilityError


def create_app() -> FastAPI:
    """FastAPI app factory."""

    application = FastAPI(title="Project Pivot MVP Runtime")

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.post("/pipeline/run", response_model=MvpPipelineRunResult)
    async def run_pipeline(request: MvpPipelineRunRequest) -> MvpPipelineRunResult:
        try:
            return run_mvp_pipeline(request)
        except (PipelineRuntimeError, ReliabilityError, HMDADataLoadError) as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return application


app = create_app()
