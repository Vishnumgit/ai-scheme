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

export interface SchemeBenefitItem {
  benefit_type: string;
  amount?: number;
  percentage?: number;
  unit?: string;
  description?: string;
}

export interface SchemeDocumentItem {
  document_name: string;
  mandatory: boolean;
  conditional: boolean;
  condition?: string;
  issuing_authority?: string;
}

export interface Scheme {
  id: string;
  title: string;
  ministry_or_org: string;
  description: string;
  target_demographics: string[];
  eligible_business_types: string[];
  max_funding_amount?: number;
  subsidy_percentage?: number;
  application_url?: string;
  scheme_code?: string;
  status?: string;
  government_level?: string;
  funding_type?: string;
  states?: string[];
  verification_status?: string;
  verified_at?: string;
  source_name?: string;
  source_url?: string;
  official_source_url?: string;
  data_quality_score?: number;
  benefits?: SchemeBenefitItem[];
  documents?: SchemeDocumentItem[];
}

export interface ScoreBreakdown {
  demographic_score: number;
  business_score: number;
  category_score: number;
  semantic_score: number;
  hard_filter_passed: boolean;
}

export interface SchemeMatchResult {
  scheme: Scheme;
  match_score: number;
  eligibility_status: string;
  ai_reasoning: string;
  key_benefits: string[];
  required_documents: string[];
  score_breakdown?: ScoreBreakdown;
  missing_requirements?: string[];
  matching_factors?: string[];
}

export interface SchemeFilterParams {
  status?: string;
  state?: string;
  category?: string;
  business_type?: string;
  gender?: string;
  query?: string;
  page?: number;
  limit?: number;
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
      application_url: "https://www.standupmitra.in/",
      verification_status: "VERIFIED_OFFICIAL"
    },
    match_score: 95,
    eligibility_status: "Highly Eligible",
    ai_reasoning: "Strong fit for women and SC entrepreneurs with a new business in eligible sectors.",
    key_benefits: ["₹10 Lakh to ₹1 Crore loan support", "Priority banking access", "Greenfield enterprise funding"],
    required_documents: ["Aadhaar", "Caste certificate", "Udyam registration", "Business plan"],
    matching_factors: ["Exclusive allocation for Women & SC/ST", "Priority banking quota"]
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
      application_url: "https://www.kviconline.gov.in/pmegpeportal/",
      verification_status: "VERIFIED_OFFICIAL"
    },
    match_score: 94,
    eligibility_status: "Highly Eligible",
    ai_reasoning: "Excellent alignment with the entrepreneur profile, special-category support, and artisan-focused business.",
    key_benefits: ["Up to 35% subsidy", "Micro-enterprise employment support", "Credit-linked assistance"],
    required_documents: ["Aadhaar", "Project report", "Bank details", "Category certificate if applicable"],
    matching_factors: ["Special category affirmative subsidy", "Artisan sector support"]
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
      application_url: "https://www.mudra.org.in/",
      verification_status: "VERIFIED_OFFICIAL"
    },
    match_score: 90,
    eligibility_status: "Highly Eligible",
    ai_reasoning: "Good profile fit for small business financing and women-led enterprise support.",
    key_benefits: ["Collateral-free loan", "Flexible business funding", "Formal credit support"],
    required_documents: ["Aadhaar", "Bank passbook", "Business details", "Udyam registration"],
    matching_factors: ["Collateral-free credit", "Micro-enterprise priority"]
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
      application_url: "https://pmvishwakarma.gov.in/",
      verification_status: "VERIFIED_OFFICIAL"
    },
    match_score: 88,
    eligibility_status: "Highly Eligible",
    ai_reasoning: "Excellent match for artisan-led or craft-based businesses and marginalized worker communities.",
    key_benefits: ["Toolkit support", "Credit support", "Marketing assistance"],
    required_documents: ["Aadhaar", "Occupation proof", "Bank account", "Artisan certificate if available"],
    matching_factors: ["Direct artisan assistance", "Toolkit incentive"]
  }
];

export async function fetchAllSchemes(params?: SchemeFilterParams): Promise<Scheme[]> {
  const queryParams = new URLSearchParams();
  if (params?.status) queryParams.set("status", params.status);
  if (params?.state) queryParams.set("state", params.state);
  if (params?.category) queryParams.set("category", params.category);
  if (params?.business_type) queryParams.set("business_type", params.business_type);
  if (params?.gender) queryParams.set("gender", params.gender);
  if (params?.query) queryParams.set("query", params.query);
  if (params?.page) queryParams.set("page", params.page.toString());
  if (params?.limit) queryParams.set("limit", params.limit.toString());

  const url = `${API_BASE}/api/v1/schemes${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
  const res = await fetch(url);
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

export async function fetchAdminStats() {
  const res = await fetch(`${API_BASE}/api/v1/admin/stats`);
  if (!res.ok) throw new Error("Failed to fetch admin stats");
  return res.json();
}

export async function triggerSeed() {
  const res = await fetch(`${API_BASE}/api/v1/admin/seed`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to trigger seed");
  return res.json();
}
