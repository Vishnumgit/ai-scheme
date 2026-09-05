import React from "react";
import { Language } from "../lib/i18n";

type NavbarProps = {
  language: Language;
  onLanguageChange: (language: Language) => void;
  languageLabel: string;
  tagline: string;
};

export const Navbar = ({ language, onLanguageChange, languageLabel, tagline }: NavbarProps) => {
  return (
    <header style={{
      background: "#1e3a8a",
      color: "#ffffff",
      padding: "1rem 2rem",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <span style={{ fontSize: "1.5rem", fontWeight: "bold" }}>🇮🇳 SchemeMatch AI</span>
      </div>
      <nav style={{ display: "flex", alignItems: "center", gap: "1rem", fontSize: "0.9rem", color: "#e2e8f0" }}>
        <span>{tagline}</span>
        <label style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
          <span>{languageLabel}</span>
          <select
            aria-label={languageLabel}
            value={language}
            onChange={(event) => onLanguageChange(event.target.value as Language)}
            style={{ padding: "0.35rem", borderRadius: "5px", border: "1px solid #bfdbfe", color: "#1e293b" }}
          >
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="te">తెలుగు</option>
          </select>
        </label>
      </nav>
    </header>
  );
};
