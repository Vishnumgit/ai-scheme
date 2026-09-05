from fastapi import APIRouter, HTTPException
from typing import List
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime

from app.schemas.scheme import SchemeResponse, SchemeCreate

router = APIRouter()

# Default curated schemes for marginalized entrepreneurs and broad India-focused support
DEFAULT_SCHEMES: List[SchemeResponse] = [
    SchemeResponse(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        title="Stand-Up India Scheme",
        ministry_or_org="Ministry of Finance / SIDBI",
        description="Facilitates bank loans between 10 lakh and 1 crore to at least one Scheduled Caste (SC) or Scheduled Tribe (ST) borrower and at least one woman borrower per bank branch for setting up a greenfield enterprise.",
        target_demographics=["Women", "SC", "ST"],
        eligible_business_types=["Manufacturing", "Service", "Trading"],
        max_funding_amount=Decimal("10000000.00"),
        subsidy_percentage=Decimal("15.00"),
        application_url="https://www.standupmitra.in/",
        eligibility_criteria={"requires_udyam": True, "min_age": 18, "greenfield_only": True},
        created_at=datetime.utcnow()
    ),
    SchemeResponse(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        title="Prime Minister's Employment Generation Programme (PMEGP)",
        ministry_or_org="Ministry of MSME / KVIC",
        description="Credit-linked subsidy scheme generating employment opportunities through establishment of micro-enterprises in rural and urban areas. Higher subsidy rate of up to 35% for Special Category beneficiaries (SC/ST/OBC/Minorities/Women/Differently-abled).",
        target_demographics=["Women", "SC", "ST", "OBC", "Minority", "Differently-Abled"],
        eligible_business_types=["Manufacturing", "Service", "Artisan"],
        max_funding_amount=Decimal("5000000.00"),
        subsidy_percentage=Decimal("35.00"),
        application_url="https://www.kviconline.gov.in/pmegpeportal/",
        eligibility_criteria={"requires_udyam": False, "min_age": 18, "education_min": "8th Pass for >10L Mfg"},
        created_at=datetime.utcnow()
    ),
    SchemeResponse(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        title="Pradhan Mantri Mudra Yojana (PMMY)",
        ministry_or_org="Department of Financial Services",
        description="Provides collateral-free institutional credit up to 10 Lakhs to micro and small business units. Special emphasis on women entrepreneurs, minority-owned enterprises, and first-time business founders.",
        target_demographics=["Women", "Minority", "OBC", "SC", "ST"],
        eligible_business_types=["Manufacturing", "Service", "Trading", "Artisan"],
        max_funding_amount=Decimal("1000000.00"),
        subsidy_percentage=Decimal("0.00"),
        application_url="https://www.mudra.org.in/",
        eligibility_criteria={"requires_udyam": False, "collateral_free": True},
        created_at=datetime.utcnow()
    ),
    SchemeResponse(
        id=UUID("44444444-4444-4444-4444-444444444444"),
        title="Ambedkar Social Innovation and Incubation Mission (ASIIM)",
        ministry_or_org="Ministry of Social Justice and Empowerment",
        description="Promotes innovation and enterprise among SC youth with special preference to Divyangs and women entrepreneurs by supporting innovative technology startups with equity funding up to 30 lakhs over 3 years.",
        target_demographics=["SC", "Differently-Abled", "Women"],
        eligible_business_types=["Manufacturing", "Service"],
        max_funding_amount=Decimal("3000000.00"),
        subsidy_percentage=Decimal("100.00"),
        application_url="https://vcfsc.in/asiim/",
        eligibility_criteria={"requires_udyam": True, "startup_focus": True},
        created_at=datetime.utcnow()
    ),
    SchemeResponse(
        id=UUID("55555555-5555-5555-5555-555555555555"),
        title="Pradhan Mantri Vishwakarma Yojana",
        ministry_or_org="Ministry of MSME",
        description="Provides end-to-end support to artisans and craftspeople including toolkit incentive, credit support, digital payments, and marketing assistance for traditional occupations.",
        target_demographics=["Women", "OBC", "SC", "ST"],
        eligible_business_types=["Artisan", "Manufacturing", "Service"],
        max_funding_amount=Decimal("3000000.00"),
        subsidy_percentage=Decimal("25.00"),
        application_url="https://pmvishwakarma.gov.in/",
        eligibility_criteria={"requires_udyam": False, "artisan_only": True},
        created_at=datetime.utcnow()
    ),
    SchemeResponse(
        id=UUID("66666666-6666-6666-6666-666666666666"),
        title="Credit Guarantee Fund Trust for MSEs (CGTMSE)",
        ministry_or_org="Ministry of MSME / SIDBI",
        description="Credit guarantee scheme that enables banks to provide collateral-free loans to micro and small enterprises, making credit more accessible to first-generation entrepreneurs.",
        target_demographics=["Women", "SC", "ST", "OBC", "Minority"],
        eligible_business_types=["Manufacturing", "Service", "Trading"],
        max_funding_amount=Decimal("2000000.00"),
        subsidy_percentage=Decimal("0.00"),
        application_url="https://www.cgtmse.in/",
        eligibility_criteria={"requires_udyam": True, "collateral_free": True},
        created_at=datetime.utcnow()
    ),
    SchemeResponse(
        id=UUID("77777777-7777-7777-7777-777777777777"),
        title="MSE-Cluster Development Programme (CDP)",
        ministry_or_org="Ministry of MSME",
        description="Supports cluster-based micro and small enterprises with common facilities, infrastructure, and modernization assistance for women, SC/ST, and artisan clusters.",
        target_demographics=["Women", "SC", "ST", "OBC"],
        eligible_business_types=["Manufacturing", "Artisan", "Service"],
        max_funding_amount=Decimal("5000000.00"),
        subsidy_percentage=Decimal("35.00"),
        application_url="https://msme.gov.in/",
        eligibility_criteria={"requires_udyam": True, "cluster_based": True},
        created_at=datetime.utcnow()
    ),
    SchemeResponse(
        id=UUID("88888888-8888-8888-8888-888888888888"),
        title="National Handicapped Finance and Development Corporation (NHFDC)",
        ministry_or_org="Department of Empowerment of Persons with Disabilities",
        description="Provides loans and concessional assistance for education, training, and business support to persons with disabilities, including entrepreneurs and self-employed individuals.",
        target_demographics=["Differently-Abled"],
        eligible_business_types=["Manufacturing", "Service", "Trading", "Artisan"],
        max_funding_amount=Decimal("2500000.00"),
        subsidy_percentage=Decimal("20.00"),
        application_url="https://nhfdc.nic.in/",
        eligibility_criteria={"requires_udyam": False, "disability_certificate_required": True},
        created_at=datetime.utcnow()
    ),
    SchemeResponse(
        id=UUID("99999999-9999-9999-9999-999999999999"),
        title="Prime Minister's Formalisation of Micro Food Processing Enterprises (PMFME)",
        ministry_or_org="Ministry of Food Processing Industries",
        description="Supports micro food processing enterprises with credit linked subsidy, common infrastructure, branding, and marketing support for women and rural entrepreneurs.",
        target_demographics=["Women", "Minority", "OBC", "SC", "ST"],
        eligible_business_types=["Manufacturing", "Service"],
        max_funding_amount=Decimal("4000000.00"),
        subsidy_percentage=Decimal("35.00"),
        application_url="https://pmfme.mofpi.gov.in/",
        eligibility_criteria={"requires_udyam": False, "food_processing_focus": True},
        created_at=datetime.utcnow()
    ),
    SchemeResponse(
        id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        title="Startup India Seed Fund Scheme",
        ministry_or_org="Department for Promotion of Industry and Internal Trade",
        description="Provides seed funding to startups that are innovative, scalable, and have the potential to create employment, with a strong push for women-led and community-inclusive entrepreneurship.",
        target_demographics=["Women", "SC", "ST", "OBC", "Minority"],
        eligible_business_types=["Service", "Manufacturing"],
        max_funding_amount=Decimal("7500000.00"),
        subsidy_percentage=Decimal("0.00"),
        application_url="https://www.startupindia.gov.in/",
        eligibility_criteria={"requires_udyam": True, "startup_focus": True},
        created_at=datetime.utcnow()
    ),
    SchemeResponse(
        id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        title="Women Entrepreneurship Platform (WEP)",
        ministry_or_org="Ministry of Women and Child Development / MSME",
        description="Offers mentoring, market access, and support resources for women-owned enterprises across sectors, especially in rural and semi-urban India.",
        target_demographics=["Women"],
        eligible_business_types=["Manufacturing", "Service", "Trading", "Artisan"],
        max_funding_amount=Decimal("1500000.00"),
        subsidy_percentage=Decimal("10.00"),
        application_url="https://wep.gov.in/",
        eligibility_criteria={"requires_udyam": False, "women_led": True},
        created_at=datetime.utcnow()
    ),
    SchemeResponse(
        id=UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        title="PM SVANidhi Scheme",
        ministry_or_org="Ministry of Housing and Urban Affairs",
        description="Supports street vendors including women, SC/ST, and minorities through collateral-free working capital loans and digital empowerment.",
        target_demographics=["Women", "SC", "ST", "Minority", "OBC"],
        eligible_business_types=["Trading", "Service"],
        max_funding_amount=Decimal("1000000.00"),
        subsidy_percentage=Decimal("0.00"),
        application_url="https://www.pmsvanidhi.mohua.gov.in/",
        eligibility_criteria={"requires_udyam": False, "street_vendor_focus": True},
        created_at=datetime.utcnow()
    ),
    SchemeResponse(
        id=UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
        title="Pradhan Mantri Kaushal Vikas Yojana (PMKVY)",
        ministry_or_org="Ministry of Skill Development and Entrepreneurship",
        description="Skill development and entrepreneurship training program for youth and marginalized communities, enabling employability and self-employment support.",
        target_demographics=["Women", "SC", "ST", "OBC", "Minority", "Differently-Abled"],
        eligible_business_types=["Service", "Manufacturing", "Trading"],
        max_funding_amount=Decimal("200000.00"),
        subsidy_percentage=Decimal("100.00"),
        application_url="https://www.msde.gov.in/",
        eligibility_criteria={"requires_udyam": False, "training_program": True},
        created_at=datetime.utcnow()
    )
]


@router.get("", response_model=List[SchemeResponse], tags=["Schemes"])
async def list_schemes():
    """Retrieve all available schemes in the database."""
    return DEFAULT_SCHEMES


@router.get("/{scheme_id}", response_model=SchemeResponse, tags=["Schemes"])
async def get_scheme(scheme_id: UUID):
    """Retrieve details of a specific scheme by UUID."""
    for scheme in DEFAULT_SCHEMES:
        if scheme.id == scheme_id:
            return scheme
    raise HTTPException(status_code=404, detail="Scheme not found")
