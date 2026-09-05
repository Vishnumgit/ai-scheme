"""
Normalizer — converts raw parsed scheme dicts into the canonical normalized
scheme record matching the database schema.

Rules:
  1. Original text is NEVER discarded — always preserved in *_text fields.
  2. Structured fields are extracted from text using pattern matching + heuristics.
  3. No LLM calls in this module — pure deterministic normalization.
  4. Every rule extracted from text retains source_text reference.
"""
import re
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Known value mappings
# ─────────────────────────────────────────────────────────────────────────────

GENDER_MAP = {
    "female": "Female", "women": "Female", "woman": "Female", "ladies": "Female",
    "male": "Male", "men": "Male", "man": "Male",
    "any": "Any", "all": "Any",
    "transgender": "Transgender", "trans": "Transgender",
}

SOCIAL_CATEGORY_MAP = {
    "sc": "SC", "scheduled caste": "SC",
    "st": "ST", "scheduled tribe": "ST",
    "obc": "OBC", "other backward class": "OBC", "other backward caste": "OBC",
    "ews": "EWS", "economically weaker section": "EWS",
    "minority": "Minority", "minorities": "Minority",
    "general": "General",
}

BUSINESS_TYPE_MAP = {
    "manufacturing": "Manufacturing",
    "service": "Service", "services": "Service",
    "trading": "Trading", "retail": "Trading", "trade": "Trading",
    "artisan": "Artisan", "craft": "Artisan", "handicraft": "Artisan",
    "agriculture": "Agriculture", "farming": "Agriculture", "farm": "Agriculture",
    "startup": "Startup",
}

STATUS_MAP = {
    "active": "active", "open": "active", "ongoing": "active", "live": "active",
    "closed": "discontinued", "discontinued": "discontinued", "expired": "discontinued",
    "suspended": "suspended", "paused": "suspended",
    "merged": "merged",
}

FUNDING_TYPE_MAP = {
    "central sector": "central_sector",
    "centrally sponsored": "centrally_sponsored",
    "css": "centrally_sponsored",
    "state": "state",
    "local": "local",
}

GOVERNMENT_LEVEL_MAP = {
    "central": "central", "national": "central", "union": "central",
    "state": "state",
    "ut": "union_territory", "union territory": "union_territory",
    "district": "district",
}

# Common Indian rupee amounts
AMOUNT_PATTERN = re.compile(
    r"(?:rs\.?|₹|inr)?\s*"
    r"(\d+(?:\.\d+)?)\s*"
    r"(lakh|lakhs|lac|lacs|crore|crores|cr|thousand|k)?",
    re.IGNORECASE
)

AGE_PATTERN = re.compile(r"(?:age\s+)?(\d+)\s*(?:years?|yrs?)?\s*(?:and\s+)?(?:above|minimum|min)", re.IGNORECASE)
AGE_MAX_PATTERN = re.compile(r"(?:age\s+)?(?:below|maximum|max|up\s+to|upto)\s+(\d+)\s*(?:years?|yrs?)?", re.IGNORECASE)
INCOME_PATTERN = re.compile(
    r"(?:annual\s+)?(?:family\s+)?income\s+(?:of\s+)?(?:not\s+exceeding|up\s+to|below|less\s+than)?\s*"
    r"(?:rs\.?|₹)?\s*(\d+(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs|crore|crores)?",
    re.IGNORECASE
)


# ─────────────────────────────────────────────────────────────────────────────
# Main normalize function
# ─────────────────────────────────────────────────────────────────────────────

