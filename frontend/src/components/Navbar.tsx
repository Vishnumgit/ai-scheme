import React from "react";
import Link from "next/link";

export const Navbar = () => {
  return (
    <header style={{
      background: "#1e3a8a",
      color: "#ffffff",
      padding: "1rem 2rem",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
      flexWrap: "wrap",
      gap: "1rem"
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <Link href="/" style={{ color: "#ffffff", textDecoration: "none", fontSize: "1.4rem", fontWeight: "bold" }}>
          🇮🇳 SchemeMatch AI
        </Link>
        <span style={{ fontSize: "0.8rem", background: "rgba(255,255,255,0.15)", padding: "0.2rem 0.6rem", borderRadius: "12px" }}>
          Verified Knowledge Base
        </span>
      </div>
      <nav style={{ display: "flex", alignItems: "center", gap: "1.5rem", fontSize: "0.9rem" }}>
        <Link href="/" style={{ color: "#e2e8f0", textDecoration: "none", fontWeight: 500 }}>
          Schemes & Matching
        </Link>
        <Link href="/admin" style={{ color: "#93c5fd", textDecoration: "none", fontWeight: 600 }}>
          ⚙️ Ingestion & Admin
        </Link>
      </nav>
    </header>
  );
};
