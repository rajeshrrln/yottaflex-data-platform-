from fastapi import APIRouter, HTTPException, Query

from app.services.quarantine import (
    get_quarantined_records,
    get_quarantine_summary,
)

router = APIRouter(
    prefix="/api/quarantine",
    tags=["Quarantine"],
)


@router.get("/")
def list_quarantined_records(
    limit: int = Query(default=100, ge=1, le=500),
    run_id: str | None = None,
):
    return {
        "records": get_quarantined_records(
            limit=limit,
            run_id=run_id,
        )
    }


@router.get("/summary")
def quarantine_summary():
    return get_quarantine_summary()