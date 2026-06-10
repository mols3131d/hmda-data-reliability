"""FastAPI app for MVP pipeline runtime."""

from fastapi import FastAPI, HTTPException

from project_pivot.pipeline import (
    MvpPipelineRunRequest,
    MvpPipelineRunResult,
    PipelineRuntimeError,
    run_mvp_pipeline,
)
from project_pivot.reliability.errors import ReliabilityError
from project_pivot.taxi_data.errors import TaxiDataLoadError


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
        except (PipelineRuntimeError, ReliabilityError, TaxiDataLoadError) as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return application


app = create_app()
