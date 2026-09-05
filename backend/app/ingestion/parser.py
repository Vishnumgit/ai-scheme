"""
Parser — source-specific parsers that extract raw scheme data
from API JSON responses, HTML pages, or CSV/PDF content.

Each parser returns a list of raw scheme dicts (pre-normalization).
The raw dict uses source field names; normalization happens in normalizer.py.
"""
import json
import logging
from typing import List, Dict, Any, Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Parser registry — maps source_id to parser function
# ─────────────────────────────────────────────────────────────────────────────

def parse_source(source_id: str, content: bytes, content_type: str, url: str) -> List[Dict[str, Any]]:
    """Dispatch to the appropriate parser based on source_id."""
    parsers = {
        "apisetu_myscheme": parse_apisetu_myscheme,
        "myscheme_web": parse_myscheme_html,
        "india_gov_schemes": parse_india_gov_html,
        "data_gov_in": parse_data_gov_api,
        "national_services_portal": parse_india_gov_html,  # same HTML structure
        "msme_ministry": parse_generic_ministry_html,
        "mudra_portal": parse_generic_ministry_html,
        "standupmitra": parse_generic_ministry_html,
        "kvic": parse_generic_ministry_html,
    }
    parser = parsers.get(source_id, parse_generic_json)
    try:
        return parser(content, content_type, url)
    except Exception as e:
        logger.error("Parser error for source %s at %s: %s", source_id, url, e)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# API Setu — myScheme API (preferred, authorized)
# ─────────────────────────────────────────────────────────────────────────────

