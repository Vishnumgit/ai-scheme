"""
Importer — orchestrates the full ingestion pipeline.

Stages:
  1. Fetch — retrieve content from each enabled source
  2. Parse — extract raw scheme records
  3. Normalize — convert to canonical schema
  4. Validate — check required fields and quality
  5. Deduplicate — remove duplicates (in-batch + vs. existing DB)
  6. Persist — insert new / update changed records
  7. Embed — generate and store embeddings (after successful DB insert)
  8. Version — create scheme_versions snapshot on changes

CLI usage:
  python -m app.ingestion.import_schemes
  python -m app.ingestion.import_schemes --dry-run
  python -m app.ingestion.import_schemes --source msme_ministry --limit 10
  python -m app.ingestion.import_schemes --incremental --category Women
"""
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.models.scheme import (
    Scheme, SchemeEligibilityRule, SchemeBenefit,
    SchemeDocument, SchemeLocation, SchemeSource,
    SchemeVersion, SchemeEmbedding,
)
from app.ingestion.source_registry import get_enabled_sources, get_source
from app.ingestion.fetcher import RateLimitedFetcher
from app.ingestion.parser import parse_source
from app.ingestion.normalizer import normalize_scheme, extract_documents
from app.ingestion.validator import batch_validate
from app.ingestion.deduplicator import Deduplicator, build_existing_keys, check_against_existing
from app.ingestion.embedder import build_embedding_text, generate_embedding, MIN_QUALITY_FOR_EMBEDDING

logger = logging.getLogger(__name__)

# URLs to discover schemes from per source
SOURCE_ENTRY_URLS: Dict[str, List[str]] = {
    "apisetu_myscheme": [
        # Update with actual API Setu endpoint after obtaining credentials
        "https://api.apisetu.gov.in/myscheme/schemes",
    ],
    "india_gov_schemes": [
        "https://www.india.gov.in/government-schemes",
    ],
    "data_gov_in": [
        "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        "?api-key={DATA_GOV_API_KEY}&format=json&limit=500",
    ],
    "msme_ministry": [
        "https://msme.gov.in/government-schemes",
        "https://msme.gov.in/schemes",
    ],
    "mudra_portal": [
        "https://www.mudra.org.in/",
    ],
    "standupmitra": [
        "https://www.standupmitra.in/",
    ],
    "kvic": [
        "https://www.kviconline.gov.in/pmegpeportal/jsp/pmegp.jsp",
    ],
}


class ImportStats:
    def __init__(self):
        self.fetched = 0
        self.parsed = 0
        self.normalized = 0
        self.validated = 0
        self.invalid = 0
        self.duplicates = 0
        self.inserted = 0
        self.updated = 0
        self.skipped = 0
        self.embedded = 0
        self.errors: List[str] = []

    def summary(self) -> str:
        return (
            f"Fetched: {self.fetched} | Parsed: {self.parsed} | Normalized: {self.normalized} | "
            f"Valid: {self.validated} | Invalid: {self.invalid} | Dupes: {self.duplicates} | "
            f"Inserted: {self.inserted} | Updated: {self.updated} | Skipped: {self.skipped} | "
            f"Embedded: {self.embedded} | Errors: {len(self.errors)}"
        )


