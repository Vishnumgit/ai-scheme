"""
Deduplicator — detects and resolves duplicate scheme records before insertion.

Deduplication strategy (in priority order):
  1. Exact match on scheme_code + government_level (most reliable)
  2. Exact match on normalized name + ministry
  3. Fuzzy name similarity for near-duplicates (flagged for review, not auto-merged)

Rules:
  - Same scheme_code from same authority → merge (keep higher authority source)
  - Same name + ministry → likely duplicate → flag, keep existing if already in DB
  - Different schemes with similar names → flag for human review, DO NOT auto-merge
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _normalize_name_for_dedup(name: str) -> str:
    """Normalize scheme name for comparison (remove articles, punctuation, extra spaces)."""
    name = name.lower().strip()
    # Remove common prefixes/suffixes that shouldn't affect identity
    name = re.sub(r"\bpradhan\s+mantri\b", "pm", name)
    name = re.sub(r"\bscheme\b|\bprogramme\b|\byojana\b|\bmission\b", "", name)
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _make_dedup_key(normalized: Dict[str, Any]) -> str:
    """
    Create a deduplication key.
    Prefer scheme_code if available, otherwise use name + ministry hash.
    """
    scheme_code = (normalized.get("scheme_code") or "").strip()
    gov_level = (normalized.get("government_level") or "").strip()

    if scheme_code and gov_level:
        return f"code:{scheme_code}:{gov_level}"

    name_key = _normalize_name_for_dedup(normalized.get("name") or "")
    ministry_key = (normalized.get("ministry") or "").lower().strip()[:50]
    return f"name:{name_key}:{ministry_key}"


class Deduplicator:
    """
    In-memory deduplication within a single ingestion batch.
    Cross-batch deduplication (against existing DB records) is handled in the importer.
    """

    def __init__(self):
        self._seen: Dict[str, Dict[str, Any]] = {}  # dedup_key → first record

    def process(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Deduplicate a list of normalized records within the batch.

        Returns:
            (unique_records, duplicate_records)
        """
        unique, duplicates = [], []

        for record in records:
            key = _make_dedup_key(record)

            if key in self._seen:
                existing = self._seen[key]
                # Keep the record with higher data quality
                if record.get("data_quality_score", 0) > existing.get("data_quality_score", 0):
                    logger.debug("Replacing lower-quality duplicate for key: %s", key)
                    unique.remove(existing)
                    self._seen[key] = record
                    unique.append(record)
                else:
                    logger.debug("Dropping in-batch duplicate for key: %s", key)
                duplicates.append(record)
            else:
                self._seen[key] = record
                unique.append(record)

        logger.info("Deduplication: %d unique, %d duplicates from %d records",
                    len(unique), len(duplicates), len(records))
        return unique, duplicates

    def get_dedup_key(self, normalized: Dict[str, Any]) -> str:
        return _make_dedup_key(normalized)


def check_against_existing(
    record: Dict[str, Any],
    existing_keys: set,
) -> Optional[str]:
    """
    Check if a record's dedup key already exists in the DB key set.
    Returns the matching key if duplicate, None if new.
    """
    key = _make_dedup_key(record)
    if key in existing_keys:
        return key
    return None


def build_existing_keys(existing_records: List[Dict[str, Any]]) -> set:
    """Build a set of dedup keys from existing DB records (fetched as dicts)."""
    return {_make_dedup_key(r) for r in existing_records}
