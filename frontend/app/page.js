"use client";

import { useState, useEffect, useCallback } from "react";
import StatusBar from "./components/StatusBar";
import RiskGauge from "./components/RiskGauge";
import AlertBadge from "./components/AlertBadge";
import EEGChart from "./components/EEGChart";
import PredictionHistory from "./components/PredictionHistory";
import SimulationControls from "./components/SimulationControls";
import DatasetUploader from "./components/DatasetUploader";
import StatsPanel from "./components/StatsPanel";
import PredictionLog from "./components/PredictionLog";
import LoginPage from "./components/LoginPage";
import { predictWindow } from "../lib/api";
import { generateMockEEG, generateMockBatch } from "../lib/mockEEG";

export default function Dashboard() {
  // ── Authentication State ─────────────────────────────────────────────────
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);

  // ── Dashboard State ──────────────────────────────────────────────────────
  const [predictions, setPredictions] = useState([]);
  const [latestResult, setLatestResult] = useState(null);
  const [currentEEG, setCurrentEEG] = useState(null);
  const [loading, setLoading] = useState(false);
  const [patientId, setPatientId] = useState("CHB01");
  const [error, setError] = useState(null);
  const [inputTab, setInputTab] = useState("dataset"); // "dataset" | "simulation"

  useEffect(() => {
    try {
      const savedUser = localStorage.getItem("neuroguard_user");
      if (savedUser) {
        setUser(JSON.parse(savedUser));
      }
    } catch {
      // ignore
    } finally {
      setAuthChecked(true);
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    try {
      localStorage.setItem("neuroguard_user", JSON.stringify(userData));
    } catch {
      // ignore
    }
  };

  const handleLogout = () => {
    setUser(null);
    try {
      localStorage.removeItem("neuroguard_user");
    } catch {
      // ignore
    }
  };

  // ── Handlers ─────────────────────────────────────────────────────────────
  const handleGenerateSingle = useCallback(async (mode) => {
    setLoading(true);
    setError(null);
    try {
      const eeg = generateMockEEG(mode);
      setCurrentEEG(eeg);

      const result = await predictWindow(eeg, patientId);
      setLatestResult(result);
      setPredictions((prev) => [...prev, result]);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  const handleSimulateSession = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const windows = generateMockBatch(10);
      setCurrentEEG(windows[windows.length - 1]);

      for (const win of windows) {
        const result = await predictWindow(win, patientId);
        setPredictions((prev) => [...prev, result]);
        setLatestResult(result);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  const handleDatasetEvaluated = useCallback((result) => {
    if (result.predictions && result.predictions.length > 0) {
      const lastPred = result.predictions[result.predictions.length - 1];
      setLatestResult(lastPred);
      setPredictions((prev) => [...prev, ...result.predictions]);
    }
    if (result.sample_waveform) {
      setCurrentEEG(result.sample_waveform);
    }
  }, []);

  const handleStreamWindow = useCallback((windowPred, index, waveform) => {
    setLatestResult(windowPred);
    setPredictions((prev) => [...prev, windowPred]);
    if (waveform) {
      setCurrentEEG(waveform);
    }
  }, []);

  // ── Derived values ───────────────────────────────────────────────────────
  const probability = latestResult?.probability ?? 0;
  const alertLevel = latestResult?.alert_level ?? "LOW";
  const prediction = latestResult?.prediction ?? "—";
  const confidence = latestResult?.confidence ?? "—";

  // Prevent flash before checking localStorage
  if (!authChecked) {
    return (
      <div style={{ minHeight: "100vh", background: "#0a0e1a", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span className="spinner" style={{ width: "32px", height: "32px" }}></span>
      </div>
    );
  }

  // If not logged in, render the editorial login page
  if (!user) {
    return <LoginPage onLogin={handleLogin} />;
  }

  // Clinician initials
  const initials = user.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-primary)" }}>
      {/* ── Redesigned Editorial Navigation Bar ────────────────────────────── */}
      <header className="editorial-dashboard-header">
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <a href="#" style={{ display: "flex", alignItems: "center", gap: "10px", textDecoration: "none" }}>
            <span className="font-syne font-extrabold text-2xl tracking-tighter" style={{ color: "#0f172a" }}>
              NG
            </span>
            <span style={{ width: "1px", height: "20px", background: "#cbd5e1" }}></span>
            <span style={{ fontSize: "0.72rem", letterSpacing: "0.18em", textTransform: "uppercase", color: "#64748b", fontWeight: 700 }}>
              Clinical AI • FUTO
            </span>
          </a>
        </div>

        {/* Desktop Nav Links */}
        <nav className="nav-links-row hidden md:flex">
          <a href="#monitor" className="nav-link-item">Monitor</a>
          <a href="#dataset-input" className="nav-link-item">Dataset Input</a>
          <a href="#history" className="nav-link-item">Analytics</a>
          <a href="#logs" className="nav-link-item">Event Log</a>
        </nav>

        {/* Right: Clinician Credentials Pill & Logout */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div className="clinician-badge-pill">
            <div className="clinician-avatar">{initials}</div>
            <div style={{ lineHeight: 1.2 }}>
              <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#0f172a" }}>{user.name}</div>
              <div style={{ fontSize: "0.68rem", color: "#64748b" }}>{user.organization}</div>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="editorial-btn-secondary"
            style={{
              padding: "6px 14px",
              fontSize: "0.7rem",
              color: "#0f172a",
              borderColor: "#cbd5e1",
              background: "#ffffff",
            }}
            title="Switch User or Logout"
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* ── Main Dashboard Workspace ─────────────────────────────────────── */}
      <main className="dashboard" style={{ marginTop: "24px" }}>
        {/* Status Bar */}
        <StatusBar />

        {/* Error banner */}
        {error && (
          <div
            className="card fade-in"
            style={{
              background: "rgba(239, 68, 68, 0.1)",
              borderColor: "rgba(239, 68, 68, 0.3)",
              padding: "12px 20px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <span style={{ color: "var(--accent-red)", fontSize: "0.85rem" }}>
              ⚠️ {error}
            </span>
            <button
              className="btn btn-outline btn-sm"
              onClick={() => setError(null)}
              style={{ borderColor: "rgba(239, 68, 68, 0.3)", color: "var(--accent-red)" }}
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Input Mode Selector Tabs */}
        <div id="dataset-input" className="input-tab-bar slide-up" style={{ animationDelay: "0.15s" }}>
          <button
            className={`input-tab-btn ${inputTab === "dataset" ? "active" : ""}`}
            onClick={() => setInputTab("dataset")}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: "16px", height: "16px" }}>
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" strokeLinecap="round" strokeLinejoin="round" />
              <polyline points="17 8 12 3 7 8" strokeLinecap="round" strokeLinejoin="round" />
              <line x1="12" y1="3" x2="12" y2="15" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Dataset &amp; File Input (EDF / CSV / JSON)
          </button>
          <button
            className={`input-tab-btn ${inputTab === "simulation" ? "active" : ""}`}
            onClick={() => setInputTab("simulation")}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: "16px", height: "16px" }}>
              <path d="M12 20V10M18 20V4M6 20v-4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Synthetic Signal Simulator
          </button>
        </div>

        {/* Input Panels */}
        {inputTab === "dataset" ? (
          <DatasetUploader
            patientId={patientId}
            onPatientIdChange={setPatientId}
            onDatasetEvaluated={handleDatasetEvaluated}
            onStreamWindow={handleStreamWindow}
            loading={loading}
            setLoading={setLoading}
            setError={setError}
          />
        ) : (
          <SimulationControls
            onGenerateSingle={handleGenerateSingle}
            onSimulateSession={handleSimulateSession}
            loading={loading}
            patientId={patientId}
            onPatientIdChange={setPatientId}
          />
        )}

        {/* Main Grid: EEG + Gauge */}
        <div id="monitor" className="dashboard-grid-top">
          {/* EEG Waveform */}
          <div className="card slide-up" style={{ animationDelay: "0.3s" }}>
            <div className="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              EEG Signal Visualisation
              {currentEEG && (
                <span
                  style={{
                    marginLeft: "auto",
                    fontSize: "0.68rem",
                    color: "var(--text-muted)",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  {currentEEG.length}ch × {currentEEG[0]?.length || 0} samples
                </span>
              )}
            </div>
            <EEGChart eegData={currentEEG} />
          </div>

          {/* Risk Gauge + Latest Result */}
          <div className="card slide-up" style={{ animationDelay: "0.4s" }}>
            <div className="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              Current Risk Level
            </div>
            <RiskGauge probability={probability} />
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "12px",
                marginTop: "8px",
              }}
            >
              <AlertBadge level={alertLevel} />
              <div style={{ display: "flex", gap: "24px", fontSize: "0.8rem" }}>
                <div style={{ textAlign: "center" }}>
                  <div className="text-muted" style={{ fontSize: "0.68rem", marginBottom: "2px" }}>
                    PREDICTION
                  </div>
                  <div style={{ fontWeight: 600 }}>{prediction}</div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div className="text-muted" style={{ fontSize: "0.68rem", marginBottom: "2px" }}>
                    CONFIDENCE
                  </div>
                  <div style={{ fontWeight: 600 }}>{confidence}</div>
                </div>
                {latestResult?.processing_ms && (
                  <div style={{ textAlign: "center" }}>
                    <div className="text-muted" style={{ fontSize: "0.68rem", marginBottom: "2px" }}>
                      LATENCY
                    </div>
                    <div className="text-mono" style={{ fontWeight: 600 }}>
                      {latestResult.processing_ms.toFixed(0)}ms
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Middle Grid: History + Stats */}
        <div id="history" className="dashboard-grid-main">
          <div className="card slide-up" style={{ animationDelay: "0.5s" }}>
            <div className="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 3v18h18" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M7 16l4-6 4 2 5-8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              Prediction History
              {predictions.length > 0 && (
                <span
                  style={{
                    marginLeft: "auto",
                    fontSize: "0.68rem",
                    color: "var(--text-muted)",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  {predictions.length} predictions
                </span>
              )}
            </div>
            <PredictionHistory predictions={predictions} />
          </div>

          <div className="card slide-up" style={{ animationDelay: "0.6s" }}>
            <div className="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M16 8v8M12 11v5M8 14v2M4 2v20h20" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              Session Statistics
            </div>
            <StatsPanel predictions={predictions} />
          </div>
        </div>

        {/* Bottom: Prediction Log */}
        <div id="logs" className="card slide-up" style={{ animationDelay: "0.7s" }}>
          <div className="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Prediction Event Log
          </div>
          <PredictionLog predictions={predictions} />
        </div>
      </main>

      {/* ── Editorial Footer ──────────────────────────────────────────────── */}
      <footer
        style={{
          borderTop: "1px solid #cbd5e1",
          background: "#e2e8f0",
          padding: "32px 24px",
          marginTop: "48px",
          fontSize: "0.8rem",
          color: "#64748b",
        }}
      >
        <div
          style={{
            maxWidth: "1280px",
            margin: "0 auto",
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "16px",
          }}
        >
          <div>
            <div className="font-syne font-bold text-slate-900 text-sm" style={{ letterSpacing: "0.05em", color: "#0f172a" }}>
              NeuroGuard • Clinical Seizure Prediction Engine
            </div>
            <div style={{ fontSize: "0.75rem", marginTop: "4px", color: "#64748b" }}>
              Department of Computer Science • Federal University of Technology, Owerri (FUTO)
            </div>
          </div>
          <div style={{ display: "flex", gap: "16px", alignItems: "center", color: "#64748b" }}>
            <span className="font-mono text-xs">CHB-MIT PhysioNet</span>
            <span>•</span>
            <span className="font-mono text-xs">Dual-Stream CNN-LSTM</span>
            <span>•</span>
            <span className="font-mono text-xs">FastAPI + Next.js</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