async def run_ingestion(
    source_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    dry_run: bool = False,
    incremental: bool = True,
    category_filter: Optional[str] = None,
    min_quality: int = 20,
) -> ImportStats:
    """
    Main ingestion entry point.

    Args:
        source_ids: Limit to specific sources (None = all enabled)
        limit: Max records to process (for testing)
        dry_run: Validate without writing to DB
        incremental: Skip records whose content hash hasn't changed
        category_filter: Filter by category keyword
        min_quality: Minimum quality score to import

    Returns:
        ImportStats with counts for each stage
    """
    stats = ImportStats()
    logger.info("Starting ingestion | dry_run=%s | incremental=%s | limit=%s", dry_run, incremental, limit)

    # Determine which sources to use
    if source_ids:
        sources = [get_source(sid) for sid in source_ids]
    else:
        sources = get_enabled_sources()

    fetcher = await RateLimitedFetcher.create()
    deduplicator = Deduplicator()

    try:
        all_normalized: List[Dict[str, Any]] = []

        # ── Stage 1 + 2: Fetch & Parse ────────────────────────────────────────
        for source in sources:
            source_id = next(k for k, v in __import__(
                "app.ingestion.source_registry", fromlist=["SOURCES"]
            ).SOURCES.items() if v is source)

            entry_urls = SOURCE_ENTRY_URLS.get(source_id, [])
            if not entry_urls:
                logger.warning("No entry URLs for source: %s", source_id)
                continue

            for url in entry_urls:
                # Expand env vars in URLs
                url = os.path.expandvars(url)
                logger.info("Fetching %s from %s", source_id, url)

                result = await fetcher.fetch(
                    url=url,
                    source_config=source,
                    check_robots=(source.get("type") == "html"),
                )

                if not result.ok:
                    stats.errors.append(f"Fetch failed {url}: HTTP {result.status} — {result.error}")
                    continue

                if result.content is None:
                    # No change detected (hash match in incremental mode)
                    stats.skipped += 1
                    continue

                stats.fetched += 1

                # ── Stage 2: Parse ────────────────────────────────────────────
                raw_records = parse_source(source_id, result.content, result.content_type, url)
                stats.parsed += len(raw_records)

                # ── Stage 3: Normalize ────────────────────────────────────────
                for raw in raw_records:
                    raw["content_hash"] = result.content_hash
                    normalized = normalize_scheme(raw)
                    if not normalized:
                        continue
                    # Apply category filter
                    if category_filter and not _matches_category(normalized, category_filter):
                        continue
                    all_normalized.append(normalized)
                    stats.normalized += 1

                    if limit and stats.normalized >= limit:
                        logger.info("Reached import limit of %d", limit)
                        break
                if limit and stats.normalized >= limit:
                    break
            if limit and stats.normalized >= limit:
                break

        logger.info("Normalized %d records total", len(all_normalized))

        # ── Stage 4: Validate ─────────────────────────────────────────────────
        valid_records, invalid_records = batch_validate(all_normalized, min_quality_score=min_quality)
        stats.validated = len(valid_records)
        stats.invalid = len(invalid_records)

        if invalid_records:
            logger.warning("Dropped %d invalid records", len(invalid_records))

        # ── Stage 5: Deduplicate (in-batch) ───────────────────────────────────
        unique_records, batch_dupes = deduplicator.process(valid_records)
        stats.duplicates += len(batch_dupes)

        if dry_run:
            logger.info("DRY RUN complete. %s", stats.summary())
            return stats

        # ── Stage 6 + 7 + 8: Persist, Embed, Version ─────────────────────────
        async with AsyncSessionLocal() as session:
            # Load existing dedup keys from DB
            existing = await _load_existing_keys(session)

            for record in unique_records:
                try:
                    existing_key = check_against_existing(record, existing)
                    if existing_key:
                        # Update existing record
                        updated = await _update_scheme(session, record, incremental)
                        if updated:
                            stats.updated += 1
                        else:
                            stats.skipped += 1
                    else:
                        # Insert new record
                        scheme_id = await _insert_scheme(session, record)
                        if scheme_id:
                            stats.inserted += 1
                            existing.add(deduplicator.get_dedup_key(record))

                            # Generate embedding after successful insert
                            if record.get("data_quality_score", 0) >= MIN_QUALITY_FOR_EMBEDDING:
                                embedded = await _generate_and_store_embedding(session, scheme_id, record)
                                if embedded:
                                    stats.embedded += 1
                except Exception as e:
                    logger.error("Error persisting scheme '%s': %s", record.get("name", "?"), e)
                    stats.errors.append(f"Persist error for '{record.get('name')}': {e}")

            await session.commit()

    finally:
        await fetcher.close()

    logger.info("Ingestion complete: %s", stats.summary())
    return stats


async def _load_existing_keys(session: AsyncSession) -> set:
    """Load dedup keys of all existing schemes from DB."""
    from app.ingestion.deduplicator import build_existing_keys, _make_dedup_key
    result = await session.execute(select(Scheme.name, Scheme.ministry, Scheme.scheme_code, Scheme.government_level))
    rows = result.mappings().all()
    return {_make_dedup_key(dict(r)) for r in rows}


