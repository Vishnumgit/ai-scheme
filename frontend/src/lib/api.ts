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
