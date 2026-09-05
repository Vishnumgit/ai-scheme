"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "../components/Navbar";
import { SchemeCard } from "../components/SchemeCard";
import {
  EntrepreneurProfile,
  SchemeMatchResult,
  Scheme,
  matchSchemes,
  fetchAllSchemes,
  fallbackIndiaSchemes
} from "../lib/api";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<"match" | "browse">("match");

  // Profile Matching State
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

  // Browse Catalog State
  const [browseSchemes, setBrowseSchemes] = useState<Scheme[]>([]);
  const [browseLoading, setBrowseLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterSector, setFilterSector] = useState("");
  const [filterState, setFilterState] = useState("");

  const handleMatch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const results = await matchSchemes(profile);
      setMatches(results);
      setHasSearched(true);
    } catch (err) {
      console.error(err);
      setMatches(fallbackIndiaSchemes);
      setHasSearched(true);
    } finally {
      setLoading(false);
    }
  };

  const loadBrowseSchemes = async () => {
    try {
      setBrowseLoading(true);
      const data = await fetchAllSchemes({
        query: searchQuery || undefined,
        category: filterCategory || undefined,
        business_type: filterSector || undefined,
        state: filterState || undefined,
      });
      setBrowseSchemes(data);
    } catch (err) {
      console.error("Browse fetch failed:", err);
    } finally {
      setBrowseLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "browse") {
      loadBrowseSchemes();
    }
  }, [activeTab, filterCategory, filterSector, filterState]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadBrowseSchemes();
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc", fontFamily: "system-ui, sans-serif" }}>
      <Navbar />

      <main style={{ maxWidth: "1150px", margin: "2rem auto", padding: "0 1rem" }}>
        {/* Banner */}
        <section style={{
          background: "linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)",
          color: "#ffffff",
          padding: "2rem",
          borderRadius: "12px",
          marginBottom: "1.5rem"
        }}>
          <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "1.8rem" }}>
            AI-Driven Scheme & Grant Matching
          </h1>
          <p style={{ margin: 0, fontSize: "1.05rem", opacity: 0.9 }}>
            Source-verified government financial aid, subsidies, and credit guarantee programs tailored for marginalized entrepreneurs.
          </p>
        </section>

        {/* Tab Navigation */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem", borderBottom: "1px solid #e2e8f0", paddingBottom: "0.5rem" }}>
          <button
            onClick={() => setActiveTab("match")}
            style={{
              padding: "0.6rem 1.25rem",
              borderRadius: "6px",
              border: "none",
              background: activeTab === "match" ? "#1e3a8a" : "transparent",
              color: activeTab === "match" ? "#ffffff" : "#475569",
              fontWeight: 600,
              cursor: "pointer",
              fontSize: "0.95rem"
            }}
          >
            🎯 Profile Matcher
          </button>
          <button
            onClick={() => setActiveTab("browse")}
            style={{
              padding: "0.6rem 1.25rem",
              borderRadius: "6px",
              border: "none",
              background: activeTab === "browse" ? "#1e3a8a" : "transparent",
              color: activeTab === "browse" ? "#ffffff" : "#475569",
              fontWeight: 600,
              cursor: "pointer",
              fontSize: "0.95rem"
            }}
          >
            📚 Browse & Search All Schemes
          </button>
        </div>

        {/* TAB 1: Profile Matcher */}
        {activeTab === "match" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "2rem" }}>
            {/* Form */}
            <section style={{
              background: "#ffffff",
              padding: "1.5rem",
              borderRadius: "10px",
              border: "1px solid #e2e8f0",
              boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
              height: "fit-content"
            }}>
              <h2 style={{ fontSize: "1.2rem", margin: "0 0 1rem 0", color: "#1e293b" }}>
                Entrepreneur Profile
              </h2>
              <form onSubmit={handleMatch} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "600", color: "#475569", marginBottom: "0.25rem" }}>Full Name</label>
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
                    <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "600", color: "#475569", marginBottom: "0.25rem" }}>Gender</label>
                    <select
                      value={profile.gender}
                      onChange={(e) => setProfile({ ...profile, gender: e.target.value })}
                      style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #cbd5e1" }}
                    >
                      <option value="Female">Female</option>
                      <option value="Male">Male</option>
                      <option value="Transgender">Transgender</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "600", color: "#475569", marginBottom: "0.25rem" }}>Social Category</label>
                    <select
                      value={profile.social_category}
                      onChange={(e) => setProfile({ ...profile, social_category: e.target.value })}
                      style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #cbd5e1" }}
                    >
                      <option value="SC">Scheduled Caste (SC)</option>
                      <option value="ST">Scheduled Tribe (ST)</option>
                      <option value="OBC">Other Backward Class (OBC)</option>
                      <option value="Minority">Minority Community</option>
                      <option value="General">General</option>
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
                    Person with Disability (Divyang / PwD)
                  </label>
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "600", color: "#475569", marginBottom: "0.25rem" }}>Business Sector</label>
                  <select
                    value={profile.business_type}
                    onChange={(e) => setProfile({ ...profile, business_type: e.target.value })}
                    style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #cbd5e1" }}
                  >
                    <option value="Artisan">Handicraft / Artisan / Traditional</option>
                    <option value="Manufacturing">Manufacturing / Food Processing</option>
                    <option value="Service">Service Sector</option>
                    <option value="Trading">Retail / Trading</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "600", color: "#475569", marginBottom: "0.25rem" }}>State</label>
                  <input
                    type="text"
                    value={profile.state || ""}
                    onChange={(e) => setProfile({ ...profile, state: e.target.value })}
                    style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #cbd5e1" }}
                    placeholder="e.g. Telangana, Maharashtra"
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "600", color: "#475569", marginBottom: "0.25rem" }}>Annual Turnover (₹)</label>
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
                    Udyam / MSME Registered
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
                  {loading ? "Matching Schemes with AI..." : "🔍 Find Eligible Schemes"}
                </button>
              </form>
            </section>

            {/* Matches Output */}
            <section>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                <h2 style={{ fontSize: "1.2rem", margin: 0, color: "#1e293b" }}>
                  {hasSearched ? `Recommended Schemes (${matches.length})` : "Matched Schemes"}
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
                  Click <strong>"Find Eligible Schemes"</strong> on the left to evaluate your profile against verified criteria!
                </div>
              )}

              {matches.map((match) => (
                <SchemeCard key={match.scheme.id} match={match} />
              ))}
            </section>
          </div>
        )}

        {/* TAB 2: Browse Catalog */}
        {activeTab === "browse" && (
          <section>
            {/* Search & Filter Bar */}
            <div style={{
              background: "#ffffff",
              padding: "1.5rem",
              borderRadius: "10px",
              border: "1px solid #e2e8f0",
              marginBottom: "1.5rem"
            }}>
              <form onSubmit={handleSearchSubmit} style={{ display: "flex", gap: "1rem", marginBottom: "1rem", flexWrap: "wrap" }}>
                <input
                  type="text"
                  placeholder="Search schemes by name, keyword, or ministry..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ flex: 1, minWidth: "250px", padding: "0.6rem 1rem", borderRadius: "6px", border: "1px solid #cbd5e1" }}
                />
                <button
                  type="submit"
                  style={{
                    background: "#1e3a8a",
                    color: "#ffffff",
                    border: "none",
                    padding: "0.6rem 1.5rem",
                    borderRadius: "6px",
                    fontWeight: 600,
                    cursor: "pointer"
                  }}
                >
                  Search
                </button>
              </form>

              {/* Filter pills */}
              <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
                <select
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                  style={{ padding: "0.4rem 0.8rem", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "0.85rem" }}
                >
                  <option value="">All Social Categories</option>
                  <option value="SC">SC (Scheduled Caste)</option>
                  <option value="ST">ST (Scheduled Tribe)</option>
                  <option value="OBC">OBC</option>
                  <option value="Minority">Minority</option>
                  <option value="Women">Women Focused</option>
                </select>

                <select
                  value={filterSector}
                  onChange={(e) => setFilterSector(e.target.value)}
                  style={{ padding: "0.4rem 0.8rem", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "0.85rem" }}
                >
                  <option value="">All Business Sectors</option>
                  <option value="Artisan">Artisan / Handicraft</option>
                  <option value="Manufacturing">Manufacturing</option>
                  <option value="Service">Service</option>
                  <option value="Trading">Trading</option>
                </select>

                <input
                  type="text"
                  placeholder="Filter by State..."
                  value={filterState}
                  onChange={(e) => setFilterState(e.target.value)}
                  style={{ padding: "0.4rem 0.8rem", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "0.85rem" }}
                />
              </div>
            </div>

            {/* Scheme Catalog Grid */}
            {browseLoading ? (
              <div style={{ textAlign: "center", padding: "3rem", color: "#64748b" }}>Loading verified schemes...</div>
            ) : browseSchemes.length === 0 ? (
              <div style={{
                background: "#ffffff",
                padding: "3rem",
                borderRadius: "10px",
                textAlign: "center",
                color: "#64748b",
                border: "1px solid #e2e8f0"
              }}>
                No schemes match the selected filters. Try broadening your search query.
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "1rem" }}>
                {browseSchemes.map((scheme) => (
                  <div key={scheme.id} style={{
                    background: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "10px",
                    padding: "1.5rem"
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem" }}>
                      <div>
                        <h3 style={{ margin: "0 0 0.25rem 0", color: "#1e293b" }}>{scheme.title}</h3>
                        <span style={{ fontSize: "0.85rem", color: "#64748b" }}>{scheme.ministry_or_org}</span>
                      </div>
                      <span style={{
                        background: "#dcfce7",
                        color: "#15803d",
                        padding: "0.2rem 0.6rem",
                        borderRadius: "12px",
                        fontSize: "0.75rem",
                        fontWeight: 600
                      }}>
                        {scheme.verification_status || "Verified Official"}
                      </span>
                    </div>
                    <p style={{ color: "#334155", fontSize: "0.95rem", lineHeight: 1.5, margin: "0.75rem 0" }}>
                      {scheme.description}
                    </p>
                    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
                      {scheme.target_demographics?.map((d, i) => (
                        <span key={i} style={{ background: "#f1f5f9", padding: "0.2rem 0.5rem", borderRadius: "4px", fontSize: "0.75rem", color: "#475569" }}>
                          {d}
                        </span>
                      ))}
                    </div>
                    {scheme.application_url && (
                      <a
                        href={scheme.application_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          background: "#1e3a8a",
                          color: "#ffffff",
                          padding: "0.45rem 0.9rem",
                          borderRadius: "6px",
                          textDecoration: "none",
                          fontSize: "0.85rem",
                          fontWeight: 600,
                          display: "inline-block"
                        }}
                      >
                        Official Application Portal ↗
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
