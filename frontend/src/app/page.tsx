"use client";

import React, { useState } from "react";
import { Navbar } from "../components/Navbar";
import { SchemeCard } from "../components/SchemeCard";
import { EntrepreneurProfile, SchemeMatchResult, matchSchemes } from "../lib/api";
import { Language, translations } from "../lib/i18n";

export default function HomePage() {
  const [language, setLanguage] = useState<Language>("en");
  const t = translations[language];
  const [profile, setProfile] = useState<EntrepreneurProfile>({
    full_name: "Anita Sharma",
    email: "anita.sharma@example.com",
    phone: "+91 9876543210",
    gender: "Female",
    social_category: "SC",
    is_differently_abled: false,
    business_name: "Shakti Handicrafts & Textiles",
    business_type: "Artisan",
    annual_turnover: 350000,
    state: "Telangana",
    district: "Warangal",
    is_udyam_registered: true,
  });

  const [matches, setMatches] = useState<SchemeMatchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleMatch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const results = await matchSchemes(profile);
      setMatches(results);
      setHasSearched(true);
    } catch (err) {
      console.error(err);
      // Fallback offline sample data if backend isn't started yet
      setMatches([
        {
          scheme: {
            id: "22222222-2222-2222-2222-222222222222",
            title: "Prime Minister's Employment Generation Programme (PMEGP)",
            ministry_or_org: "Ministry of MSME / KVIC",
            description: "Credit-linked subsidy scheme generating micro-enterprise employment. Up to 35% capital subsidy for Special Category (Women / SC / ST / Minorities / Differently-Abled).",
            target_demographics: ["Women", "SC", "ST", "OBC", "Minority", "Differently-Abled"],
            eligible_business_types: ["Manufacturing", "Service", "Artisan"],
            max_funding_amount: 5000000,
            subsidy_percentage: 35,
            application_url: "https://www.kviconline.gov.in/pmegpeportal/"
          },
          match_score: 95.0,
          eligibility_status: "Highly Eligible",
          ai_reasoning: "Exceptional alignment: Applicant qualifies for special category subsidy benefits as a Woman and SC artisan entrepreneur.",
          key_benefits: ["Government Capital Subsidy up to 35%", "Loan limit up to ₹50,00,000", "Collateral-free credit support"],
          required_documents: ["Aadhaar Card", "Bank Passbook", "SC Community Certificate", "Udyam Registration Certificate"]
        },
        {
          scheme: {
            id: "11111111-1111-1111-1111-111111111111",
            title: "Stand-Up India Scheme",
            ministry_or_org: "Ministry of Finance / SIDBI",
            description: "Bank loans between 10 Lakhs and 1 Crore to at least one SC/ST and at least one woman borrower per branch.",
            target_demographics: ["Women", "SC", "ST"],
            eligible_business_types: ["Manufacturing", "Service", "Trading"],
            max_funding_amount: 10000000,
            subsidy_percentage: 15,
            application_url: "https://www.standupmitra.in/"
          },
          match_score: 90.0,
          eligibility_status: "Highly Eligible",
          ai_reasoning: "Direct priority allocation: Guaranteed loan quota reserved specifically for Women and Scheduled Caste founders.",
          key_benefits: ["Loan from ₹10 Lakh to ₹1 Crore", "Margin money support up to 15%", "Working capital overdraft"],
          required_documents: ["Aadhaar Card", "Caste Certificate", "Udyam Registration", "Detailed Project Report"]
        }
      ]);
      setHasSearched(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc", fontFamily: "system-ui, sans-serif" }}>
      <Navbar language={language} onLanguageChange={setLanguage} languageLabel={t.languageLabel} tagline={t.tagline} />

      <main style={{ maxWidth: "1100px", margin: "2rem auto", padding: "0 1rem" }}>
        {/* Banner */}
        <section style={{
          background: "linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)",
          color: "#ffffff",
          padding: "2rem",
          borderRadius: "12px",
          marginBottom: "2rem"
        }}>
          <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "1.8rem" }}>
            {t.heroTitle}
          </h1>
          <p style={{ margin: 0, fontSize: "1.05rem", opacity: 0.9 }}>
            {t.heroDescription}
          </p>
        </section>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.6fr", gap: "2rem" }}>
          {/* Profile Form */}
          <section style={{
            background: "#ffffff",
            padding: "1.5rem",
            borderRadius: "10px",
            border: "1px solid #e2e8f0",
            height: "fit-content"
          }}>
            <h2 style={{ fontSize: "1.2rem", marginTop: 0, color: "#1e293b", borderBottom: "2px solid #f1f5f9", paddingBottom: "0.5rem" }}>
              {t.profileTitle}
            </h2>

            <form onSubmit={handleMatch} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "600", color: "#475569", marginBottom: "0.25rem" }}>{t.fullName}</label>
                <input
                  type="text"
                  value={profile.full_name}
                  onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                  style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #cbd5e1" }}
                  required
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "600", color: "#475569", marginBottom: "0.25rem" }}>{t.gender}</label>
                  <select
                    value={profile.gender}
                    onChange={(e) => setProfile({ ...profile, gender: e.target.value })}
                    style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #cbd5e1" }}
                  >
                    <option value="Female">{t.female}</option>
                    <option value="Male">{t.male}</option>
                    <option value="Non-Binary">{t.nonBinary}</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "600", color: "#475569", marginBottom: "0.25rem" }}>{t.socialCategory}</label>
                  <select
                    value={profile.social_category}
                    onChange={(e) => setProfile({ ...profile, social_category: e.target.value })}
                    style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #cbd5e1" }}
                  >
                    <option value="SC">{t.scheduledCaste}</option>
                    <option value="ST">{t.scheduledTribe}</option>
                    <option value="OBC">{t.otherBackwardClass}</option>
                    <option value="Minority">{t.minorityCommunity}</option>
                    <option value="General">{t.general}</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem", fontWeight: "600", color: "#475569" }}>
                  <input
                    type="checkbox"
                    checked={profile.is_differently_abled}
                    onChange={(e) => setProfile({ ...profile, is_differently_abled: e.target.checked })}
                  />
                  {t.disability}
                </label>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "600", color: "#475569", marginBottom: "0.25rem" }}>{t.businessSector}</label>
                <select
                  value={profile.business_type}
                  onChange={(e) => setProfile({ ...profile, business_type: e.target.value })}
                  style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #cbd5e1" }}
                >
                  <option value="Artisan">{t.artisan}</option>
                  <option value="Manufacturing">{t.manufacturing}</option>
                  <option value="Service">{t.service}</option>
                  <option value="Trading">{t.trading}</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "600", color: "#475569", marginBottom: "0.25rem" }}>{t.annualTurnover}</label>
                <input
                  type="number"
                  value={profile.annual_turnover}
                  onChange={(e) => setProfile({ ...profile, annual_turnover: Number(e.target.value) })}
                  style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #cbd5e1" }}
                />
              </div>

              <div>
                <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem", fontWeight: "600", color: "#475569" }}>
                  <input
                    type="checkbox"
                    checked={profile.is_udyam_registered}
                    onChange={(e) => setProfile({ ...profile, is_udyam_registered: e.target.checked })}
                  />
                  {t.udyamRegistered}
                </label>
              </div>

              <button
                type="submit"
                disabled={loading}
                style={{
                  background: "#2563eb",
                  color: "#ffffff",
                  padding: "0.75rem",
                  border: "none",
                  borderRadius: "6px",
                  fontWeight: "bold",
                  cursor: "pointer",
                  marginTop: "0.5rem"
                }}
              >
                {loading ? t.matching : t.findSchemes}
              </button>
            </form>
          </section>

          {/* Matches Output */}
          <section>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <h2 style={{ fontSize: "1.2rem", margin: 0, color: "#1e293b" }}>
                {hasSearched ? `${t.recommendedSchemes} (${matches.length})` : t.matchedSchemes}
              </h2>
            </div>

            {!hasSearched && (
              <div style={{
                background: "#ffffff",
                border: "1px dashed #cbd5e1",
                padding: "3rem 2rem",
                borderRadius: "10px",
                textAlign: "center",
                color: "#64748b"
              }}>
                <span style={{ fontSize: "2.5rem", display: "block", marginBottom: "0.5rem" }}>📋</span>
                {t.emptyState}
              </div>
            )}

            {matches.map((match) => (
              <SchemeCard key={match.scheme.id} match={match} language={language} />
            ))}
          </section>
        </div>
      </main>
    </div>
  );
}
