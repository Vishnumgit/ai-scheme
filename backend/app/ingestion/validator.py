"""
Validator — validates normalized scheme records before DB insertion.

Checks:
  1. Required fields present
  2. Application URL liveness (optional, async)
  3. Data quality threshold
  4. Status consistency
  5. URL format validation
"""
import logging
import re
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ["name"]
RECOMMENDED_FIELDS = ["description", "ministry", "eligibility_text", "official_application_url", "official_source_url"]

URL_PATTERN = re.compile(
    r"^https?://"
    r"(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,}"
    r"(?::\d+)?"
    r"(?:[/?#]\S*)?$",
    re.IGNORECASE,
)


class ValidationResult:
    __slots__ = ("valid", "errors", "warnings", "scheme_name")

    def __init__(self, scheme_name: str):
        self.scheme_name = scheme_name
        self.valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


def validate_scheme(normalized: Dict[str, Any], min_quality_score: int = 20) -> ValidationResult:
    """
    Validate a normalized scheme dict.
    Returns a ValidationResult with errors (block import) and warnings (allow with flag).
    """
    name = normalized.get("name", "<unnamed>")
    result = ValidationResult(scheme_name=name)

    # ── Required fields ───────────────────────────────────────────────────────
    for field in REQUIRED_FIELDS:
        if not normalized.get(field):
            result.add_error(f"Missing required field: {field}")

    # ── Name length ───────────────────────────────────────────────────────────
    if normalized.get("name") and len(normalized["name"]) < 5:
        result.add_error(f"Scheme name too short: '{normalized['name']}'")

    # ── Status ────────────────────────────────────────────────────────────────
    valid_statuses = {"active", "suspended", "closed", "merged", "discontinued", "unknown"}
    if normalized.get("status") and normalized["status"] not in valid_statuses:
        result.add_warning(f"Unknown status '{normalized['status']}' — will be set to 'unknown'")
        normalized["status"] = "unknown"

    # ── URL format validation ─────────────────────────────────────────────────
    for url_field in ("application_url", "official_application_url", "source_url", "official_source_url"):
        url = normalized.get(url_field)
        if url and not _is_valid_url(url):
            result.add_warning(f"Invalid URL format in {url_field}: {url}")

    # ── Data quality threshold ────────────────────────────────────────────────
    quality = normalized.get("data_quality_score", 0)
    if quality < min_quality_score:
        result.add_error(f"Data quality score {quality} below minimum {min_quality_score}")

    # ── Recommended field warnings ────────────────────────────────────────────
    for field in RECOMMENDED_FIELDS:
        if not normalized.get(field):
            result.add_warning(f"Recommended field missing: {field}")

    # ── Discontinued scheme with no details ───────────────────────────────────
    if normalized.get("status") == "discontinued" and not normalized.get("description"):
        result.add_warning("Discontinued scheme has no description")

    # ── Verification status consistency ───────────────────────────────────────
    if normalized.get("verification_status") == "VERIFIED_OFFICIAL" and not normalized.get("verified_at"):
        result.add_warning("VERIFIED_OFFICIAL but no verified_at timestamp — resetting to OFFICIAL_NEEDS_REVIEW")
        normalized["verification_status"] = "OFFICIAL_NEEDS_REVIEW"

    if result.warnings:
        logger.debug("Scheme '%s' has %d warnings: %s", name, len(result.warnings), result.warnings)
    if not result.valid:
        logger.warning("Scheme '%s' failed validation: %s", name, result.errors)

    return result


def _is_valid_url(url: str) -> bool:
    return bool(URL_PATTERN.match(url))


async def validate_url_liveness(url: str, fetcher) -> Tuple[int, bool]:
    """
    Check if a URL responds with 2xx or 3xx.
    Returns (http_status, is_live).
    """
    try:
        status, _ = await fetcher.check_url_liveness(url)
        return status, 200 <= status < 400
    except Exception as e:
        logger.warning("URL liveness check failed for %s: %s", url, e)
        return 0, False


def batch_validate(
    records: List[Dict[str, Any]],
    min_quality_score: int = 20,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate a batch of normalized records.
    Returns (valid_records, invalid_records).
    """
    valid, invalid = [], []
    for record in records:
        result = validate_scheme(record, min_quality_score)
        if result.valid:
            valid.append(record)
        else:
            invalid.append({**record, "_validation_errors": result.errors})
    logger.info("Batch validation: %d valid, %d invalid out of %d", len(valid), len(invalid), len(records))
    return valid, invalid
