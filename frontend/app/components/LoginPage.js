"use client";

import { useState } from "react";

export default function LoginPage({ onLogin }) {
  const [name, setName] = useState("");
  const [organization, setOrganization] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("Clinician / Neurologist");
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please enter your full name.");
      return;
    }
    if (!organization.trim()) {
      setError("Please enter your institution or organization.");
      return;
    }
    if (!email.trim() || !email.includes("@")) {
      setError("Please provide a valid email address.");
      return;
    }

    const userData = {
      name: name.trim(),
      organization: organization.trim(),
      email: email.trim(),
      role,
      loginTime: new Date().toISOString(),
    };

    if (onLogin) {
      onLogin(userData);
    }
  };

  const handleDemoLogin = () => {
    const demoData = {
      name: "Dr. Joshua King",
      organization: "Federal University of Technology, Owerri (FUTO)",
      email: "joshua.king@futo.edu.ng",
      role: "Lead Clinical Researcher",
      loginTime: new Date().toISOString(),
    };
    if (onLogin) {
      onLogin(demoData);
    }
  };

  return (
    <div className="login-screen">
      {/* Editorial Minimal Header */}
      <header className="login-header">
        <div className="login-header-brand">
          <span className="font-syne font-extrabold text-2xl tracking-tighter text-black">NG</span>
          <span className="h-5 w-px bg-black/25"></span>
          <span className="text-[11px] uppercase tracking-widest text-black/70 font-semibold">
            Clinical Seizure AI • FUTO CS Dept
          </span>
        </div>
        <div className="hidden sm:flex items-center gap-3">
          <span className="status-dot connected"></span>
          <span className="text-xs uppercase tracking-wider text-black/60 font-mono">Engine v1.0.0 Online</span>
        </div>
      </header>

      {/* Hero & Login Section */}
      <main className="login-main">
        <div className="login-container">
          {/* Top Title Section */}
          <div className="login-hero-text">
            <div className="hero-tag-badge">
              <span
                style={{
                  borderLeft: "3px solid #2563eb",
                  borderRight: "3px solid #2563eb",
                  padding: "4px 12px",
                  fontWeight: 700,
                  fontSize: "10px",
                  textTransform: "uppercase",
                  letterSpacing: "0.15em",
                  color: "#2563eb",
                  background: "rgba(37, 99, 235, 0.08)",
                }}
              >
                PRACTITIONER PORTAL
              </span>
            </div>
            <h1 className="font-syne text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 leading-tight mt-4 mb-2">
              NeuroGuard <span style={{ textDecoration: "underline", textDecorationColor: "#2563eb", textDecorationThickness: "3px" }}>AI</span>
            </h1>
            <p className="text-sm sm:text-base text-slate-600 max-w-lg font-medium leading-relaxed">
              Clinical-grade 18-channel EEG seizure prediction &amp; automated pre-ictal surveillance.
            </p>
          </div>

          {/* Login Card */}
          <div className="login-card">
            <div className="login-card-header">
              <h2 className="font-syne text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
                <span>Practitioner Access</span>
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Enter your practitioner details to access live EEG streaming &amp; pre-trained dataset analysis.
              </p>
            </div>

            {error && (
              <div className="login-error-badge">
                <span>⚠️ {error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="login-form">
              <div className="form-group">
                <label className="form-label" htmlFor="user-name">
                  Full Name / Title
                </label>
                <input
                  id="user-name"
                  type="text"
                  className="editorial-input"
                  placeholder="e.g. Dr. Ada Lovelace"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    setError("");
                  }}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="user-org">
                  Institution / Organization
                </label>
                <input
                  id="user-org"
                  type="text"
                  className="editorial-input"
                  placeholder="e.g. FUTO / Teaching Hospital"
                  value={organization}
                  onChange={(e) => {
                    setOrganization(e.target.value);
                    setError("");
                  }}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="user-email">
                  Official Email Address
                </label>
                <input
                  id="user-email"
                  type="email"
                  className="editorial-input"
                  placeholder="e.g. clinician@hospital.edu"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setError("");
                  }}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="user-role">
                  Clinical Role
                </label>
                <select
                  id="user-role"
                  className="editorial-input"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                >
                  <option value="Clinician / Neurologist">Clinician / Neurologist</option>
                  <option value="Lead Clinical Researcher">Lead Clinical Researcher</option>
                  <option value="Biomedical Engineer">Biomedical Engineer</option>
                  <option value="Student Investigator">Student Investigator</option>
                </select>
              </div>

              <div className="login-actions">
                <button type="submit" className="editorial-btn-primary">
                  <span>Enter Clinical Workspace</span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="w-4 h-4">
                    <line x1="7" y1="17" x2="17" y2="7"></line>
                    <polyline points="7 7 17 7 17 17"></polyline>
                  </svg>
                </button>

                <button
                  type="button"
                  onClick={handleDemoLogin}
                  className="editorial-btn-secondary"
                  title="Quick 1-click test credentials"
                >
                  ⚡ Fast Demo Access
                </button>
              </div>
            </form>
          </div>

          {/* Feature Highlights Grid */}
          <div className="login-features-grid">
            <div className="feature-item">
              <span className="feature-num">01</span>
              <div className="feature-title">Dual-Stream Neural Network</div>
              <p className="feature-desc">
                Spatial 1D-CNN filters cross-channel interactions while temporal LSTM tracks frequency dynamics.
              </p>
            </div>
            <div className="feature-item">
              <span className="feature-num">02</span>
              <div className="feature-title">CHB-MIT Dataset Harmonization</div>
              <p className="feature-desc">
                Standardized 18-channel 10-20 montage with 5-level Daubechies-4 discrete wavelet decomposition.
              </p>
            </div>
            <div className="feature-item">
              <span className="feature-num">03</span>
              <div className="feature-title">Real-Time Dataset Upload</div>
              <p className="feature-desc">
                Upload real European Data Format (.EDF), CSV, or JSON recordings for instant inference and streaming.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Editorial Footer */}
      <footer className="login-footer">
        <div>© 2026 NeuroGuard • Department of Computer Science, FUTO</div>
        <div className="flex gap-4">
          <span className="font-mono text-xs text-black/50">CHB-MIT 256Hz Spec</span>
          <span>•</span>
          <span className="font-mono text-xs text-black/50">Pre-Ictal Detection Window: 30m</span>
        </div>
      </footer>
    </div>
  );
}
