"""
001 - Create normalized scheme tables

Revision ID: 001_scheme_tables
Revises: 
Create Date: 2026-09-05

Replaces the original flat `schemes` table with a fully normalized,
source-verified, versioned schema. Enables:
  - Deterministic eligibility rule evaluation
  - Structured benefits/documents/locations
  - Full provenance (source URL, content hash, verification status, timestamps)
  - Immutable version history
  - pgvector embeddings in a separate table for model flexibility
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_scheme_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensions ────────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

    # ── Rename old schemes table if it exists (preserve legacy data) ──────────
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'schemes'
            ) THEN
                ALTER TABLE schemes RENAME TO schemes_legacy;
            END IF;
        END $$;
    """)

    # ── schemes (canonical) ───────────────────────────────────────────────────
    op.create_table(
        "schemes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scheme_code", sa.String(100), nullable=True),
        sa.Column("slug", sa.String(255), nullable=True, unique=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("short_name", sa.String(255), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("scheme_version", sa.Integer, server_default="1"),
        sa.Column("status", sa.String(50), server_default="active"),

        # Ownership
        sa.Column("ministry", sa.String(255), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("implementing_agency", sa.String(255), nullable=True),
        sa.Column("funding_type", sa.String(50), nullable=True),
        sa.Column("government_level", sa.String(50), nullable=True),

        # Geography
        sa.Column("states", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("districts", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("rural_urban_scope", sa.String(50), nullable=True),
        sa.Column("geographic_restrictions", sa.Text, nullable=True),

        # Target beneficiaries
        sa.Column("beneficiary_types", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("gender_eligibility", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("social_categories", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("disability_eligibility", sa.Boolean, server_default="false"),
        sa.Column("age_min", sa.Integer, nullable=True),
        sa.Column("age_max", sa.Integer, nullable=True),
        sa.Column("citizenship_requirements", sa.Text, nullable=True),
        sa.Column("residency_requirements", sa.Text, nullable=True),

        # Financial conditions
        sa.Column("income_limit", sa.Numeric(15, 2), nullable=True),
        sa.Column("income_limit_period", sa.String(20), nullable=True),
        sa.Column("income_limit_type", sa.String(50), nullable=True),
        sa.Column("land_holding_limit", sa.String(100), nullable=True),
        sa.Column("loan_amount_min", sa.Numeric(15, 2), nullable=True),
        sa.Column("loan_amount_max", sa.Numeric(15, 2), nullable=True),
        sa.Column("subsidy_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("subsidy_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("grant_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("interest_subvention", sa.Numeric(5, 2), nullable=True),
        sa.Column("collateral_requirement", sa.Boolean, nullable=True),
        sa.Column("margin_money_requirement", sa.Numeric(5, 2), nullable=True),

        # Education / occupation / enterprise
        sa.Column("education_requirements", sa.Text, nullable=True),
        sa.Column("occupation_types", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("employment_status", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("business_types", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("enterprise_size", sa.String(50), nullable=True),
        sa.Column("msme_requirements", sa.Boolean, server_default="false"),
        sa.Column("udyam_required", sa.Boolean, server_default="false"),
        sa.Column("startup_requirements", sa.Boolean, server_default="false"),
        sa.Column("farmer_requirements", sa.Boolean, server_default="false"),
        sa.Column("artisan_requirements", sa.Boolean, server_default="false"),
        sa.Column("student_requirements", sa.Boolean, server_default="false"),

        # Eligibility — machine-readable AND original text
        sa.Column("eligibility_rules_json", postgresql.JSONB, server_default="[]"),
        sa.Column("eligibility_text", sa.Text, nullable=True),
        sa.Column("exclusions", sa.Text, nullable=True),
        sa.Column("priority_groups", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("selection_method", sa.Text, nullable=True),

        # Benefits
        sa.Column("benefits_structured_json", postgresql.JSONB, server_default="[]"),
        sa.Column("benefits_text", sa.Text, nullable=True),
        sa.Column("financial_benefit", sa.Boolean, server_default="false"),
        sa.Column("non_financial_benefits", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("benefit_duration", sa.String(100), nullable=True),
        sa.Column("benefit_coverage", sa.Text, nullable=True),
        sa.Column("benefit_frequency", sa.String(100), nullable=True),

        # Application
        sa.Column("application_mode", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("application_steps", sa.Text, nullable=True),
        sa.Column("application_url", sa.Text, nullable=True),
        sa.Column("official_application_url", sa.Text, nullable=True),
        sa.Column("offline_application_details", sa.Text, nullable=True),
        sa.Column("application_deadline", sa.Text, nullable=True),
        sa.Column("application_window", sa.Text, nullable=True),
        sa.Column("processing_authority", sa.String(255), nullable=True),

        # Provenance — mandatory
        sa.Column("source_name", sa.String(255), nullable=True),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("official_source_url", sa.Text, nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("source_document_url", sa.Text, nullable=True),
        sa.Column("source_last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheme_last_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_status", sa.String(50), server_default="UNKNOWN"),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("raw_source_snapshot_path", sa.Text, nullable=True),
        sa.Column("data_version", sa.Integer, server_default="1"),
        sa.Column("data_quality_score", sa.Integer, server_default="0"),

        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_index("ix_schemes_status", "schemes", ["status"])
    op.create_index("ix_schemes_government_level", "schemes", ["government_level"])
    op.create_index("ix_schemes_verification_status", "schemes", ["verification_status"])
    op.create_index("ix_schemes_ministry", "schemes", ["ministry"])
    op.create_index("ix_schemes_scheme_code", "schemes", ["scheme_code"])

    # ── scheme_eligibility_rules ──────────────────────────────────────────────
    op.create_table(
        "scheme_eligibility_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("operator", sa.String(20), nullable=True),
        sa.Column("field", sa.String(100), nullable=True),
        sa.Column("value", sa.String(255), nullable=True),
        sa.Column("value_min", sa.String(100), nullable=True),
        sa.Column("value_max", sa.String(100), nullable=True),
        sa.Column("value_list", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("logical_group", sa.String(20), server_default="AND"),
        sa.Column("required", sa.Boolean, server_default="true"),
        sa.Column("source_text", sa.Text, nullable=True),
    )
    op.create_index("ix_eligibility_rules_scheme_id", "scheme_eligibility_rules", ["scheme_id"])
    op.create_index("ix_eligibility_rules_scheme_type", "scheme_eligibility_rules", ["scheme_id", "rule_type"])

    # ── scheme_benefits ───────────────────────────────────────────────────────
    op.create_table(
        "scheme_benefits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("benefit_type", sa.String(100), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("conditions", sa.Text, nullable=True),
    )
    op.create_index("ix_scheme_benefits_scheme_id", "scheme_benefits", ["scheme_id"])

    # ── scheme_documents ──────────────────────────────────────────────────────
    op.create_table(
        "scheme_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_name", sa.String(255), nullable=False),
        sa.Column("mandatory", sa.Boolean, server_default="true"),
        sa.Column("conditional", sa.Boolean, server_default="false"),
        sa.Column("condition", sa.Text, nullable=True),
        sa.Column("issuing_authority", sa.String(255), nullable=True),
    )
    op.create_index("ix_scheme_documents_scheme_id", "scheme_documents", ["scheme_id"])

    # ── scheme_locations ──────────────────────────────────────────────────────
    op.create_table(
        "scheme_locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state_code", sa.String(10), nullable=True),
        sa.Column("state_name", sa.String(100), nullable=True),
        sa.Column("district_code", sa.String(20), nullable=True),
        sa.Column("district_name", sa.String(100), nullable=True),
        sa.Column("geography_type", sa.String(20), server_default="state"),
    )
    op.create_index("ix_scheme_locations_scheme_id", "scheme_locations", ["scheme_id"])
    op.create_index("ix_scheme_locations_state", "scheme_locations", ["state_name"])

    # ── scheme_sources ────────────────────────────────────────────────────────
    op.create_table(
        "scheme_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_url", sa.Text, nullable=False),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("publisher", sa.String(255), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("http_status", sa.Integer, nullable=True),
        sa.Column("authority_level", sa.String(20), server_default="secondary"),
    )
    op.create_index("ix_scheme_sources_scheme_id", "scheme_sources", ["scheme_id"])

    # ── scheme_versions ───────────────────────────────────────────────────────
    op.create_table(
        "scheme_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("snapshot", postgresql.JSONB, nullable=False),
        sa.Column("change_summary", sa.Text, nullable=True),
        sa.Column("changed_by", sa.String(100), server_default="ingestion_pipeline"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_scheme_versions_scheme_id", "scheme_versions", ["scheme_id"])

    # ── scheme_embeddings ─────────────────────────────────────────────────────
    op.create_table(
        "scheme_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("embedding_model", sa.String(100), nullable=False),
        sa.Column("embedding_dim", sa.Integer, nullable=False),
        sa.Column("embedding_text", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    # Add vector column with dynamic dimension via raw SQL (supports both 768 and 1536)
    op.execute("ALTER TABLE scheme_embeddings ADD COLUMN IF NOT EXISTS embedding_768 vector(768);")
    op.execute("ALTER TABLE scheme_embeddings ADD COLUMN IF NOT EXISTS embedding_1536 vector(1536);")

    # HNSW indexes for fast cosine similarity search
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_scheme_embeddings_768_hnsw
        ON scheme_embeddings USING hnsw (embedding_768 vector_cosine_ops);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_scheme_embeddings_1536_hnsw
        ON scheme_embeddings USING hnsw (embedding_1536 vector_cosine_ops);
    """)

    op.create_index("ix_scheme_embeddings_scheme_id", "scheme_embeddings", ["scheme_id"])
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_scheme_embedding_model
        ON scheme_embeddings (scheme_id, embedding_model);
    """)

    # ── entrepreneur_profiles (keep existing, add age/income fields) ──────────
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'entrepreneur_profiles'
            ) THEN
                CREATE TABLE entrepreneur_profiles (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    full_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE,
                    phone VARCHAR(50),
                    gender VARCHAR(50),
                    social_category VARCHAR(100),
                    is_differently_abled BOOLEAN DEFAULT FALSE,
                    business_name VARCHAR(255),
                    business_type VARCHAR(100),
                    annual_turnover NUMERIC(15, 2) DEFAULT 0.00,
                    state VARCHAR(100),
                    district VARCHAR(100),
                    is_udyam_registered BOOLEAN DEFAULT FALSE,
                    profile_summary TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            END IF;
        END $$;
    """)
    # Add new fields to entrepreneur_profiles if not present
    op.execute("ALTER TABLE entrepreneur_profiles ADD COLUMN IF NOT EXISTS age INTEGER;")
    op.execute("ALTER TABLE entrepreneur_profiles ADD COLUMN IF NOT EXISTS annual_income NUMERIC(15, 2);")
    op.execute("ALTER TABLE entrepreneur_profiles ADD COLUMN IF NOT EXISTS occupation VARCHAR(100);")
    op.execute("ALTER TABLE entrepreneur_profiles ADD COLUMN IF NOT EXISTS is_farmer BOOLEAN DEFAULT FALSE;")
    op.execute("ALTER TABLE entrepreneur_profiles ADD COLUMN IF NOT EXISTS is_student BOOLEAN DEFAULT FALSE;")
    op.execute("ALTER TABLE entrepreneur_profiles ADD COLUMN IF NOT EXISTS enterprise_size VARCHAR(50);")
    op.execute("ALTER TABLE entrepreneur_profiles ADD COLUMN IF NOT EXISTS profile_text TEXT;")

    # ── scheme_matches (keep existing) ────────────────────────────────────────
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'scheme_matches'
            ) THEN
                CREATE TABLE scheme_matches (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    entrepreneur_id UUID REFERENCES entrepreneur_profiles(id),
                    scheme_id UUID REFERENCES schemes(id),
                    match_score NUMERIC(5, 2) NOT NULL,
                    eligibility_status VARCHAR(50) DEFAULT 'Eligible',
                    ai_reasoning TEXT,
                    status VARCHAR(50) DEFAULT 'Recommended',
                    match_breakdown JSONB DEFAULT '{}',
                    missing_requirements TEXT[],
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            END IF;
        END $$;
    """)
    op.execute("ALTER TABLE scheme_matches ADD COLUMN IF NOT EXISTS match_breakdown JSONB DEFAULT '{}';")
    op.execute("ALTER TABLE scheme_matches ADD COLUMN IF NOT EXISTS missing_requirements TEXT[] DEFAULT '{}';")


def downgrade() -> None:
    op.drop_table("scheme_matches")
    op.drop_table("scheme_embeddings")
    op.drop_table("scheme_versions")
    op.drop_table("scheme_sources")
    op.drop_table("scheme_locations")
    op.drop_table("scheme_documents")
    op.drop_table("scheme_benefits")
    op.drop_table("scheme_eligibility_rules")
    op.drop_table("schemes")
    op.drop_table("entrepreneur_profiles")
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'schemes_legacy'
            ) THEN
                ALTER TABLE schemes_legacy RENAME TO schemes;
            END IF;
        END $$;
    """)
