"use client";

import { useEffect, useState } from "react";

interface HealthStatus {
  status: string;
  service: string;
  version: string;
  profile: string;
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/health")
      .then((r) => r.json())
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <main style={styles.main}>
      {/* Background gradient overlay */}
      <div style={styles.bgGradient} />

      <div style={styles.container}>
        {/* Logo */}
        <div style={styles.logoContainer}>
          <div style={styles.logoIcon}>
            <svg
              width="48"
              height="48"
              viewBox="0 0 48 48"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle cx="24" cy="24" r="20" stroke="#3b82f6" strokeWidth="2" opacity="0.3" />
              <circle cx="24" cy="24" r="14" stroke="#06b6d4" strokeWidth="2" opacity="0.5" />
              <circle cx="24" cy="24" r="8" stroke="#3b82f6" strokeWidth="2" />
              <circle cx="24" cy="24" r="3" fill="#22c55e" />
              {/* Scan lines */}
              <line x1="24" y1="4" x2="24" y2="12" stroke="#3b82f6" strokeWidth="1.5" opacity="0.4" />
              <line x1="24" y1="36" x2="24" y2="44" stroke="#3b82f6" strokeWidth="1.5" opacity="0.4" />
              <line x1="4" y1="24" x2="12" y2="24" stroke="#3b82f6" strokeWidth="1.5" opacity="0.4" />
              <line x1="36" y1="24" x2="44" y2="24" stroke="#3b82f6" strokeWidth="1.5" opacity="0.4" />
            </svg>
          </div>
          <h1 style={styles.title}>
            Net<span style={styles.titleAccent}>Watch</span>{" "}
            <span style={styles.titleAi}>AI</span>
          </h1>
        </div>

        <p style={styles.subtitle}>
          Self-hosted network security platform
        </p>

        {/* Status Card */}
        <div style={styles.card}>
          <div style={styles.statusRow}>
            <div
              style={{
                ...styles.statusDot,
                background: health?.status === "healthy" ? "#22c55e" : loading ? "#eab308" : "#ef4444",
                boxShadow: health?.status === "healthy"
                  ? "0 0 8px rgba(34, 197, 94, 0.5)"
                  : loading
                  ? "0 0 8px rgba(234, 179, 8, 0.5)"
                  : "0 0 8px rgba(239, 68, 68, 0.5)",
              }}
            />
            <span style={styles.statusText}>
              {loading ? "Connecting..." : health ? "All Systems Operational" : "Backend Offline"}
            </span>
          </div>

          {health && (
            <div style={styles.infoGrid}>
              <InfoItem label="Service" value={health.service} />
              <InfoItem label="Version" value={health.version} />
              <InfoItem label="Profile" value={health.profile} />
              <InfoItem label="Status" value={health.status} accent />
            </div>
          )}
        </div>

        {/* Quick Links */}
        <div style={styles.linksRow}>
          <a href="/docs" style={styles.link}>
            <span style={styles.linkIcon}>📖</span> API Docs
          </a>
          <a href="http://localhost:8000/docs" style={styles.link} target="_blank" rel="noopener">
            <span style={styles.linkIcon}>⚡</span> Swagger UI
          </a>
        </div>

        {/* Phase indicator */}
        <p style={styles.phaseText}>
          Phase 1 — Infrastructure Ready · Dashboard coming in Phase 9
        </p>
      </div>
    </main>
  );
}

function InfoItem({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div style={styles.infoItem}>
      <span style={styles.infoLabel}>{label}</span>
      <span
        style={{
          ...styles.infoValue,
          color: accent ? "#22c55e" : "#f1f5f9",
        }}
      >
        {value}
      </span>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  main: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
    overflow: "hidden",
  },
  bgGradient: {
    position: "absolute",
    inset: 0,
    background:
      "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(59, 130, 246, 0.08) 0%, transparent 60%), " +
      "radial-gradient(ellipse 60% 40% at 80% 100%, rgba(6, 182, 212, 0.06) 0%, transparent 50%)",
    pointerEvents: "none",
  },
  container: {
    textAlign: "center" as const,
    maxWidth: 480,
    padding: "2rem",
    animation: "fadeIn 0.6s ease-out",
  },
  logoContainer: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "1rem",
    marginBottom: "0.75rem",
  },
  logoIcon: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontSize: "2.5rem",
    fontWeight: 700,
    letterSpacing: "-0.02em",
    color: "#f1f5f9",
  },
  titleAccent: {
    color: "#3b82f6",
  },
  titleAi: {
    fontSize: "1.25rem",
    fontWeight: 500,
    color: "#06b6d4",
    verticalAlign: "super",
  },
  subtitle: {
    fontSize: "1.05rem",
    color: "#94a3b8",
    marginBottom: "2rem",
  },
  card: {
    background: "rgba(26, 31, 53, 0.7)",
    backdropFilter: "blur(12px)",
    border: "1px solid #1e293b",
    borderRadius: "16px",
    padding: "1.5rem",
    marginBottom: "1.5rem",
    boxShadow: "0 4px 24px rgba(0, 0, 0, 0.3)",
  },
  statusRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "0.625rem",
    marginBottom: "1.25rem",
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
  },
  statusText: {
    fontSize: "0.95rem",
    fontWeight: 500,
    color: "#f1f5f9",
  },
  infoGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "0.75rem",
  },
  infoItem: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "0.25rem",
  },
  infoLabel: {
    fontSize: "0.7rem",
    fontWeight: 500,
    color: "#64748b",
    textTransform: "uppercase" as const,
    letterSpacing: "0.08em",
  },
  infoValue: {
    fontSize: "0.9rem",
    fontWeight: 500,
    fontFamily: '"JetBrains Mono", monospace',
  },
  linksRow: {
    display: "flex",
    gap: "1rem",
    justifyContent: "center",
    marginBottom: "2rem",
  },
  link: {
    display: "flex",
    alignItems: "center",
    gap: "0.375rem",
    padding: "0.5rem 1rem",
    borderRadius: "10px",
    border: "1px solid #1e293b",
    color: "#94a3b8",
    fontSize: "0.85rem",
    textDecoration: "none",
    transition: "all 0.2s ease",
  },
  linkIcon: {
    fontSize: "0.9rem",
  },
  phaseText: {
    fontSize: "0.75rem",
    color: "#475569",
    fontStyle: "italic",
  },
};
