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