async def _insert_scheme(session: AsyncSession, record: Dict[str, Any]) -> Optional[str]:
    """Insert a new scheme and all its child records. Returns the new scheme UUID."""
    import uuid

    now = datetime.now(timezone.utc)
    scheme_id = uuid.uuid4()

    # Build Scheme ORM object
    scheme = Scheme(
        id=scheme_id,
        name=record["name"],
        short_name=record.get("short_name"),
        slug=_ensure_unique_slug(record.get("slug", ""), str(scheme_id)[:8]),
        scheme_code=record.get("scheme_code"),
        status=record.get("status", "active"),
        description=record.get("description"),
        ministry=record.get("ministry"),
        department=record.get("department"),
        implementing_agency=record.get("implementing_agency"),
        funding_type=record.get("funding_type"),
        government_level=record.get("government_level", "central"),
        states=record.get("states", []),
        beneficiary_types=record.get("beneficiary_types", []),
        gender_eligibility=record.get("gender_eligibility", []),
        social_categories=record.get("social_categories", []),
        disability_eligibility=record.get("disability_eligibility", False),
        age_min=record.get("age_min"),
        age_max=record.get("age_max"),
        income_limit=record.get("income_limit"),
        income_limit_period=record.get("income_limit_period"),
        loan_amount_min=record.get("loan_amount_min"),
        loan_amount_max=record.get("loan_amount_max"),
        subsidy_amount=record.get("subsidy_amount"),
        subsidy_percentage=record.get("subsidy_percentage"),
        grant_amount=record.get("grant_amount"),
        interest_subvention=record.get("interest_subvention"),
        collateral_requirement=record.get("collateral_requirement"),
        education_requirements=record.get("education_requirements"),
        business_types=record.get("business_types", []),
        enterprise_size=record.get("enterprise_size"),
        msme_requirements=record.get("msme_requirements", False),
        udyam_required=record.get("udyam_required", False),
        startup_requirements=record.get("startup_requirements", False),
        farmer_requirements=record.get("farmer_requirements", False),
        artisan_requirements=record.get("artisan_requirements", False),
        student_requirements=record.get("student_requirements", False),
        eligibility_rules_json=record.get("eligibility_rules_json", []),
        eligibility_text=record.get("eligibility_text"),
        benefits_structured_json=record.get("benefits_structured_json", []),
        benefits_text=record.get("benefits_text"),
        financial_benefit=record.get("financial_benefit", False),
        application_url=record.get("application_url"),
        official_application_url=record.get("official_application_url"),
        application_steps=record.get("application_steps"),
        source_name=record.get("source_name"),
        source_url=record.get("source_url"),
        official_source_url=record.get("official_source_url"),
        source_type=record.get("source_type"),
        source_last_checked_at=now,
        verification_status=record.get("verification_status", "UNKNOWN"),
        content_hash=record.get("content_hash"),
        data_quality_score=record.get("data_quality_score", 0),
        created_at=now,
        updated_at=now,
    )
    session.add(scheme)
    await session.flush()  # get the ID without committing

    # Insert eligibility rules
    for rule in record.get("eligibility_rules_json", []):
        session.add(SchemeEligibilityRule(
            scheme_id=scheme_id,
            rule_type=rule.get("rule_type", ""),
            operator=rule.get("operator"),
            field=rule.get("field"),
            value=rule.get("value"),
            value_min=rule.get("value_min"),
            value_max=rule.get("value_max"),
            value_list=rule.get("value_list", []),
            logical_group=rule.get("logical_group", "AND"),
            required=rule.get("required", True),
            source_text=rule.get("source_text"),
        ))

    # Insert benefits
    for benefit in record.get("benefits_structured_json", []):
        session.add(SchemeBenefit(
            scheme_id=scheme_id,
            benefit_type=benefit.get("benefit_type", ""),
            amount=benefit.get("amount"),
            percentage=benefit.get("percentage"),
            description=benefit.get("description"),
        ))

    # Insert documents
    for doc in extract_documents({}, record):
        session.add(SchemeDocument(
            scheme_id=scheme_id,
            document_name=doc.get("document_name", ""),
            mandatory=doc.get("mandatory", True),
            conditional=doc.get("conditional", False),
            condition=doc.get("condition"),
        ))

    # Insert source provenance
    session.add(SchemeSource(
        scheme_id=scheme_id,
        source_url=record.get("source_url") or record.get("official_source_url") or "",
        source_type=record.get("source_type"),
        publisher=record.get("source_name"),
        checked_at=now,
        content_hash=record.get("content_hash"),
        http_status=200,
        authority_level="primary" if record.get("source_type") == "api" else "secondary",
    ))

    # Initial version snapshot
    session.add(SchemeVersion(
        scheme_id=scheme_id,
        version_number=1,
        snapshot=_make_snapshot(record),
        change_summary="Initial import",
        changed_by="ingestion_pipeline",
        created_at=now,
    ))

    logger.debug("Inserted scheme: %s (id=%s)", record["name"], scheme_id)
    return str(scheme_id)


async def _update_scheme(session: AsyncSession, record: Dict[str, Any], incremental: bool) -> bool:
    """Update an existing scheme if content has changed."""
    # In incremental mode, skip if hash matches
    # Full implementation: query DB for existing hash, compare, then update
    # For MVP: always update changed fields
    logger.debug("Updating scheme: %s", record.get("name"))
    # Simplified — full implementation would compare content_hash
    return True


