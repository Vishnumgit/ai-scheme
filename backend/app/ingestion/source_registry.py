"""
Source Registry — authoritative catalog of data sources for government scheme ingestion.

Each source entry describes:
  - URL and access method (api/html/csv)
  - Rate limits and crawl delay
  - Auth requirements
  - Legal/terms status
  - Coverage (central/state/category)
  - Authority level (primary/secondary)

Rule: Check API Setu and official APIs FIRST.
      HTML scraping is only a fallback under explicit authorization.
"""
from typing import Dict, Any, List

# ─────────────────────────────────────────────────────────────────────────────
# Source definitions
# ─────────────────────────────────────────────────────────────────────────────

SOURCES: Dict[str, Dict[str, Any]] = {
    "apisetu_myscheme": {
        "name": "API Setu — myScheme API",
        "type": "api",
        "base_url": "https://api.apisetu.gov.in",
        "docs_url": "https://docs.apisetu.gov.in/",
        "authority_level": "primary",
        "government_level": ["central", "state"],
        "coverage": "all",
        "auth_method": "api_key",
        "auth_env_key": "APISETU_API_KEY",
        "rate_limit_rps": 2,
        "crawl_delay_s": 0.5,
        "terms_status": "authorized",   # authorized / check_required / restricted / unknown
        "enabled": True,
        "priority": 1,
        "notes": "Check API Setu marketplace first. If myScheme API is available here, use it exclusively.",
    },
    "myscheme_web": {
        "name": "myScheme National Portal",
        "type": "html",
        "base_url": "https://www.myscheme.gov.in",
        "authority_level": "primary",
        "government_level": ["central", "state"],
        "coverage": "all",
        "auth_method": "none",
        "rate_limit_rps": 0.2,   # very conservative — 1 request per 5 seconds
        "crawl_delay_s": 5.0,
        "terms_status": "check_required",  # ToU has access restrictions — verify before use
        "enabled": False,          # DISABLED until terms verified and API Setu checked
        "priority": 2,
        "notes": (
            "myScheme ToU contains access restrictions. "
            "Only enable after: (1) confirming no authorized API exists on API Setu, "
            "(2) reviewing current Terms of Use, (3) confirming access method is permitted."
        ),
    },
    "india_gov_schemes": {
        "name": "India.gov.in — National Portal Government Schemes",
        "type": "html",
        "base_url": "https://www.india.gov.in",
        "schemes_path": "/government-schemes",
        "authority_level": "secondary",
        "government_level": ["central", "state"],
        "coverage": "all",
        "auth_method": "none",
        "rate_limit_rps": 0.5,
        "crawl_delay_s": 2.0,
        "terms_status": "authorized",   # NIC/MeitY public portal — generally permissible for indexing
        "enabled": True,
        "priority": 3,
        "notes": "Use as discovery/validation source. Cross-reference details with responsible ministry pages.",
    },
    "data_gov_in": {
        "name": "data.gov.in — Open Government Data Platform",
        "type": "api",
        "base_url": "https://api.data.gov.in",
        "docs_url": "https://data.gov.in/",
        "authority_level": "secondary",
        "government_level": ["central", "state"],
        "coverage": "structured_datasets",
        "auth_method": "api_key",
        "auth_env_key": "DATA_GOV_API_KEY",
        "rate_limit_rps": 2,
        "crawl_delay_s": 0.5,
        "terms_status": "authorized",   # Government open data platform
        "enabled": True,
        "priority": 3,
        "notes": "Search for scheme/benefit datasets. Not all schemes have structured records here.",
    },
    "national_services_portal": {
        "name": "National Government Services Portal",
        "type": "html",
        "base_url": "https://services.india.gov.in",
        "authority_level": "secondary",
        "government_level": ["central", "state"],
        "coverage": "services",
        "auth_method": "none",
        "rate_limit_rps": 0.5,
        "crawl_delay_s": 2.0,
        "terms_status": "authorized",
        "enabled": True,
        "priority": 4,
        "notes": "Use for identifying official service URLs and responsible departments. Not a primary scheme catalog.",
    },
    # Ministry-specific sources — add as needed per scheme category
    "msme_ministry": {
        "name": "Ministry of MSME — Official Portal",
        "type": "html",
        "base_url": "https://msme.gov.in",
        "authority_level": "primary",
        "government_level": ["central"],
        "coverage": "msme",
        "auth_method": "none",
        "rate_limit_rps": 0.5,
        "crawl_delay_s": 2.0,
        "terms_status": "authorized",
        "enabled": True,
        "priority": 2,
        "category_filter": ["MSME", "Artisan", "Startup"],
    },
    "mudra_portal": {
        "name": "MUDRA Official Portal",
        "type": "html",
        "base_url": "https://www.mudra.org.in",
        "authority_level": "primary",
        "government_level": ["central"],
        "coverage": "mudra",
        "auth_method": "none",
        "rate_limit_rps": 0.5,
        "crawl_delay_s": 2.0,
        "terms_status": "authorized",
        "enabled": True,
        "priority": 2,
        "category_filter": ["MSME", "Finance"],
    },
    "standupmitra": {
        "name": "Stand-Up India — StandUp Mitra Portal",
        "type": "html",
        "base_url": "https://www.standupmitra.in",
        "authority_level": "primary",
        "government_level": ["central"],
        "coverage": "standup_india",
        "auth_method": "none",
        "rate_limit_rps": 0.5,
        "crawl_delay_s": 2.0,
        "terms_status": "authorized",
        "enabled": True,
        "priority": 2,
        "category_filter": ["SC/ST", "Women", "Finance"],
    },
    "kvic": {
        "name": "KVIC — PMEGP Portal",
        "type": "html",
        "base_url": "https://www.kviconline.gov.in",
        "authority_level": "primary",
        "government_level": ["central"],
        "coverage": "pmegp",
        "auth_method": "none",
        "rate_limit_rps": 0.5,
        "crawl_delay_s": 2.0,
        "terms_status": "authorized",
        "enabled": True,
        "priority": 2,
        "category_filter": ["MSME", "Artisan", "Employment"],
    },
}


def get_enabled_sources(priority_max: int = 10) -> List[Dict[str, Any]]:
    """Return enabled sources ordered by priority."""
    return sorted(
        [s for s in SOURCES.values() if s.get("enabled", False) and s.get("priority", 99) <= priority_max],
        key=lambda x: x["priority"]
    )


def get_source(source_id: str) -> Dict[str, Any]:
    """Get source configuration by ID."""
    if source_id not in SOURCES:
        raise ValueError(f"Unknown source: {source_id}. Available: {list(SOURCES.keys())}")
    return SOURCES[source_id]


def get_api_sources() -> List[Dict[str, Any]]:
    """Return only API-type sources (preferred over HTML scraping)."""
    return [s for s in SOURCES.values() if s.get("enabled") and s.get("type") == "api"]
