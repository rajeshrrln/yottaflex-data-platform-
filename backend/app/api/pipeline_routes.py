
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.pipeline_orchestrator import (
    PipelineOrchestrator,
    PipelineExecutionError,
)

from app.services.run_history import (
    start_run,
    finish_run,
    get_run_history,
)

router = APIRouter(prefix="/api/pipelines", tags=["Pipelines"])


class PipelineRunRequest(BaseModel):
    config: dict[str, Any] = Field(
        ...,
        description="Metadata configuration for the ETL pipeline",
    )


@router.post("/run")
def run_pipeline(request: PipelineRunRequest):
    """Execute an ETL pipeline and store its execution history."""

    run_id, started_at = start_run(request.config)

    orchestrator = PipelineOrchestrator()

    try:
        
        result = orchestrator.run(
            request.config,
            run_id=run_id,
        )
        finish_run(
            run_id=run_id,
            started_at=started_at,
            status="success",
            result=result,
        )

        result["run_id"] = run_id
        return result

    except PipelineExecutionError as exc:
        finish_run(
            run_id=run_id,
            started_at=started_at,
            status="failed",
            error=str(exc),
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        finish_run(
            run_id=run_id,
            started_at=started_at,
            status="failed",
            error=str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Unexpected pipeline execution error",
        ) from exc


@router.get("/history")
def pipeline_history(limit: int = 50):
    """Retrieve recent pipeline execution history."""

    if limit < 1 or limit > 200:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 200",
        )

    return {
        "total": len(get_run_history(limit)),
        "runs": get_run_history(limit),
    }
