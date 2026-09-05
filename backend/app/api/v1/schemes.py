import json
import logging
import os
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.scheme_repository import SchemeRepository
from app.schemas.scheme import SchemeResponse, SchemeListResponse

logger = logging.getLogger(__name__)
router = APIRouter()

SEED_FILE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "seed", "seed_schemes.json")
)


def _load_fallback_seed_schemes() -> List[SchemeResponse]:
    """Helper to load fallback seed schemes if DB is empty."""
    if not os.path.exists(SEED_FILE_PATH):
        return []
    try:
        with open(SEED_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        results = []
        for s in data:
            results.append(
                SchemeResponse(
                    id=UUID(s["id"]),
                    title=s["name"],
                    ministry_or_org=s.get("ministry") or "Government of India",
                    description=s.get("description", ""),
                    target_demographics=s.get("social_categories", []) + [g for g in s.get("gender_eligibility", []) if g != "Any"],
                    eligible_business_types=s.get("eligible_business_types", []),
                    max_funding_amount=Decimal(str(s["loan_amount_max"])) if s.get("loan_amount_max") else None,
                    subsidy_percentage=Decimal(str(s["subsidy_percentage"])) if s.get("subsidy_percentage") else None,
                    application_url=s.get("application_url"),
                    eligibility_criteria={
                        "requires_udyam": s.get("udyam_required", False),
                        "min_age": s.get("age_min", 18)
                    },
                    scheme_code=s.get("scheme_code"),
                    status="active",
                    government_level=s.get("government_level", "central"),
                    funding_type=s.get("funding_type", "central_sector"),
                    states=s.get("states", []),
                    beneficiary_types=s.get("beneficiary_types", []),
                    gender_eligibility=s.get("gender_eligibility", []),
                    social_categories=s.get("social_categories", []),
                    disability_eligibility=s.get("disability_eligibility", False),
                    udyam_required=s.get("udyam_required", False),
                    verification_status=s.get("verification_status", "OFFICIAL_NEEDS_REVIEW"),
                    source_name=s.get("source_name"),
                    source_url=s.get("source_url"),
                    official_source_url=s.get("official_source_url"),
                    data_quality_score=70,
                    created_at=datetime.utcnow()
                )
            )
        return results
    except Exception as e:
        logger.error("Failed to load fallback seeds: %s", e)
        return []


@router.get("", response_model=List[SchemeResponse], tags=["Schemes"])
async def list_schemes(
    status: Optional[str] = Query("active", description="Filter by status (active, closed, all)"),
    state: Optional[str] = Query(None, description="Filter by Indian State"),
    category: Optional[str] = Query(None, description="Filter by Social Category (SC, ST, OBC, Minority)"),
    business_type: Optional[str] = Query(None, description="Filter by Business Sector/Type"),
    gender: Optional[str] = Query(None, description="Filter by Gender"),
    query: Optional[str] = Query(None, description="Search keyword in scheme name or description"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve government schemes backed by verified database storage,
    with comprehensive multi-faceted filtering and search.
    """
    try:
        schemes, total = await SchemeRepository.list_schemes(
            session=db,
            status=status,
            state=state,
            category=category,
            business_type=business_type,
            gender=gender,
            query=query,
            page=page,
            limit=limit
        )
        if schemes:
            return schemes
    except Exception as e:
        logger.warning("Database query failed, falling back to seed data: %s", e)

    # If DB has no records yet or is unreachable, fallback to seed records
    seeds = _load_fallback_seed_schemes()
    filtered = seeds
    if category:
        filtered = [s for s in filtered if category.upper() in [c.upper() for c in s.social_categories]]
    if business_type:
        filtered = [s for s in filtered if business_type.lower() in [b.lower() for b in s.eligible_business_types]]
    if gender and gender.lower() != "any":
        filtered = [s for s in filtered if any(gender.lower() in g.lower() for g in s.gender_eligibility)]
    if query:
        q = query.lower()
        filtered = [s for s in filtered if q in s.title.lower() or q in (s.description or "").lower()]
    return filtered[:limit]


@router.get("/{scheme_id}", response_model=SchemeResponse, tags=["Schemes"])
async def get_scheme(scheme_id: UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve details of a specific scheme by UUID including rules, benefits, and documents."""
    try:
        scheme = await SchemeRepository.get_by_id(db, scheme_id)
        if scheme:
            return scheme
    except Exception as e:
        logger.warning("Database lookup failed: %s", e)

    # Check fallback seeds
    seeds = _load_fallback_seed_schemes()
    for s in seeds:
        if s.id == scheme_id:
            return s

    raise HTTPException(status_code=404, detail="Scheme not found")
