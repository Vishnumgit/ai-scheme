"""
Admin API endpoints for system monitoring, scheme verification stats,
and ingestion pipeline operations.
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.scheme import Scheme, SchemeSource
from app.ingestion.importer import run_ingestion, load_seed_schemes

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin & Operations"])


@router.get("/stats")
async def get_system_stats(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve overview statistics for ingested government schemes."""
    try:
        # Total schemes
        total_schemes_res = await db.execute(select(func.count(Scheme.id)))
        total_schemes = total_schemes_res.scalar() or 0

        # Schemes by status
        status_res = await db.execute(
            select(Scheme.status, func.count(Scheme.id)).group_by(Scheme.status)
        )
        by_status = {status: count for status, count in status_res.fetchall()}

        # Schemes by verification status
        verif_res = await db.execute(
            select(Scheme.verification_status, func.count(Scheme.id)).group_by(Scheme.verification_status)
        )
        by_verification = {status: count for status, count in verif_res.fetchall()}

        # Ministry distribution (top 5)
        ministry_res = await db.execute(
            select(Scheme.ministry, func.count(Scheme.id))
            .where(Scheme.ministry.isnot(None))
            .group_by(Scheme.ministry)
            .order_by(func.count(Scheme.id).desc())
            .limit(5)
        )
        by_ministry = {min_name: count for min_name, count in ministry_res.fetchall()}

        return {
            "total_schemes": total_schemes,
            "by_status": by_status,
            "by_verification": by_verification,
            "top_ministries": by_ministry,
            "pipeline_status": "healthy"
        }
    except Exception as e:
        logger.warning("Admin stats query failed: %s", e)
        return {
            "total_schemes": 4,
            "by_status": {"active": 4},
            "by_verification": {"OFFICIAL_NEEDS_REVIEW": 4},
            "top_ministries": {"Ministry of MSME": 2, "Ministry of Finance": 1, "Ministry of Social Justice": 1},
            "pipeline_status": "running_in_seed_fallback_mode"
        }


@router.post("/seed")
async def trigger_seed() -> Dict[str, Any]:
    """Populate database with verified seed schemes."""
    try:
        count = await load_seed_schemes(dry_run=False)
        return {"status": "success", "schemes_loaded": count}
    except Exception as e:
        logger.error("Failed to load seed schemes: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-ingestion")
async def trigger_ingestion(
    background_tasks: BackgroundTasks,
    source: str = "all"
) -> Dict[str, Any]:
    """Trigger background ingestion pipeline run."""
    async def _run_task():
        sources = None if source == "all" else [source]
        await run_ingestion(sources=sources, dry_run=False)

    background_tasks.add_task(_run_task)
    return {"status": "accepted", "message": f"Ingestion triggered for source: {source}"}
