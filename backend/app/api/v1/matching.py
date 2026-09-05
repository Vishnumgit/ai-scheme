import logging
from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import EntrepreneurProfileBase
from app.schemas.scheme import SchemeMatchResult, SchemeResponse
from app.core.database import get_db
from app.repositories.scheme_repository import SchemeRepository
from app.services.recommendation_service import RecommendationService
from app.api.v1.schemes import _load_fallback_seed_schemes

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/recommend", response_model=List[SchemeMatchResult], tags=["AI Scheme Matching"])
async def match_schemes(
    profile: EntrepreneurProfileBase,
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluates entrepreneur profile demographics, caste, gender, turnover, 
    and sector against government scheme rules and returns prioritized matches 
    with transparent scoring breakdown and dynamic document checklists.
    """
    candidates: List[SchemeResponse] = []
    try:
        candidates = await SchemeRepository.get_schemes_for_profile(db, profile, limit=50)
    except Exception as e:
        logger.warning("Database candidate query failed, using fallback seeds: %s", e)

    if not candidates:
        candidates = _load_fallback_seed_schemes()

    recommendations = await RecommendationService.recommend(profile, candidates)
    return recommendations