async def _generate_and_store_embedding(
    session: AsyncSession, scheme_id: str, record: Dict[str, Any]
) -> bool:
    """Generate embedding and store in scheme_embeddings table."""
    import uuid
    embedding_text = build_embedding_text(record)
    embedding, dim, model_name = await generate_embedding(embedding_text)

    if embedding is None:
        return False

    # Choose correct column based on dimension
    emb_obj = SchemeEmbedding(
        id=uuid.uuid4(),
        scheme_id=uuid.UUID(scheme_id),
        embedding_model=model_name,
        embedding_dim=dim,
        embedding_text=embedding_text[:2000],
    )
    session.add(emb_obj)

    # Store vector via raw SQL (pgvector type not directly handled by ORM column here)
    col = "embedding_768" if dim == 768 else "embedding_1536"
    await session.execute(
        f"UPDATE scheme_embeddings SET {col} = :vec WHERE scheme_id = :sid AND embedding_model = :model",
        {"vec": str(embedding), "sid": scheme_id, "model": model_name}
    )

    logger.debug("Stored %d-dim embedding for scheme_id=%s", dim, scheme_id)
    return True


def _ensure_unique_slug(slug: str, suffix: str) -> str:
    """Append a suffix to make slug unique if needed."""
    if not slug:
        return suffix
    return f"{slug[:180]}-{suffix}"


def _make_snapshot(record: Dict[str, Any]) -> Dict:
    """Create a serializable snapshot dict for scheme_versions."""
    exclude_keys = {"_raw", "_source_id"}
    return {k: v for k, v in record.items() if k not in exclude_keys and isinstance(v, (str, int, float, bool, list, dict, type(None)))}


def _matches_category(record: Dict[str, Any], category_filter: str) -> bool:
    """Check if a record matches a category filter string."""
    cf = category_filter.lower()
    text = " ".join([
        record.get("name", ""),
        record.get("ministry", ""),
        record.get("description", "")[:200],
        " ".join(record.get("business_types", [])),
        " ".join(record.get("social_categories", [])),
    ]).lower()
    return cf in text


# ─────────────────────────────────────────────────────────────────────────────
# Seed loader — loads the 4 default schemes for demo/testing
# ─────────────────────────────────────────────────────────────────────────────

async def load_seed_schemes(dry_run: bool = False) -> int:
    """
    Load seed schemes from data/seed/seed_schemes.json.
    Used only for testing and demo purposes.
    Returns number of schemes loaded.
    """
    seed_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "seed", "seed_schemes.json")
    seed_path = os.path.normpath(seed_path)

    if not os.path.exists(seed_path):
        logger.warning("Seed file not found: %s", seed_path)
        return 0

    with open(seed_path, "r", encoding="utf-8") as f:
        seed_records = json.load(f)

    logger.info("Loading %d seed schemes", len(seed_records))

    if dry_run:
        logger.info("DRY RUN — seed schemes would be loaded: %s", [r["name"] for r in seed_records])
        return len(seed_records)

    async with AsyncSessionLocal() as session:
        for record in seed_records:
            # Normalize seed record to canonical format
            normalized = {
                "name": record["name"],
                "scheme_code": record.get("scheme_code"),
                "ministry": record.get("ministry"),
                "department": record.get("department"),
                "implementing_agency": record.get("implementing_agency"),
                "government_level": record.get("government_level", "central"),
                "funding_type": record.get("funding_type"),
                "description": record.get("description", ""),
                "eligibility_text": record.get("eligibility_text", ""),
                "social_categories": record.get("social_categories", []),
                "gender_eligibility": record.get("gender_eligibility", []),
                "disability_eligibility": record.get("disability_eligibility", False),
                "loan_amount_max": record.get("loan_amount_max"),
                "subsidy_percentage": record.get("subsidy_percentage"),
                "grant_amount": record.get("grant_amount"),
                "udyam_required": record.get("udyam_required", False),
                "startup_requirements": record.get("startup_requirements", False),
                "business_types": record.get("eligible_business_types", []),
                "application_url": record.get("application_url"),
                "official_application_url": record.get("official_application_url"),
                "source_name": record.get("source_name"),
                "source_url": record.get("source_url"),
                "official_source_url": record.get("official_source_url"),
                "source_type": record.get("source_type", "official_portal"),
                "verification_status": record.get("verification_status", "OFFICIAL_NEEDS_REVIEW"),
                "data_quality_score": 70,  # seed data gets decent quality score
                "is_seed": True,
            }
            normalized["eligibility_rules_json"] = []
            normalized["benefits_structured_json"] = []
            normalized["financial_benefit"] = bool(record.get("loan_amount_max") or record.get("subsidy_percentage"))
            await _insert_scheme(session, normalized)
        await session.commit()

    logger.info("Seed schemes loaded successfully")
    return len(seed_records)
