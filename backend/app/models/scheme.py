"""
Canonical Scheme model — normalized, source-verified, versioned.
Replaces the old flat `schemes` table.
"""
from sqlalchemy import (
    Column, String, Numeric, Text, DateTime, Boolean,
    Integer, JSON, ARRAY, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_code = Column(String(100), nullable=True, index=True)  # Official ID from source
    slug = Column(String(255), nullable=True, unique=True, index=True)

    # Identity
    name = Column(String(500), nullable=False)
    short_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    scheme_version = Column(Integer, default=1)
    status = Column(String(50), default="active")  # active/suspended/closed/merged/discontinued/unknown

    # Ownership
    ministry = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    implementing_agency = Column(String(255), nullable=True)
    funding_type = Column(String(50), nullable=True)  # central_sector/centrally_sponsored/state/local/other
    government_level = Column(String(50), nullable=True)  # central/state/union_territory/district

    # Geography
    states = Column(ARRAY(String), default=list)
    districts = Column(ARRAY(String), default=list)
    rural_urban_scope = Column(String(50), nullable=True)  # rural/urban/both
    geographic_restrictions = Column(Text, nullable=True)

    # Target beneficiaries
    beneficiary_types = Column(ARRAY(String), default=list)
    gender_eligibility = Column(ARRAY(String), default=list)  # Male/Female/Any/Transgender
    social_categories = Column(ARRAY(String), default=list)  # SC/ST/OBC/EWS/Minority/General/Other
    disability_eligibility = Column(Boolean, default=False)
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)
    citizenship_requirements = Column(Text, nullable=True)
    residency_requirements = Column(Text, nullable=True)

    # Financial / economic conditions
    income_limit = Column(Numeric(15, 2), nullable=True)
    income_limit_period = Column(String(20), nullable=True)  # annual/monthly
    income_limit_type = Column(String(50), nullable=True)
    land_holding_limit = Column(String(100), nullable=True)
    loan_amount_min = Column(Numeric(15, 2), nullable=True)
    loan_amount_max = Column(Numeric(15, 2), nullable=True)
    subsidy_amount = Column(Numeric(15, 2), nullable=True)
    subsidy_percentage = Column(Numeric(5, 2), nullable=True)
    grant_amount = Column(Numeric(15, 2), nullable=True)
    interest_subvention = Column(Numeric(5, 2), nullable=True)
    collateral_requirement = Column(Boolean, nullable=True)
    margin_money_requirement = Column(Numeric(5, 2), nullable=True)

    # Education / occupation / enterprise
    education_requirements = Column(Text, nullable=True)
    occupation_types = Column(ARRAY(String), default=list)
    employment_status = Column(ARRAY(String), default=list)
    business_types = Column(ARRAY(String), default=list)
    enterprise_size = Column(String(50), nullable=True)  # micro/small/medium/large
    msme_requirements = Column(Boolean, default=False)
    udyam_required = Column(Boolean, default=False)
    startup_requirements = Column(Boolean, default=False)
    farmer_requirements = Column(Boolean, default=False)
    artisan_requirements = Column(Boolean, default=False)
    student_requirements = Column(Boolean, default=False)

    # Eligibility — both machine-readable AND original text preserved
    eligibility_rules_json = Column(JSONB, default=list)  # structured rules array
    eligibility_text = Column(Text, nullable=True)        # original source text, never discarded
    exclusions = Column(Text, nullable=True)
    priority_groups = Column(ARRAY(String), default=list)
    selection_method = Column(Text, nullable=True)

    # Benefits
    benefits_structured_json = Column(JSONB, default=list)
    benefits_text = Column(Text, nullable=True)
    financial_benefit = Column(Boolean, default=False)
    non_financial_benefits = Column(ARRAY(String), default=list)
    benefit_duration = Column(String(100), nullable=True)
    benefit_coverage = Column(Text, nullable=True)
    benefit_frequency = Column(String(100), nullable=True)

    # Application
    application_mode = Column(ARRAY(String), default=list)  # online/offline/both
    application_steps = Column(Text, nullable=True)
    application_url = Column(Text, nullable=True)
    official_application_url = Column(Text, nullable=True)
    offline_application_details = Column(Text, nullable=True)
    application_deadline = Column(Text, nullable=True)
    application_window = Column(Text, nullable=True)
    processing_authority = Column(String(255), nullable=True)

    # Evidence / provenance — every record MUST have source
    source_name = Column(String(255), nullable=True)
    source_url = Column(Text, nullable=True)
    official_source_url = Column(Text, nullable=True)
    source_type = Column(String(50), nullable=True)  # official_portal/api/ministry_page/open_data/manual
    source_document_url = Column(Text, nullable=True)
    source_last_checked_at = Column(DateTime(timezone=True), nullable=True)
    scheme_last_updated_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_status = Column(String(50), default="UNKNOWN")
    # VERIFIED_OFFICIAL / OFFICIAL_NEEDS_REVIEW / SECONDARY_NEEDS_VERIFICATION / STALE / DISCONTINUED / UNKNOWN
    content_hash = Column(String(64), nullable=True)  # SHA-256 of source content
    raw_source_snapshot_path = Column(Text, nullable=True)
    data_version = Column(Integer, default=1)
    data_quality_score = Column(Integer, default=0)  # 0–100 automated quality indicator

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    eligibility_rules = relationship("SchemeEligibilityRule", back_populates="scheme", cascade="all, delete-orphan")
    benefits = relationship("SchemeBenefit", back_populates="scheme", cascade="all, delete-orphan")
    documents = relationship("SchemeDocument", back_populates="scheme", cascade="all, delete-orphan")
    locations = relationship("SchemeLocation", back_populates="scheme", cascade="all, delete-orphan")
    sources = relationship("SchemeSource", back_populates="scheme", cascade="all, delete-orphan")
    versions = relationship("SchemeVersion", back_populates="scheme", cascade="all, delete-orphan")
    embeddings = relationship("SchemeEmbedding", back_populates="scheme", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_schemes_status", "status"),
        Index("ix_schemes_government_level", "government_level"),
        Index("ix_schemes_verification_status", "verification_status"),
        Index("ix_schemes_ministry", "ministry"),
    )


