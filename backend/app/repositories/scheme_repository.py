"""
Scheme Repository — handles data access for government schemes,
relationships, filtering, and conversion to response schemas.
"""
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc
from sqlalchemy.orm import selectinload

from app.models.scheme import (
    Scheme, SchemeEligibilityRule, SchemeBenefit,
    SchemeDocument, SchemeLocation, SchemeSource
)
from app.schemas.scheme import (
    SchemeResponse, SchemeBenefitItem, SchemeDocumentItem,
    SchemeEligibilityRuleItem
)
from app.schemas.user import EntrepreneurProfileBase

logger = logging.getLogger(__name__)


class SchemeRepository:

    @staticmethod
    def to_response(scheme: Scheme) -> SchemeResponse:
        """Convert SQLAlchemy Scheme model to SchemeResponse with backwards compatibility."""
        # Convert benefits
        benefits_list = [
            SchemeBenefitItem(
                benefit_type=b.benefit_type or "General",
                amount=b.amount,
                percentage=b.percentage,
                unit=b.unit,
                description=b.description
            )
            for b in getattr(scheme, "benefits", []) or []
        ]

        # Convert documents
        docs_list = [
            SchemeDocumentItem(
                document_name=d.document_name,
                mandatory=bool(d.mandatory),
                conditional=bool(d.conditional),
                condition=d.condition,
                issuing_authority=d.issuing_authority
            )
            for d in getattr(scheme, "documents", []) or []
        ]

        # Convert eligibility rules
        rules_list = [
            SchemeEligibilityRuleItem(
                rule_type=r.rule_type,
                operator=r.operator,
                value=r.value,
                value_min=r.value_min,
                value_max=r.value_max,
                value_list=r.value_list or [],
                required=bool(r.required),
                source_text=r.source_text
            )
            for r in getattr(scheme, "eligibility_rules", []) or []
        ]

        # Build eligibility criteria dict for legacy compatibility
        legacy_criteria = {
            "requires_udyam": scheme.udyam_required or False,
            "min_age": scheme.age_min,
            "max_age": scheme.age_max,
            "disability_eligible": scheme.disability_eligibility or False
        }

        # Target demographics list
        demos = []
        if scheme.social_categories:
            demos.extend(scheme.social_categories)
        if scheme.gender_eligibility:
            demos.extend([g for g in scheme.gender_eligibility if g.lower() != "any"])
        if scheme.beneficiary_types:
            demos.extend(scheme.beneficiary_types)
        if scheme.disability_eligibility:
            demos.append("Differently-Abled")
        demos = list(dict.fromkeys(demos))  # Deduplicate

        return SchemeResponse(
            id=scheme.id,
            title=scheme.name,
            ministry_or_org=scheme.ministry or scheme.department or "Government of India",
            description=scheme.description or scheme.eligibility_text or "",
            target_demographics=demos,
            eligible_business_types=scheme.business_types or [],
            max_funding_amount=scheme.loan_amount_max or scheme.grant_amount,
            subsidy_percentage=scheme.subsidy_percentage,
            application_url=scheme.application_url or scheme.official_application_url,
            eligibility_criteria=legacy_criteria,
            scheme_code=scheme.scheme_code,
            slug=scheme.slug,
            status=scheme.status or "active",
            government_level=scheme.government_level,
            funding_type=scheme.funding_type,
            states=scheme.states or [],
            beneficiary_types=scheme.beneficiary_types or [],
            gender_eligibility=scheme.gender_eligibility or [],
            social_categories=scheme.social_categories or [],
            disability_eligibility=scheme.disability_eligibility or False,
            udyam_required=scheme.udyam_required or False,
            verification_status=scheme.verification_status or "UNKNOWN",
            verified_at=scheme.verified_at,
            source_name=scheme.source_name,
            source_url=scheme.source_url,
            official_source_url=scheme.official_source_url,
            data_quality_score=scheme.data_quality_score or 0,
            created_at=scheme.created_at or datetime.utcnow(),
            updated_at=scheme.updated_at,
            benefits=benefits_list,
            documents=docs_list,
            eligibility_rules=rules_list
        )

    @classmethod
    async def get_by_id(cls, session: AsyncSession, scheme_id: UUID) -> Optional[SchemeResponse]:
        """Fetch a single scheme by UUID with related entities loaded."""
        stmt = (
            select(Scheme)
            .options(
                selectinload(Scheme.eligibility_rules),
                selectinload(Scheme.benefits),
                selectinload(Scheme.documents),
                selectinload(Scheme.locations),
                selectinload(Scheme.sources),
            )
            .where(Scheme.id == scheme_id)
        )
        result = await session.execute(stmt)
        scheme = result.scalar_one_or_none()
        if not scheme:
            return None
        return cls.to_response(scheme)

    @classmethod
    async def list_schemes(
        cls,
        session: AsyncSession,
        status: Optional[str] = "active",
        state: Optional[str] = None,
        category: Optional[str] = None,
        business_type: Optional[str] = None,
        gender: Optional[str] = None,
        query: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[SchemeResponse], int]:
        """List schemes with dynamic filtering and pagination."""
        stmt = (
            select(Scheme)
            .options(
                selectinload(Scheme.eligibility_rules),
                selectinload(Scheme.benefits),
                selectinload(Scheme.documents)
            )
        )

        filters = []
        if status and status.lower() != "all":
            filters.append(Scheme.status == status.lower())

        if state:
            state_clean = state.title()
            filters.append(
                or_(
                    Scheme.states.contains([state_clean]),
                    Scheme.government_level == "central",
                    Scheme.states == []
                )
            )

        if category:
            filters.append(
                or_(
                    Scheme.social_categories.contains([category.upper()]),
                    Scheme.social_categories.contains([category.title()]),
                    Scheme.beneficiary_types.contains([category])
                )
            )

        if business_type:
            filters.append(
                or_(
                    Scheme.business_types.contains([business_type]),
                    Scheme.business_types.contains([business_type.title()]),
                    Scheme.business_types == []
                )
            )

        if gender and gender.lower() != "any":
            filters.append(
                or_(
                    Scheme.gender_eligibility.contains([gender.title()]),
                    Scheme.gender_eligibility.contains(["Any"]),
                    Scheme.gender_eligibility == []
                )
            )

        if query:
            search_pat = f"%{query.strip()}%"
            filters.append(
                or_(
                    Scheme.name.ilike(search_pat),
                    Scheme.description.ilike(search_pat),
                    Scheme.ministry.ilike(search_pat),
                    Scheme.scheme_code.ilike(search_pat)
                )
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        # Count total matches
        count_stmt = select(func.count(Scheme.id))
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        count_res = await session.execute(count_stmt)
        total = count_res.scalar() or 0

        # Pagination & sorting
        offset = max(0, (page - 1) * limit)
        stmt = stmt.order_by(desc(Scheme.data_quality_score), desc(Scheme.created_at)).limit(limit).offset(offset)

        result = await session.execute(stmt)
        schemes = result.scalars().all()

        return [cls.to_response(s) for s in schemes], total

    @classmethod
    async def get_schemes_for_profile(
        cls,
        session: AsyncSession,
        profile: EntrepreneurProfileBase,
        limit: int = 50
    ) -> List[SchemeResponse]:
        """Fetch candidate schemes for matching against an entrepreneur profile."""
        stmt = (
            select(Scheme)
            .options(
                selectinload(Scheme.eligibility_rules),
                selectinload(Scheme.benefits),
                selectinload(Scheme.documents)
            )
            .where(Scheme.status == "active")
        )

        # Geographic pre-filter: schemes must be central or match user state
        if profile.state:
            user_state = profile.state.title()
            stmt = stmt.where(
                or_(
                    Scheme.states.contains([user_state]),
                    Scheme.government_level == "central",
                    Scheme.states == []
                )
            )

        stmt = stmt.order_by(desc(Scheme.data_quality_score)).limit(limit)
        result = await session.execute(stmt)
        schemes = result.scalars().all()
        return [cls.to_response(s) for s in schemes]
