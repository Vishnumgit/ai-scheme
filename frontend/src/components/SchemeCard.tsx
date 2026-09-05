import React from "react";
import { SchemeMatchResult } from "../lib/api";
import { translations, Language } from "../lib/i18n";

export const SchemeCard: React.FC<{ match: SchemeMatchResult; language: Language }> = ({ match, language }) => {
  const { scheme, match_score, eligibility_status, ai_reasoning, key_benefits, required_documents } = match;
  const t = translations[language];

  const getStatusColor = (status: string) => {
    if (status === "Highly Eligible") return "#16a34a"; // Green
    if (status === "Eligible") return "#2563eb"; // Blue
    return "#d97706"; // Amber
  };

  return (
    <div style={{
      border: "1px solid #e2e8f0",
      borderRadius: "10px",
      padding: "1.5rem",
      background: "#ffffff",
      boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05)",
      marginBottom: "1.5rem"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem" }}>
        <div>
          <h3 style={{ margin: "0 0 0.25rem 0", color: "#1e293b" }}>{scheme.title}</h3>
          <span style={{ fontSize: "0.85rem", color: "#64748b", fontWeight: "500" }}>{scheme.ministry_or_org}</span>
        </div>
        <div style={{ textAlign: "right" }}>
          <span style={{
            background: getStatusColor(eligibility_status),
            color: "#ffffff",
            padding: "0.3rem 0.8rem",
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

      {/* AI Reasoning Callout */}
      <div style={{
        background: "#eff6ff",
        borderLeft: "4px solid #3b82f6",
        padding: "0.75rem 1rem",
        borderRadius: "4px",
        marginBottom: "1rem",
        fontSize: "0.9rem",
        color: "#1e40af"
      }}>
        <strong>{t.aiReason}</strong> {ai_reasoning}
      </div>

      {/* Benefits */}
      <div style={{ marginBottom: "1rem" }}>
        <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9rem", color: "#475569" }}>{t.keyBenefits}</h4>
        <ul style={{ margin: 0, paddingLeft: "1.25rem", color: "#0f172a", fontSize: "0.9rem" }}>
          {key_benefits.map((benefit, i) => (
            <li key={i} style={{ marginBottom: "0.25rem" }}>{benefit}</li>
          ))}
        </ul>
      </div>

      {/* Documents */}
      <div style={{ marginBottom: "1rem" }}>
        <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9rem", color: "#475569" }}>{t.requiredDocuments}</h4>
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

      {/* Link */}
      {scheme.application_url && (
        <a
          href={scheme.application_url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: "inline-block",
            marginTop: "0.5rem",
            background: "#1e3a8a",
            color: "#ffffff",
            padding: "0.5rem 1rem",
            borderRadius: "6px",
            textDecoration: "none",
            fontSize: "0.9rem",
            fontWeight: "500"
          }}
        >
          {t.applyPortal}
        </a>
      )}
    </div>
  );
};