class SchemeEligibilityRule(Base):
    """One row per atomic eligibility rule — enables precise deterministic filtering."""
    __tablename__ = "scheme_eligibility_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id = Column(UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)

    rule_type = Column(String(50), nullable=False)
    # age / gender / social_category / income / state / udyam / disability
    # business_type / occupation / employment / education / startup / farmer / artisan

    operator = Column(String(20), nullable=True)   # gte / lte / eq / in / not_in / between
    field = Column(String(100), nullable=True)
    value = Column(String(255), nullable=True)      # single value
    value_min = Column(String(100), nullable=True)  # for range rules
    value_max = Column(String(100), nullable=True)
    value_list = Column(ARRAY(String), default=list)  # for IN / not_in rules
    logical_group = Column(String(20), default="AND")  # AND / OR
    required = Column(Boolean, default=True)        # True = hard disqualifier if fails
    source_text = Column(Text, nullable=True)       # original sentence this was extracted from

    scheme = relationship("Scheme", back_populates="eligibility_rules")

    __table_args__ = (
        Index("ix_eligibility_rules_scheme_id_type", "scheme_id", "rule_type"),
    )


class SchemeBenefit(Base):
    """Structured benefit record — one row per distinct benefit."""
    __tablename__ = "scheme_benefits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id = Column(UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)

    benefit_type = Column(String(100), nullable=False)
    # loan / subsidy / grant / interest_subvention / insurance / training /
    # market_linkage / technology / mentoring / other

    amount = Column(Numeric(15, 2), nullable=True)
    percentage = Column(Numeric(5, 2), nullable=True)
    unit = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    conditions = Column(Text, nullable=True)

    scheme = relationship("Scheme", back_populates="benefits")


class SchemeDocument(Base):
    """Required document per scheme — one row per document type."""
    __tablename__ = "scheme_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id = Column(UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)

    document_name = Column(String(255), nullable=False)
    mandatory = Column(Boolean, default=True)
    conditional = Column(Boolean, default=False)
    condition = Column(Text, nullable=True)         # e.g., "required only for SC/ST applicants"
    issuing_authority = Column(String(255), nullable=True)

    scheme = relationship("Scheme", back_populates="documents")


class SchemeLocation(Base):
    """Geographic scope — one row per state/district applicable."""
    __tablename__ = "scheme_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id = Column(UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)

    state_code = Column(String(10), nullable=True)
    state_name = Column(String(100), nullable=True)
    district_code = Column(String(20), nullable=True)
    district_name = Column(String(100), nullable=True)
    geography_type = Column(String(20), default="state")  # state / district / national

    scheme = relationship("Scheme", back_populates="locations")

    __table_args__ = (
        Index("ix_scheme_locations_state", "state_name"),
    )


class SchemeSource(Base):
    """Provenance record — one per fetch event. Multiple sources per scheme allowed."""
    __tablename__ = "scheme_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id = Column(UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)

    source_url = Column(Text, nullable=False)
    source_type = Column(String(50), nullable=True)
    # official_portal / api / ministry_page / open_data / news / manual

    publisher = Column(String(255), nullable=True)
    checked_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    content_hash = Column(String(64), nullable=True)
    http_status = Column(Integer, nullable=True)
    authority_level = Column(String(20), default="secondary")  # primary / secondary / unverified

    scheme = relationship("Scheme", back_populates="sources")


class SchemeVersion(Base):
    """Immutable historical snapshot — created on every meaningful change."""
    __tablename__ = "scheme_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id = Column(UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)

    version_number = Column(Integer, nullable=False)
    snapshot = Column(JSONB, nullable=False)   # full serialized scheme at this version
    change_summary = Column(Text, nullable=True)
    changed_by = Column(String(100), default="ingestion_pipeline")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    scheme = relationship("Scheme", back_populates="versions")


class SchemeEmbedding(Base):
    """Vector embedding — separate table for model flexibility."""
    __tablename__ = "scheme_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id = Column(UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)

    embedding_model = Column(String(100), nullable=False)  # e.g., "text-embedding-004", "text-embedding-3-small"
    embedding_dim = Column(Integer, nullable=False)        # 768 / 1536 / etc.
    embedding_text = Column(Text, nullable=True)           # the text that was embedded
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Note: The actual vector column is added by migration (pgvector type)
    # Using raw SQL for the vector column since SQLAlchemy pgvector needs dimension at definition

    scheme = relationship("Scheme", back_populates="embeddings")

    __table_args__ = (
        UniqueConstraint("scheme_id", "embedding_model", name="uq_scheme_embedding_model"),
    )
