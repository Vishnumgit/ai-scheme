import React from "react";
import { SchemeMatchResult } from "../lib/api";

export const SchemeCard: React.FC<{ match: SchemeMatchResult }> = ({ match }) => {
  const {
    scheme,
    match_score,
    eligibility_status,
    ai_reasoning,
    key_benefits,
    required_documents,
    score_breakdown,
    matching_factors,
    missing_requirements
  } = match;

  const getStatusColor = (status: string) => {
    if (status === "Highly Eligible") return "#16a34a"; // Green
    if (status === "Eligible") return "#2563eb"; // Blue
    return "#d97706"; // Amber
  };

  const getVerificationBadge = (status?: string) => {
    switch (status) {
      case "VERIFIED_OFFICIAL":
        return { text: "✓ Verified Official Source", bg: "#dcfce7", color: "#15803d" };
      case "OFFICIAL_NEEDS_REVIEW":
        return { text: "Official Portal (Review)", bg: "#fef3c7", color: "#b45309" };
      case "SECONDARY_NEEDS_VERIFICATION":
        return { text: "Secondary Source", bg: "#f3e8ff", color: "#6b21a8" };
      default:
        return { text: "Official Portal", bg: "#e0f2fe", color: "#0369a1" };
    }
  };

  const verif = getVerificationBadge(scheme.verification_status);

  return (
    <div style={{
      border: "1px solid #e2e8f0",
      borderRadius: "12px",
      padding: "1.75rem",
      background: "#ffffff",
      boxShadow: "0 4px 12px -2px rgba(0, 0, 0, 0.05)",
      marginBottom: "1.5rem"
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
            <h3 style={{ margin: 0, color: "#1e293b", fontSize: "1.25rem" }}>{scheme.title}</h3>
            <span style={{
              background: verif.bg,
              color: verif.color,
              padding: "0.15rem 0.5rem",
              borderRadius: "12px",
              fontSize: "0.75rem",
              fontWeight: 600
            }}>
              {verif.text}
            </span>
          </div>
          <span style={{ fontSize: "0.85rem", color: "#64748b", fontWeight: "500" }}>
            {scheme.ministry_or_org} {scheme.scheme_code && `• Code: ${scheme.scheme_code}`}
          </span>
        </div>
        <div style={{ textAlign: "right" }}>
          <span style={{
            background: getStatusColor(eligibility_status),
            color: "#ffffff",
            padding: "0.35rem 0.9rem",
            borderRadius: "20px",
            fontSize: "0.85rem",
            fontWeight: "bold",
            display: "inline-block"
          }}>
            {eligibility_status} ({match_score}%)
          </span>
        </div>
      </div>

      <p style={{ color: "#334155", fontSize: "0.95rem", lineHeight: "1.5", margin: "1rem 0" }}>
        {scheme.description}
      </p>

      {/* AI Explanation Callout */}
      <div style={{
        background: "#eff6ff",
        borderLeft: "4px solid #3b82f6",
        padding: "0.75rem 1rem",
        borderRadius: "6px",
        marginBottom: "1rem",
        fontSize: "0.9rem",
        color: "#1e40af"
      }}>
        <strong>🤖 AI Recommendation & Match Justification:</strong> {ai_reasoning}
      </div>

      {/* Score Breakdown Pills */}
      {score_breakdown && (
        <div style={{
          display: "flex",
          gap: "0.75rem",
          flexWrap: "wrap",
          padding: "0.6rem 0.8rem",
          background: "#f8fafc",
          borderRadius: "8px",
          marginBottom: "1rem",
          fontSize: "0.8rem",
          color: "#475569"
        }}>
          <span><strong>Demographic:</strong> +{score_breakdown.demographic_score}</span>
          <span>•</span>
          <span><strong>Category/Affirmative:</strong> +{score_breakdown.category_score}</span>
          <span>•</span>
          <span><strong>Business Sector:</strong> +{score_breakdown.business_score}</span>
          {matching_factors && matching_factors.length > 0 && (
            <div style={{ width: "100%", marginTop: "0.25rem", color: "#166534" }}>
              ✓ Verified factors: {matching_factors.join("; ")}
            </div>
          )}
        </div>
      )}

      {/* Warnings / Missing requirements */}
      {missing_requirements && missing_requirements.length > 0 && (
        <div style={{
          background: "#fffbeb",
          border: "1px solid #fef3c7",
          padding: "0.6rem 0.8rem",
          borderRadius: "6px",
          marginBottom: "1rem",
          fontSize: "0.85rem",
          color: "#92400e"
        }}>
          ⚠️ <strong>Eligibility Requirements to note:</strong> {missing_requirements.join("; ")}
        </div>
      )}

      {/* Benefits */}
      <div style={{ marginBottom: "1rem" }}>
        <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9rem", color: "#475569" }}>Key Benefits & Subsidies:</h4>
        <ul style={{ margin: 0, paddingLeft: "1.25rem", color: "#0f172a", fontSize: "0.9rem" }}>
          {key_benefits.map((benefit, i) => (
            <li key={i} style={{ marginBottom: "0.25rem" }}>{benefit}</li>
          ))}
        </ul>
      </div>

      {/* Required Documents */}
      <div style={{ marginBottom: "1.25rem" }}>
        <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9rem", color: "#475569" }}>Required Documents Checklist:</h4>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          {required_documents.map((doc, i) => (
            <span key={i} style={{
              background: "#f1f5f9",
              color: "#334155",
              padding: "0.25rem 0.6rem",
              borderRadius: "4px",
              fontSize: "0.8rem",
              border: "1px solid #cbd5e1"
            }}>
              📄 {doc}
            </span>
          ))}
        </div>
      </div>

      {/* Action links */}
      <div style={{ display: "flex", gap: "1rem", alignItems: "center", flexWrap: "wrap" }}>
        {scheme.application_url && (
          <a
            href={scheme.application_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "inline-block",
              background: "#1e3a8a",
              color: "#ffffff",
              padding: "0.55rem 1.1rem",
              borderRadius: "6px",
              textDecoration: "none",
              fontSize: "0.9rem",
              fontWeight: "600"
            }}
          >
            Apply on Official Portal ↗
          </a>
        )}
        {scheme.source_url && scheme.source_url !== scheme.application_url && (
          <a
            href={scheme.source_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: "0.85rem",
              color: "#2563eb",
              textDecoration: "underline"
            }}
          >
            View Official Source Guidelines ↗
          </a>
        )}
      </div>
    </div>
  );
};
