const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface EntrepreneurProfile {
  full_name: string;
  email?: string;
  phone?: string;
  gender: string;
  social_category: string;
  is_differently_abled: boolean;
  business_name?: string;
  business_type: string;
  annual_turnover: number;
  state?: string;
  district?: string;
  is_udyam_registered: boolean;
}

export interface SchemeMatchResult {
  scheme: {
    id: string;
    title: string;
    ministry_or_org: string;
    description: string;
    target_demographics: string[];
    eligible_business_types: string[];
    max_funding_amount?: number;
    subsidy_percentage?: number;
    application_url?: string;
  };
  match_score: number;
  eligibility_status: string;
  ai_reasoning: string;
  key_benefits: string[];
  required_documents: string[];
}

export const fallbackIndiaSchemes: SchemeMatchResult[] = [
  {
    scheme: {
      id: "11111111-1111-1111-1111-111111111111",
      title: "Stand-Up India Scheme",
      ministry_or_org: "Ministry of Finance / SIDBI",
      description: "Bank loans to women and SC/ST entrepreneurs for greenfield enterprise setup.",
      target_demographics: ["Women", "SC", "ST"],
      eligible_business_types: ["Manufacturing", "Service", "Trading"],
      max_funding_amount: 10000000,
      subsidy_percentage: 15,
      application_url: "https://www.standupmitra.in/"
    },
    match_score: 95,
    eligibility_status: "Highly Eligible",
    ai_reasoning: "Strong fit for women and SC entrepreneurs with a new business in eligible sectors.",
    key_benefits: ["₹10 Lakh to ₹1 Crore loan support", "Priority banking access", "Greenfield enterprise funding"],
    required_documents: ["Aadhaar", "Caste certificate", "Udyam registration", "Business plan"]
  },
  {
    scheme: {
      id: "22222222-2222-2222-2222-222222222222",
      title: "Prime Minister's Employment Generation Programme (PMEGP)",
      ministry_or_org: "Ministry of MSME / KVIC",
      description: "Capital subsidy and credit support for micro-enterprise creation and employment generation.",
      target_demographics: ["Women", "SC", "ST", "OBC", "Minority", "Differently-Abled"],
      eligible_business_types: ["Manufacturing", "Service", "Artisan"],
      max_funding_amount: 5000000,
      subsidy_percentage: 35,
      application_url: "https://www.kviconline.gov.in/pmegpeportal/"
    },
    match_score: 94,
    eligibility_status: "Highly Eligible",
    ai_reasoning: "Excellent alignment with the entrepreneur profile, special-category support, and artisan-focused business.",
    key_benefits: ["Up to 35% subsidy", "Micro-enterprise employment support", "Credit-linked assistance"],
    required_documents: ["Aadhaar", "Project report", "Bank details", "Category certificate if applicable"]
  },
  {
    scheme: {
      id: "33333333-3333-3333-3333-333333333333",
      title: "Pradhan Mantri Mudra Yojana (PMMY)",
      ministry_or_org: "Department of Financial Services",
      description: "Collateral-free loan support to micro and small businesses.",
      target_demographics: ["Women", "Minority", "OBC", "SC", "ST"],
      eligible_business_types: ["Manufacturing", "Service", "Trading", "Artisan"],
      max_funding_amount: 1000000,
      subsidy_percentage: 0,
      application_url: "https://www.mudra.org.in/"
    },
    match_score: 90,
    eligibility_status: "Highly Eligible",
    ai_reasoning: "Good profile fit for small business financing and women-led enterprise support.",
    key_benefits: ["Collateral-free loan", "Flexible business funding", "Formal credit support"],
    required_documents: ["Aadhaar", "Bank passbook", "Business details", "Udyam registration"]
  },
  {
    scheme: {
      id: "55555555-5555-5555-5555-555555555555",
      title: "Pradhan Mantri Vishwakarma Yojana",
      ministry_or_org: "Ministry of MSME",
      description: "Support for artisans and craftsmen through toolkits, credit, and marketing assistance.",
      target_demographics: ["Women", "OBC", "SC", "ST"],
      eligible_business_types: ["Artisan", "Manufacturing", "Service"],
      max_funding_amount: 3000000,
      subsidy_percentage: 25,
      application_url: "https://pmvishwakarma.gov.in/"
    },
    match_score: 88,
    eligibility_status: "Highly Eligible",
    ai_reasoning: "Excellent match for artisan-led or craft-based businesses and marginalized worker communities.",
    key_benefits: ["Toolkit support", "Credit support", "Marketing assistance"],
    required_documents: ["Aadhaar", "Occupation proof", "Bank account", "Artisan certificate if available"]
  }
];

export async function fetchAllSchemes() {
  const res = await fetch(`${API_BASE}/api/v1/schemes`);
  if (!res.ok) throw new Error("Failed to fetch schemes");
  return res.json();
}

export async function matchSchemes(profile: EntrepreneurProfile): Promise<SchemeMatchResult[]> {
  const res = await fetch(`${API_BASE}/api/v1/matching/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!res.ok) throw new Error("Failed to match schemes");
  return res.json();
}
