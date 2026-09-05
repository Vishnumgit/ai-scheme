from uuid import UUID

from app.api.v1.schemes import DEFAULT_SCHEMES


def test_default_scheme_catalog_has_india_schemes():
    titles = {scheme.title for scheme in DEFAULT_SCHEMES}

    expected = {
        "Stand-Up India Scheme",
        "Prime Minister's Employment Generation Programme (PMEGP)",
        "Pradhan Mantri Mudra Yojana (PMMY)",
        "Pradhan Mantri Vishwakarma Yojana",
        "PM SVANidhi Scheme",
        "Women Entrepreneurship Platform (WEP)"
    }

    assert expected.issubset(titles)
    assert len(DEFAULT_SCHEMES) >= 10


def test_scheme_uuids_are_valid():
    for scheme in DEFAULT_SCHEMES:
        assert isinstance(scheme.id, UUID)
