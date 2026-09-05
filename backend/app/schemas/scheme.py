from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class SchemeBase(BaseModel):
    title: str = ""
    ministry_or_org: str = ""
    description: Optional[str] = ""
    target_demographics: List[str] = []
    eligible_business_types: List[str] = []
    max_funding_amount: Optional[Decimal] = None
    subsidy_percentage: Optional[Decimal] = None
    application_url: Optional[str] = None
    eligibility_criteria: Optional[Dict[str, Any]] = {}

    # Rich normalized fields
    scheme_code: Optional[str] = None
    slug: Optional[str] = None
    status: str = "active"
    government_level: Optional[str] = None
    funding_type: Optional[str] = None
    states: List[str] = []
    beneficiary_types: List[str] = []
    gender_eligibility: List[str] = []
    social_categories: List[str] = []
    disability_eligibility: bool = False
    udyam_required: bool = False
    verification_status: str = "UNKNOWN"
    verified_at: Optional[datetime] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    official_source_url: Optional[str] = None
    data_quality_score: int = 0


class SchemeCreate(SchemeBase):
    pass


class SchemeBenefitItem(BaseModel):
    benefit_type: str
    amount: Optional[Decimal] = None
    percentage: Optional[Decimal] = None
    unit: Optional[str] = None
    description: Optional[str] = None


class SchemeDocumentItem(BaseModel):
    document_name: str
    mandatory: bool = True
    conditional: bool = False
    condition: Optional[str] = None
    issuing_authority: Optional[str] = None


class SchemeEligibilityRuleItem(BaseModel):
    rule_type: str
    operator: Optional[str] = None
    value: Optional[str] = None
    value_min: Optional[str] = None
    value_max: Optional[str] = None
    value_list: List[str] = []
    required: bool = True
    source_text: Optional[str] = None


class SchemeResponse(SchemeBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    benefits: List[SchemeBenefitItem] = []
    documents: List[SchemeDocumentItem] = []
    eligibility_rules: List[SchemeEligibilityRuleItem] = []

    class Config:
        from_attributes = True


class SchemeListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[SchemeResponse]


class ScoreBreakdown(BaseModel):
    demographic_score: float = 0.0
    business_score: float = 0.0
    category_score: float = 0.0
    semantic_score: float = 0.0
    hard_filter_passed: bool = True


class SchemeMatchResult(BaseModel):
    scheme: SchemeResponse
    match_score: float  # e.g., 95.0%
    eligibility_status: str  # "Highly Eligible", "Eligible", "Partially Eligible"
    ai_reasoning: str
    key_benefits: List[str]
    required_documents: List[str]
    score_breakdown: Optional[ScoreBreakdown] = None
    missing_requirements: List[str] = []
    matching_factors: List[str] = []