def parse_apisetu_myscheme(content: bytes, content_type: str, url: str) -> List[Dict[str, Any]]:
    """
    Parse API Setu / myScheme API response.
    Actual field names depend on the API spec — update when API is confirmed.
    This is a template to fill in after API Setu credentials are obtained.
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error("JSON parse error for myScheme API at %s: %s", url, e)
        return []

    # Handle both list and paginated responses
    if isinstance(data, list):
        schemes = data
    elif isinstance(data, dict):
        # Common API pagination patterns
        schemes = (
            data.get("schemes") or
            data.get("data") or
            data.get("results") or
            data.get("items") or
            []
        )
    else:
        schemes = []

    results = []
    for raw in schemes:
        if not isinstance(raw, dict):
            continue
        # Map API Setu / myScheme fields → intermediate raw dict
        # Field names are provisional — update from actual API docs
        results.append({
            "_source_id": "apisetu_myscheme",
            "_source_url": url,
            "_raw": raw,
            "name": raw.get("schemeName") or raw.get("name") or raw.get("title", ""),
            "scheme_code": raw.get("schemeId") or raw.get("scheme_id") or raw.get("id"),
            "description": raw.get("schemeDescription") or raw.get("description", ""),
            "ministry": raw.get("ministry") or raw.get("nodal_ministry", ""),
            "department": raw.get("department", ""),
            "implementing_agency": raw.get("implementingAgency") or raw.get("implementing_agency", ""),
            "government_level": _parse_gov_level(raw.get("level") or raw.get("schemeType", "")),
            "states": _extract_states(raw),
            "beneficiary_types": raw.get("targetBeneficiary") or raw.get("beneficiary", []),
            "gender_eligibility": raw.get("gender") or [],
            "social_categories": raw.get("caste") or raw.get("socialCategory") or [],
            "age_min": raw.get("minAge") or raw.get("ageMin"),
            "age_max": raw.get("maxAge") or raw.get("ageMax"),
            "income_limit": raw.get("annualIncome") or raw.get("incomeLimit"),
            "disability_eligibility": bool(raw.get("disability") or raw.get("pwd")),
            "eligibility_text": raw.get("eligibility") or raw.get("eligibilityCriteria", ""),
            "benefits_text": raw.get("benefits") or raw.get("schemeDetails", ""),
            "application_url": raw.get("applicationUrl") or raw.get("applyLink"),
            "official_application_url": raw.get("officialUrl") or raw.get("applicationUrl"),
            "business_types": raw.get("sector") or raw.get("categories") or [],
            "udyam_required": bool(raw.get("udyamRequired")),
            "status": _parse_status(raw.get("status", "active")),
            "source_type": "api",
        })

    logger.info("Parsed %d schemes from myScheme API at %s", len(results), url)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# myScheme web (HTML — disabled until terms verified)
# ─────────────────────────────────────────────────────────────────────────────

def parse_myscheme_html(content: bytes, content_type: str, url: str) -> List[Dict[str, Any]]:
    """
    Parse myScheme web pages (HTML).
    Only enabled after ToU review and explicit authorization.
    """
    soup = BeautifulSoup(content, "lxml")
    results = []

    # myScheme scheme listing cards — update selectors from actual page structure
    scheme_cards = soup.select("[class*='scheme-card'], [class*='schemeCard'], article[data-scheme]")

    for card in scheme_cards:
        name_el = card.select_one("h2, h3, [class*='scheme-title'], [class*='schemeName']")
        desc_el = card.select_one("p, [class*='description']")
        link_el = card.select_one("a[href]")

        if not name_el:
            continue

        results.append({
            "_source_id": "myscheme_web",
            "_source_url": url,
            "_raw": str(card),
            "name": name_el.get_text(strip=True),
            "description": desc_el.get_text(strip=True) if desc_el else "",
            "application_url": link_el["href"] if link_el else None,
            "source_type": "html",
        })

    logger.info("Parsed %d schemes from myScheme HTML at %s", len(results), url)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# India.gov.in
# ─────────────────────────────────────────────────────────────────────────────

def parse_india_gov_html(content: bytes, content_type: str, url: str) -> List[Dict[str, Any]]:
    """Parse India.gov.in government schemes section."""
    soup = BeautifulSoup(content, "lxml")
    results = []

    # India.gov uses a variety of listing structures — be flexible
    scheme_links = soup.select(
        "ul.scheme-list li a, "
        ".views-row a[href], "
        "div.field-content a[href*='scheme'], "
        "td a[href]"
    )

    for link in scheme_links:
        name = link.get_text(strip=True)
        href = link.get("href", "")
        if not name or len(name) < 5:
            continue

        # Build absolute URL
        if href.startswith("/"):
            from urllib.parse import urlparse as _up
            parsed = _up(url)
            href = f"{parsed.scheme}://{parsed.netloc}{href}"

        results.append({
            "_source_id": "india_gov_schemes",
            "_source_url": url,
            "_raw": str(link.parent),
            "name": name,
            "application_url": href,
            "source_type": "html",
        })

    logger.info("Parsed %d scheme links from India.gov at %s", len(results), url)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# data.gov.in API
# ─────────────────────────────────────────────────────────────────────────────

def parse_data_gov_api(content: bytes, content_type: str, url: str) -> List[Dict[str, Any]]:
    """Parse data.gov.in structured dataset API response."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []

    records = data.get("records") or data.get("data") or []
    results = []

    for rec in records:
        if not isinstance(rec, dict):
            continue
        results.append({
            "_source_id": "data_gov_in",
            "_source_url": url,
            "_raw": rec,
            "name": rec.get("scheme_name") or rec.get("SchemeName") or rec.get("title", ""),
            "ministry": rec.get("ministry") or rec.get("Ministry", ""),
            "description": rec.get("description") or rec.get("Description", ""),
            "benefits_text": rec.get("benefits") or rec.get("Benefits", ""),
            "eligibility_text": rec.get("eligibility") or rec.get("Eligibility", ""),
            "source_type": "api",
        })

    logger.info("Parsed %d records from data.gov.in at %s", len(results), url)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Generic ministry page parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_generic_ministry_html(content: bytes, content_type: str, url: str) -> List[Dict[str, Any]]:
    """
    Generic HTML parser for ministry/department pages.
    Extracts the main content and scheme name from the page title.
    Used when a specific parser doesn't exist.
    """
    soup = BeautifulSoup(content, "lxml")

    title = soup.find("title")
    h1 = soup.find("h1")
    name = (h1 and h1.get_text(strip=True)) or (title and title.get_text(strip=True)) or ""

    # Extract main content block
    main = (
        soup.find("main") or
        soup.find("div", {"id": "content"}) or
        soup.find("div", {"class": "content"}) or
        soup.find("article") or
        soup.body
    )
    description = main.get_text(" ", strip=True)[:2000] if main else ""

    if not name:
        return []

    return [{
        "_source_id": "ministry",
        "_source_url": url,
        "_raw": description[:500],
        "name": name,
        "description": description,
        "application_url": url,
        "official_source_url": url,
        "source_type": "html",
    }]


# ─────────────────────────────────────────────────────────────────────────────
# Generic JSON fallback
# ─────────────────────────────────────────────────────────────────────────────

def parse_generic_json(content: bytes, content_type: str, url: str) -> List[Dict[str, Any]]:
    try:
        data = json.loads(content)
    except Exception:
        return []

    if isinstance(data, list):
        return [{"_source_url": url, "_raw": item, **item} for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return [{"_source_url": url, "_raw": data, **data}]
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_gov_level(raw: str) -> str:
    raw = (raw or "").lower()
    if "central" in raw or "national" in raw or "union" in raw:
        return "central"
    if "state" in raw:
        return "state"
    if "ut" in raw or "union territory" in raw:
        return "union_territory"
    return "central"  # default for unknown


def _parse_status(raw: str) -> str:
    raw = (raw or "").lower()
    if raw in ("active", "open", "ongoing", "live"):
        return "active"
    if raw in ("closed", "discontinued", "expired"):
        return "discontinued"
    if raw in ("suspended", "paused"):
        return "suspended"
    return "active"


def _extract_states(raw: Dict[str, Any]) -> List[str]:
    states_raw = raw.get("state") or raw.get("states") or raw.get("applicableStates") or []
    if isinstance(states_raw, str):
        return [s.strip() for s in states_raw.split(",") if s.strip()]
    if isinstance(states_raw, list):
        return [str(s) for s in states_raw]
    return []