def normalize_scheme(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a raw parsed scheme dict into a normalized canonical record.
    Returns a dict matching the Scheme model fields.
    """
    normalized: Dict[str, Any] = {}

    # ── Identity ──────────────────────────────────────────────────────────────
    name = _clean_str(raw.get("name") or raw.get("title") or "")
    if not name:
        logger.warning("Scheme with no name skipped: %s", raw.get("_source_url", "?"))
        return {}

    normalized["name"] = name
    normalized["short_name"] = raw.get("short_name") or _make_short_name(name)
    normalized["slug"] = _make_slug(name)
    normalized["scheme_code"] = _clean_str(raw.get("scheme_code") or raw.get("schemeId"))
    normalized["status"] = STATUS_MAP.get((raw.get("status") or "active").lower(), "active")
    normalized["description"] = _clean_str(raw.get("description") or raw.get("schemeDescription") or "")

    # ── Ownership ─────────────────────────────────────────────────────────────
    normalized["ministry"] = _clean_str(raw.get("ministry") or raw.get("nodal_ministry") or "")
    normalized["department"] = _clean_str(raw.get("department") or "")
    normalized["implementing_agency"] = _clean_str(raw.get("implementing_agency") or raw.get("implementingAgency") or "")
    normalized["funding_type"] = _map_value(raw.get("funding_type", ""), FUNDING_TYPE_MAP, "")
    normalized["government_level"] = _map_value(raw.get("government_level", ""), GOVERNMENT_LEVEL_MAP, "central")

    # ── Geography ─────────────────────────────────────────────────────────────
    normalized["states"] = _extract_list(raw.get("states") or raw.get("state"))
    normalized["rural_urban_scope"] = _parse_rural_urban(raw.get("rural_urban_scope") or normalized["description"])

    # ── Target beneficiaries ──────────────────────────────────────────────────
    normalized["gender_eligibility"] = _extract_gender(
        raw.get("gender_eligibility") or raw.get("gender"),
        raw.get("eligibility_text") or normalized["description"]
    )
    normalized["social_categories"] = _extract_categories(
        raw.get("social_categories") or raw.get("caste"),
        raw.get("eligibility_text") or normalized["description"]
    )
    normalized["disability_eligibility"] = bool(
        raw.get("disability_eligibility") or
        _text_contains(raw.get("eligibility_text", ""), ["pwd", "differently abled", "divyang", "disability"])
    )
    normalized["beneficiary_types"] = _extract_list(raw.get("beneficiary_types") or raw.get("targetBeneficiary"))

    # ── Age extraction ────────────────────────────────────────────────────────
    elig_text = raw.get("eligibility_text") or normalized["description"] or ""
    raw_age_min = raw.get("age_min")
    raw_age_max = raw.get("age_max")
    normalized["age_min"] = int(raw_age_min) if raw_age_min else _extract_age_min(elig_text)
    normalized["age_max"] = int(raw_age_max) if raw_age_max else _extract_age_max(elig_text)

    # ── Financial ─────────────────────────────────────────────────────────────
    normalized["loan_amount_min"] = _parse_amount(raw.get("loan_amount_min"))
    normalized["loan_amount_max"] = _parse_amount(raw.get("loan_amount_max") or raw.get("max_funding_amount"))
    normalized["subsidy_amount"] = _parse_amount(raw.get("subsidy_amount"))
    normalized["subsidy_percentage"] = _parse_float(raw.get("subsidy_percentage"))
    normalized["grant_amount"] = _parse_amount(raw.get("grant_amount"))
    normalized["interest_subvention"] = _parse_float(raw.get("interest_subvention"))
    normalized["collateral_requirement"] = _parse_bool(raw.get("collateral_requirement"))
    raw_income = raw.get("income_limit") or raw.get("annualIncome")
    normalized["income_limit"] = _parse_amount(raw_income) or _extract_income_limit(elig_text)
    normalized["income_limit_period"] = "annual"

    # ── Enterprise ────────────────────────────────────────────────────────────
    normalized["business_types"] = _extract_business_types(
        raw.get("business_types") or raw.get("sector") or raw.get("categories"),
        normalized["description"]
    )
    normalized["udyam_required"] = bool(raw.get("udyam_required") or _text_contains(elig_text, ["udyam"]))
    normalized["startup_requirements"] = bool(raw.get("startup_requirements") or _text_contains(elig_text, ["startup", "incubat"]))
    normalized["farmer_requirements"] = bool(raw.get("farmer_requirements") or _text_contains(elig_text, ["farmer", "kisan", "agriculture"]))
    normalized["artisan_requirements"] = bool(raw.get("artisan_requirements") or _text_contains(elig_text, ["artisan", "handicraft", "craft"]))
    normalized["student_requirements"] = bool(raw.get("student_requirements") or _text_contains(elig_text, ["student", "scholar"]))
    normalized["enterprise_size"] = _clean_str(raw.get("enterprise_size") or "")
    normalized["msme_requirements"] = bool(raw.get("msme_requirements") or _text_contains(elig_text, ["msme", "micro enterprise", "small enterprise"]))

    # ── Eligibility (preserve original text) ─────────────────────────────────
    normalized["eligibility_text"] = _clean_str(elig_text)  # NEVER discard
    normalized["eligibility_rules_json"] = _build_eligibility_rules_json(normalized, elig_text)

    # ── Benefits ──────────────────────────────────────────────────────────────
    benefits_text = raw.get("benefits_text") or raw.get("benefits") or raw.get("schemeDetails") or ""
    normalized["benefits_text"] = _clean_str(benefits_text)  # preserve original
    normalized["financial_benefit"] = bool(normalized["loan_amount_max"] or normalized["subsidy_percentage"] or normalized["grant_amount"])
    normalized["benefits_structured_json"] = _build_benefits_json(normalized)

    # ── Application ───────────────────────────────────────────────────────────
    normalized["application_url"] = _clean_str(raw.get("application_url") or raw.get("applyLink") or "")
    normalized["official_application_url"] = _clean_str(
        raw.get("official_application_url") or normalized["application_url"]
    )
    normalized["application_steps"] = _clean_str(raw.get("application_steps") or raw.get("howToApply") or "")

    # ── Provenance ────────────────────────────────────────────────────────────
    normalized["source_name"] = _clean_str(raw.get("source_name") or raw.get("_source_id") or "")
    normalized["source_url"] = _clean_str(raw.get("source_url") or raw.get("_source_url") or "")
    normalized["official_source_url"] = _clean_str(raw.get("official_source_url") or normalized["source_url"])
    normalized["source_type"] = _clean_str(raw.get("source_type") or "unknown")
    normalized["verification_status"] = "SECONDARY_NEEDS_VERIFICATION"

    # Ministry/official API sources get higher initial status
    if raw.get("source_type") in ("api",) and raw.get("_source_id") in ("apisetu_myscheme", "data_gov_in"):
        normalized["verification_status"] = "OFFICIAL_NEEDS_REVIEW"

    # ── Data quality score ────────────────────────────────────────────────────
    normalized["data_quality_score"] = _compute_quality_score(normalized)

    return normalized


# ─────────────────────────────────────────────────────────────────────────────
# Build structured sub-records
# ─────────────────────────────────────────────────────────────────────────────

def _build_eligibility_rules_json(n: Dict, elig_text: str) -> List[Dict]:
    """Build machine-readable eligibility rules list from normalized fields."""
    rules = []

    if n.get("age_min"):
        rules.append({
            "rule_type": "age", "operator": "gte", "field": "age",
            "value": str(n["age_min"]), "required": True,
            "source_text": f"Extracted from: {elig_text[:200]}"
        })
    if n.get("age_max"):
        rules.append({
            "rule_type": "age", "operator": "lte", "field": "age",
            "value": str(n["age_max"]), "required": True,
            "source_text": f"Extracted from: {elig_text[:200]}"
        })
    if n.get("gender_eligibility") and "Any" not in n["gender_eligibility"]:
        rules.append({
            "rule_type": "gender", "operator": "in", "field": "gender",
            "value_list": n["gender_eligibility"], "required": True,
            "source_text": elig_text[:200]
        })
    if n.get("social_categories"):
        rules.append({
            "rule_type": "social_category", "operator": "in", "field": "social_category",
            "value_list": n["social_categories"], "required": False,  # usually priority, not hard filter
            "source_text": elig_text[:200]
        })
    if n.get("income_limit"):
        rules.append({
            "rule_type": "income", "operator": "lte", "field": "annual_income",
            "value": str(n["income_limit"]), "required": True,
            "source_text": elig_text[:200]
        })
    if n.get("udyam_required"):
        rules.append({
            "rule_type": "udyam", "operator": "eq", "field": "is_udyam_registered",
            "value": "true", "required": False,  # soft requirement — note, not hard exclude
            "source_text": elig_text[:200]
        })
    if n.get("disability_eligibility"):
        rules.append({
            "rule_type": "disability", "operator": "eq", "field": "is_differently_abled",
            "value": "true", "required": False,  # priority, not exclusion
            "source_text": elig_text[:200]
        })
    if n.get("states"):
        rules.append({
            "rule_type": "state", "operator": "in", "field": "state",
            "value_list": n["states"], "required": True,
            "source_text": "Geographic scope"
        })
    if n.get("business_types"):
        rules.append({
            "rule_type": "business_type", "operator": "in", "field": "business_type",
            "value_list": n["business_types"], "required": False,
            "source_text": elig_text[:200]
        })

    return rules


def _build_benefits_json(n: Dict) -> List[Dict]:
    """Build structured benefits list from normalized financial fields."""
    benefits = []
    if n.get("loan_amount_max"):
        benefits.append({
            "benefit_type": "loan",
            "amount": float(n["loan_amount_max"]),
            "description": f"Loan up to ₹{n['loan_amount_max']:,.0f}",
        })
    if n.get("subsidy_percentage"):
        benefits.append({
            "benefit_type": "subsidy",
            "percentage": float(n["subsidy_percentage"]),
            "description": f"Capital subsidy up to {n['subsidy_percentage']}%",
        })
    if n.get("grant_amount"):
        benefits.append({
            "benefit_type": "grant",
            "amount": float(n["grant_amount"]),
            "description": f"Grant of ₹{n['grant_amount']:,.0f}",
        })
    if n.get("interest_subvention"):
        benefits.append({
            "benefit_type": "interest_subvention",
            "percentage": float(n["interest_subvention"]),
            "description": f"Interest subvention of {n['interest_subvention']}%",
        })
    return benefits


def extract_documents(raw: Dict[str, Any], normalized: Dict[str, Any]) -> List[Dict]:
    """
    Extract a standard document list based on eligibility rules.
    Returns list of {document_name, mandatory, conditional, condition} dicts.
    """
    docs = [
        {"document_name": "Aadhaar Card / Government Photo ID", "mandatory": True},
        {"document_name": "Passport-size Photographs", "mandatory": True},
        {"document_name": "Bank Account Details (Passbook / Cancelled Cheque)", "mandatory": True},
        {"document_name": "Project Report / Business Plan", "mandatory": True},
    ]

    cats = normalized.get("social_categories", [])
    if any(c in cats for c in ["SC", "ST", "OBC"]):
        docs.append({
            "document_name": f"Caste / Community Certificate ({'/'.join(cats)})",
            "mandatory": True,
            "condition": "Required for SC/ST/OBC applicants"
        })
    if normalized.get("disability_eligibility"):
        docs.append({
            "document_name": "Disability Certificate (UDID / Medical Board)",
            "mandatory": False, "conditional": True,
            "condition": "Required for PwD/Divyang applicants"
        })
    if normalized.get("udyam_required"):
        docs.append({
            "document_name": "Udyam Registration Certificate",
            "mandatory": True,
            "condition": "Obtain free at udyamregistration.gov.in"
        })
    if normalized.get("startup_requirements"):
        docs.append({"document_name": "Startup Registration / DPIIT Recognition", "mandatory": False, "conditional": True})
    if normalized.get("farmer_requirements"):
        docs.append({"document_name": "Land Records / Khasra-Khatauni", "mandatory": True})
    if normalized.get("income_limit"):
        docs.append({"document_name": "Income Certificate (from competent authority)", "mandatory": True})

    return docs


# ─────────────────────────────────────────────────────────────────────────────
# Extraction helpers
# ─────────────────────────────────────────────────────────────────────────────

def _clean_str(v: Any) -> str:
    if v is None:
        return ""
    return " ".join(str(v).split()).strip()


def _make_slug(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug.strip("-")[:200]


def _make_short_name(name: str) -> str:
    # Extract acronym from parentheses if present, e.g. "PMEGP" from "Prime Minister's... (PMEGP)"
    m = re.search(r"\(([A-Z]{2,10})\)", name)
    if m:
        return m.group(1)
    words = name.split()
    if len(words) > 4:
        return " ".join(words[:4]) + "..."
    return name


def _map_value(raw: str, mapping: Dict[str, str], default: str) -> str:
    raw_lower = raw.lower().strip()
    for key, val in mapping.items():
        if key in raw_lower:
            return val
    return default


def _extract_list(raw: Any) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if x]
    if isinstance(raw, str):
        return [x.strip() for x in re.split(r"[,;/]", raw) if x.strip()]
    return []


def _extract_gender(raw: Any, text: str) -> List[str]:
    found = set()
    raw_list = _extract_list(raw)
    for item in raw_list:
        mapped = GENDER_MAP.get(item.lower())
        if mapped:
            found.add(mapped)
    # Also scan eligibility text
    text_lower = text.lower()
    if "women" in text_lower or "female" in text_lower or "ladies" in text_lower:
        found.add("Female")
    if "male" in text_lower and "female" not in text_lower:
        found.add("Male")
    return list(found) or ["Any"]


def _extract_categories(raw: Any, text: str) -> List[str]:
    found = set()
    raw_list = _extract_list(raw)
    for item in raw_list:
        mapped = SOCIAL_CATEGORY_MAP.get(item.lower())
        if mapped:
            found.add(mapped)
    text_lower = text.lower()
    for key, val in SOCIAL_CATEGORY_MAP.items():
        if key in text_lower:
            found.add(val)
    return list(found)


def _extract_business_types(raw: Any, text: str) -> List[str]:
    found = set()
    raw_list = _extract_list(raw)
    for item in raw_list:
        mapped = BUSINESS_TYPE_MAP.get(item.lower())
        if mapped:
            found.add(mapped)
    text_lower = text.lower()
    for key, val in BUSINESS_TYPE_MAP.items():
        if key in text_lower:
            found.add(val)
    return list(found)


def _text_contains(text: str, keywords: List[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def _parse_bool(v: Any) -> Optional[bool]:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ("true", "yes", "1", "required")
    return bool(v)


def _parse_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_amount(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        m = AMOUNT_PATTERN.search(v)
        if m:
            amount = float(m.group(1))
            unit = (m.group(2) or "").lower()
            if "lakh" in unit or "lac" in unit:
                amount *= 100_000
            elif "crore" in unit or "cr" in unit:
                amount *= 10_000_000
            elif "thousand" in unit or unit == "k":
                amount *= 1_000
            return amount
    return None


def _extract_age_min(text: str) -> Optional[int]:
    m = AGE_PATTERN.search(text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return None


def _extract_age_max(text: str) -> Optional[int]:
    m = AGE_MAX_PATTERN.search(text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return None


def _extract_income_limit(text: str) -> Optional[float]:
    m = INCOME_PATTERN.search(text)
    if m:
        amount = float(m.group(1))
        unit = (m.group(2) or "").lower()
        if "lakh" in unit or "lac" in unit:
            amount *= 100_000
        elif "crore" in unit or "cr" in unit:
            amount *= 10_000_000
        return amount
    return None


def _parse_rural_urban(text: str) -> str:
    text_lower = (text or "").lower()
    if "rural" in text_lower and "urban" in text_lower:
        return "both"
    if "rural" in text_lower:
        return "rural"
    if "urban" in text_lower:
        return "urban"
    return "both"


def _compute_quality_score(n: Dict) -> int:
    """
    Automated data quality score 0–100.
    Penalizes missing critical fields.
    """
    score = 0
    if n.get("name"):
        score += 15
    if n.get("description") and len(n["description"]) > 50:
        score += 15
    if n.get("ministry"):
        score += 10
    if n.get("eligibility_text") and len(n["eligibility_text"]) > 30:
        score += 15
    if n.get("benefits_text") or n.get("benefits_structured_json"):
        score += 10
    if n.get("official_application_url"):
        score += 10
    if n.get("official_source_url"):
        score += 10
    if n.get("age_min") or n.get("social_categories") or n.get("gender_eligibility"):
        score += 10
    if n.get("source_type") == "api":
        score += 5
    return min(score, 100)
